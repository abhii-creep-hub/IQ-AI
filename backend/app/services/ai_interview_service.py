from datetime import datetime, timezone
from statistics import mean
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.ai.service import ai_service
from app.models.ai_interview import AIInterviewQuestion, AIInterviewSession
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.skill import CandidateSkill
from app.models.user import User
from app.schemas.ai_interview import (
    AIAnswerEvaluation, GeneratedInterviewQuestions, InterviewAssistantType,
)
from app.core.config import settings
from app.services.interview_service import candidate_access_clause


class AIProviderError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


async def _call_ai(call):
    try:
        return await call
    except ValueError as error:
        message = str(error).lower()
        if "quota" in message or "rate limit" in message:
            raise AIProviderError(429, "The AI provider quota is unavailable right now. Try again later.") from None
        if "api key" in message or "gemini_api_key" in message:
            raise AIProviderError(503, "AI interview features are unavailable. Check the configured AI provider key.") from None
        raise AIProviderError(502, "The AI provider returned an invalid response. Please retry.") from None
    except TimeoutError:
        raise AIProviderError(504, "The AI request timed out. Please retry.") from None
    except RuntimeError as error:
        message = str(error).lower()
        if "gemini_api_key" in message or "api key" in message:
            raise AIProviderError(503, "AI interview features are unavailable. Check the configured AI provider key.") from None
        raise AIProviderError(502, "The AI provider could not process this request. Please retry.") from None
    except Exception:
        raise AIProviderError(502, "The AI provider could not process this request. Please retry.") from None


def build_final_report(session: AIInterviewSession) -> dict:
    questions = list(session.questions or [])
    evaluated = [q for q in questions if q.status == "answered" and q.evaluation and q.score is not None]
    answered_count = sum(1 for q in questions if q.answer and q.status in ("answered", "unevaluable"))
    skipped_count = sum(1 for q in questions if q.status == "skipped")
    unevaluable = [q for q in questions if q.status == "unevaluable"]
    score = round(mean(q.score for q in evaluated), 1) if evaluated else None

    category_map = {}
    for question in evaluated:
        category_map.setdefault(question.category, []).append(question.score)
    category_scores = {
        category: {"score": round(mean(scores), 1), "evaluated_questions": len(scores)}
        for category, scores in sorted(category_map.items())
    }

    def distinct_items(field):
        values = []
        seen = set()
        for question in evaluated:
            for value in (question.evaluation or {}).get(field, []) or []:
                normalized = str(value).strip()
                if normalized and normalized.casefold() not in seen:
                    seen.add(normalized.casefold())
                    values.append(normalized)
        return values

    strengths = distinct_items("strengths")
    gaps = distinct_items("missing_concepts")
    competencies = [q.competency for q in evaluated if q.score >= 70]
    verification = [
        {"question": q.question, "reason": (q.evaluation or {}).get("uncertainty_reason") or "Insufficient answer evidence"}
        for q in unevaluable
    ]
    follow_ups = [
        value for q in questions
        if (value := ((q.evaluation or {}).get("suggested_follow_up") or q.follow_up_question))
    ]
    coverage = round(len(evaluated) / len(questions) * 100, 1) if questions else 0.0

    if len(evaluated) < max(1, len(questions) // 2):
        recommendation = "insufficient_evidence"
        next_steps = ["Complete more questions or use a follow-up assessment before making a decision."]
    elif score is not None and score >= 80:
        recommendation = "strong_evidence"
        next_steps = ["Review the evidence and confirm key competencies with references or a work sample."]
    elif score is not None and score >= 60:
        recommendation = "potential_fit"
        next_steps = ["Probe the listed knowledge gaps in a follow-up interview."]
    else:
        recommendation = "skill_gaps"
        next_steps = ["Review the specific evidence and consider a targeted practical assessment."]

    return {
        "interview_date": (session.completed_at or datetime.now(timezone.utc)).isoformat(),
        "status": "completed",
        "mode": session.mode or "written",
        "interview_type": session.interview_type,
        "difficulty": session.difficulty,
        "total_questions": len(questions),
        "answered_questions": answered_count,
        "skipped_questions": skipped_count,
        "unevaluable_questions": len(unevaluable),
        "evaluated_questions": len(evaluated),
        "evaluation_coverage_percent": coverage,
        "overall_score": score,
        "scoring_method": "Unweighted arithmetic mean of reliable 0–100 question scores; skipped and unevaluable answers are excluded.",
        "category_performance": category_scores,
        "question_results": [
            {
                "order_index": q.order_index, "question": q.question, "category": q.category,
                "competency": q.competency, "status": q.status, "score": q.score,
                "answer_quality": q.answer_quality, "evaluation": q.evaluation,
            }
            for q in questions
        ],
        "key_strengths": strengths,
        "knowledge_gaps": gaps,
        "competencies_demonstrated": list(dict.fromkeys(competencies)),
        "areas_requiring_verification": verification,
        "recommended_follow_up_questions": list(dict.fromkeys(follow_ups)),
        "recruiter_recommendation": recommendation,
        "recommended_next_steps": next_steps,
        "decision_notice": "AI-assisted evidence summary only. Review answers and supporting evidence; this is not an automatic hiring decision.",
    }


class AIInterviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _candidate_options(self):
        return (
            selectinload(Candidate.resume),
            selectinload(Candidate.skills).selectinload(CandidateSkill.skill),
            selectinload(Candidate.experience),
            selectinload(Candidate.projects),
            selectinload(Candidate.education),
            selectinload(Candidate.ats_result),
        )

    def _session_options(self):
        return (
            selectinload(AIInterviewSession.candidate).options(*self._candidate_options()),
            selectinload(AIInterviewSession.job),
            selectinload(AIInterviewSession.questions),
        )

    async def _candidate(self, user_id: UUID, candidate_id: UUID):
        query = select(Candidate).options(*self._candidate_options(), selectinload(Candidate.job)).where(
            Candidate.id == candidate_id, candidate_access_clause(user_id)
        )
        return await self.db.scalar(query)

    async def _owned_job(self, user_id: UUID, job_id: UUID):
        return await self.db.scalar(select(Job).where(Job.id == job_id, Job.owner_id == user_id))

    async def list_candidates(self, recruiter_id: UUID, *, search=None, skip=0, limit=100):
        query = select(Candidate).options(*self._candidate_options(), selectinload(Candidate.job)).where(
            candidate_access_clause(recruiter_id)
        )
        if search:
            term = f"%{search.strip()}%"
            query = query.where(Candidate.name.ilike(term) | Candidate.email.ilike(term))
        query = query.order_by(Candidate.created_at.desc()).offset(skip).limit(limit)
        return list((await self.db.scalars(query)).all())

    async def list_jobs(self, recruiter_id: UUID, *, skip=0, limit=100):
        query = select(Job).where(Job.owner_id == recruiter_id).order_by(Job.created_at.desc()).offset(skip).limit(limit)
        return list((await self.db.scalars(query)).all())

    async def _get_session(self, recruiter_id: UUID, session_id: UUID):
        query = select(AIInterviewSession).options(*self._session_options()).where(
            AIInterviewSession.id == session_id, AIInterviewSession.recruiter_id == recruiter_id
        )
        return await self.db.scalar(query)

    async def _commit(self):
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    def _candidate_ai_context(self, candidate: Candidate):
        return {
            "skills": [
                {"name": item.skill.name, "proficiency": item.proficiency,
                 "years_experience": item.years_experience}
                for item in (candidate.skills or []) if item.skill
            ],
            "experience_years": candidate.total_experience_years,
            "work_experience": [
                {"title": item.title, "description": (item.description or "")[:1200],
                 "achievements": (item.achievements or [])[:5]}
                for item in (candidate.experience or [])[:8]
            ],
            "projects": [
                {"name": item.name, "description": (item.description or "")[:1200],
                 "technologies": (item.technologies or [])[:12]}
                for item in (candidate.projects or [])[:8]
            ],
        }

    def _job_context(self, job: Job | None):
        if not job:
            return {"title": "General screening", "description": "", "requirements": "",
                    "responsibilities": "", "required_skills": [], "preferred_skills": [],
                    "experience_min": None, "experience_max": None}
        return {
            "title": job.title,
            "description": (job.description or "")[:6000],
            "requirements": (job.requirements or "")[:4000],
            "responsibilities": (job.responsibilities or "")[:4000],
            "required_skills": job.required_skills or [],
            "preferred_skills": job.preferred_skills or [],
            "experience_min": job.experience_min,
            "experience_max": job.experience_max,
        }

    async def create(self, recruiter: User, payload: dict):
        candidate = await self._candidate(recruiter.id, payload["candidate_id"])
        if candidate is None:
            raise LookupError("Candidate not found")
        job_id = payload.get("job_id") or candidate.job_id
        if candidate.job_id and job_id != candidate.job_id:
            raise ValueError("Selected job must match the candidate's associated job")
        job = await self._owned_job(recruiter.id, job_id) if job_id else None
        if job_id and job is None:
            raise LookupError("Job not found")
        session = AIInterviewSession(
            candidate_id=candidate.id, job_id=job_id, recruiter_id=recruiter.id,
            interview_type=payload["interview_type"], difficulty=payload["difficulty"],
            mode=payload.get("mode", "written"),
            question_count=payload["question_count"], duration_minutes=payload.get("duration_minutes"),
            status="draft",
        )
        self.db.add(session)
        await self.db.flush()
        await self._commit()
        return await self._get_session(recruiter.id, session.id)

    async def list(self, recruiter_id: UUID, *, candidate_id=None, job_id=None):
        query = select(AIInterviewSession).options(*self._session_options()).where(
            AIInterviewSession.recruiter_id == recruiter_id
        )
        if candidate_id:
            query = query.where(AIInterviewSession.candidate_id == candidate_id)
        if job_id:
            if await self._owned_job(recruiter_id, job_id) is None:
                raise LookupError("Job not found")
            query = query.where(AIInterviewSession.job_id == job_id)
        return list((await self.db.scalars(query.order_by(AIInterviewSession.created_at.desc()))).all())

    async def get(self, recruiter_id: UUID, session_id: UUID):
        session = await self._get_session(recruiter_id, session_id)
        if session is None:
            raise LookupError("Interview session not found")
        return session

    async def generate_questions(self, recruiter_id: UUID, session_id: UUID):
        session = await self.get(recruiter_id, session_id)
        if session.questions:
            return session
        candidate_context = self._candidate_ai_context(session.candidate)
        job_context = self._job_context(session.job)
        raw = await _call_ai(ai_service.generate_assistant_questions(
            candidate_context, job_context, session.interview_type, session.difficulty,
            session.question_count,
        ))
        try:
            generated = GeneratedInterviewQuestions.model_validate(raw)
        except Exception:
            raise AIProviderError(502, "The AI provider returned questions in an invalid format. Please retry.") from None
        if len(generated.questions) != session.question_count:
            raise AIProviderError(502, "The AI provider returned an unexpected number of questions. Please retry.")
        new_questions = [
            AIInterviewQuestion(
                session_id=session.id, order_index=index, question=item.question,
                category=item.category, difficulty=item.difficulty, competency=item.competency,
                job_relevance=item.job_relevance, expected_concepts=item.expected_concepts,
                evaluation_rubric=item.evaluation_rubric.model_dump(),
                follow_up_question=item.follow_up_question, status="pending",
            )
            for index, item in enumerate(generated.questions, start=1)
        ]
        self.db.add_all(new_questions)
        await self._commit()
        return await self.get(recruiter_id, session_id)

    async def start(self, recruiter_id: UUID, session_id: UUID):
        session = await self.get(recruiter_id, session_id)
        if not session.questions:
            raise ValueError("Generate questions before starting the interview")
        if session.status not in ("draft", "paused"):
            raise ValueError("This interview session cannot be started")
        session.status = "in_progress"
        await self._commit()
        return await self.get(recruiter_id, session_id)

    async def pause(self, recruiter_id: UUID, session_id: UUID):
        session = await self.get(recruiter_id, session_id)
        if session.status != "in_progress":
            raise ValueError("Only an in-progress interview can be paused")
        session.status = "paused"
        await self._commit()
        return await self.get(recruiter_id, session_id)

    async def save_answer(self, recruiter_id: UUID, session_id: UUID, question_id: UUID, *, answer=None, skip=False):
        session = await self.get(recruiter_id, session_id)
        if session.status not in ("in_progress", "paused"):
            raise ValueError("Start or resume the interview before editing answers")
        question = next((item for item in session.questions if item.id == question_id), None)
        if question is None:
            raise LookupError("Question not found")
        if skip:
            question.answer = None
            question.evaluation = None
            question.score = None
            question.answer_quality = None
            question.status = "skipped"
        else:
            answer = (answer or "").strip()
            if not answer:
                raise ValueError("Enter an answer or skip this question")
            if len(answer) > 20000:
                raise ValueError("Answer must be 20,000 characters or fewer")
            if question.answer != answer:
                question.evaluation = None
                question.score = None
                question.answer_quality = None
            question.answer = answer
            question.status = "unevaluable" if (question.evaluation or {}).get("uncertain") else "answered"
        await self._commit()
        return await self.get(recruiter_id, session_id)

    async def transcribe_answer(self, recruiter_id: UUID, session_id: UUID, question_id: UUID,
                                audio_bytes: bytes, mime_type: str):
        session = await self.get(recruiter_id, session_id)
        if session.mode not in ("voice", "live_ai"):
            raise ValueError("Audio transcription is only available for voice interview modes")
        if session.status not in ("in_progress", "paused"):
            raise ValueError("Start or resume the interview before recording an answer")
        if not any(item.id == question_id for item in session.questions):
            raise LookupError("Question not found")
        if not audio_bytes:
            raise ValueError("The audio recording is empty")
        if len(audio_bytes) > settings.AI_AUDIO_MAX_SIZE_MB * 1024 * 1024:
            raise ValueError(f"Audio recording must be {settings.AI_AUDIO_MAX_SIZE_MB} MB or smaller")
        transcript = await _call_ai(ai_service.transcribe_interview_audio(audio_bytes, mime_type))
        return {"transcript": transcript, "audio_saved": False}

    def _question_context(self, question: AIInterviewQuestion):
        return {
            "question": question.question, "category": question.category,
            "difficulty": question.difficulty, "competency": question.competency,
            "job_relevance": question.job_relevance,
            "expected_concepts": question.expected_concepts or [],
            "evaluation_rubric": question.evaluation_rubric or {},
        }

    async def evaluate_answer(self, recruiter_id: UUID, session_id: UUID, question_id: UUID):
        session = await self.get(recruiter_id, session_id)
        if session.status not in ("in_progress", "paused"):
            raise ValueError("Start or resume the interview before evaluating answers")
        question = next((item for item in session.questions if item.id == question_id), None)
        if question is None:
            raise LookupError("Question not found")
        if not question.answer or question.status == "skipped":
            raise ValueError("Save an answer before evaluating it")
        if question.evaluation is not None:
            return session
        raw = await _call_ai(ai_service.evaluate_interview_answer(
            self._question_context(question), question.answer, self._job_context(session.job)
        ))
        try:
            evaluation = AIAnswerEvaluation.model_validate(raw)
        except Exception:
            raise AIProviderError(502, "The AI provider returned an invalid evaluation. Please retry.") from None
        question.evaluation = evaluation.model_dump()
        question.score = evaluation.score
        question.answer_quality = evaluation.answer_quality
        question.status = "unevaluable" if evaluation.uncertain else "answered"
        await self._commit()
        return await self.get(recruiter_id, session_id)

    async def generate_follow_up(self, recruiter_id: UUID, session_id: UUID, question_id: UUID):
        session = await self.get(recruiter_id, session_id)
        question = next((item for item in session.questions if item.id == question_id), None)
        if question is None:
            raise LookupError("Question not found")
        if not question.answer:
            raise ValueError("Save an answer before generating a follow-up")
        evaluation = question.evaluation or {}
        follow_up = evaluation.get("suggested_follow_up") or question.follow_up_question
        if not follow_up:
            raw = await _call_ai(ai_service.generate_interview_follow_up(
                self._question_context(question), question.answer, evaluation,
                self._job_context(session.job),
            ))
            follow_up = raw.get("follow_up_question") if isinstance(raw, dict) else None
            if not isinstance(follow_up, str) or not follow_up.strip() or len(follow_up) > 2000:
                raise ValueError("AI returned an invalid follow-up question")
            question.follow_up_question = follow_up.strip()
            await self._commit()
        return await self.get(recruiter_id, session_id)

    async def append_live_follow_up(self, recruiter_id: UUID, session_id: UUID, question_id: UUID):
        session = await self.get(recruiter_id, session_id)
        if session.mode != "live_ai":
            raise ValueError("Conversational follow-ups are only available in Live AI mode")
        if session.status not in ("in_progress", "paused"):
            raise ValueError("Start or resume the interview before asking follow-ups")
        parent = next((item for item in session.questions if item.id == question_id), None)
        if parent is None:
            raise LookupError("Question not found")
        if not parent.answer or not parent.evaluation:
            raise ValueError("Save and evaluate the confirmed answer before generating a follow-up")
        existing = next((item for item in session.questions if item.parent_question_id == parent.id), None)
        if existing:
            return session
        if len(session.questions) >= session.question_count + 10:
            raise ValueError("This session has reached its limit of 10 additional follow-up questions")

        recent_turns = [
            {"question": item.question, "confirmed_answer": item.answer,
             "evaluation_summary": (item.evaluation or {}).get("explanation")}
            for item in session.questions
            if item.answer and item.order_index <= parent.order_index
        ][-6:]
        raw = await _call_ai(ai_service.generate_interview_follow_up(
            self._question_context(parent), parent.answer, parent.evaluation or {},
            self._job_context(session.job), prior_turns=recent_turns,
        ))
        follow_up = raw.get("follow_up_question") if isinstance(raw, dict) else None
        if not isinstance(follow_up, str) or not follow_up.strip() or len(follow_up) > 2000:
            raise AIProviderError(502, "The AI provider returned an invalid follow-up question. Please retry.")
        question = AIInterviewQuestion(
            session_id=session.id,
            parent_question_id=parent.id,
            order_index=max((item.order_index for item in session.questions), default=0) + 1,
            question=follow_up.strip(), category=parent.category, difficulty=parent.difficulty,
            competency=parent.competency,
            job_relevance=f"Follow-up to assess {parent.competency} for {session.job.title if session.job else 'general screening'}.",
            expected_concepts=parent.expected_concepts or [],
            evaluation_rubric=parent.evaluation_rubric or {},
            status="pending",
        )
        self.db.add(question)
        await self._commit()
        return await self.get(recruiter_id, session_id)

    async def complete(self, recruiter_id: UUID, session_id: UUID):
        session = await self.get(recruiter_id, session_id)
        if session.status not in ("in_progress", "paused"):
            raise ValueError("Only an active or paused interview can be completed")
        if not session.questions or any(q.status == "pending" for q in session.questions):
            raise ValueError("Answer or skip every question before completing the interview")
        if any(q.status == "answered" and (not q.evaluation or q.score is None) for q in session.questions):
            raise ValueError("Evaluate each answered question before completing the interview")
        session.completed_at = datetime.now(timezone.utc)
        session.status = "completed"
        session.overall_report = build_final_report(session)
        await self._commit()
        return await self.get(recruiter_id, session_id)

    async def update_review(self, recruiter_id: UUID, session_id: UUID, *, recruiter_notes=None, final_decision=None):
        session = await self.get(recruiter_id, session_id)
        if recruiter_notes is not None:
            session.recruiter_notes = recruiter_notes
        if final_decision is not None:
            session.final_decision = final_decision
        await self._commit()
        return await self.get(recruiter_id, session_id)

    async def report(self, recruiter_id: UUID, session_id: UUID):
        session = await self.get(recruiter_id, session_id)
        if session.status != "completed" or not session.overall_report:
            raise ValueError("Complete the interview to view its report")
        return session, session.overall_report
