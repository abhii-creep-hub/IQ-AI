import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from pydantic import ValidationError

from app.schemas.ai_interview import AISessionCreate
from app.services.ai_interview_service import AIInterviewService, build_final_report


def create_payload(**updates):
    payload = {
        "candidate_id": uuid4(), "interview_type": "mixed",
        "difficulty": "intermediate", "question_count": 5,
    }
    payload.update(updates)
    return payload


class InterviewModeSchemaTests(unittest.TestCase):
    def test_written_mode_remains_the_default_for_existing_clients(self):
        data = AISessionCreate(**create_payload())
        self.assertEqual(data.mode, "written")

    def test_voice_and_live_ai_modes_are_valid_and_unknown_modes_rejected(self):
        for mode in ("voice", "live_ai"):
            self.assertEqual(AISessionCreate(**create_payload(mode=mode)).mode, mode)
        with self.assertRaises(ValidationError):
            AISessionCreate(**create_payload(mode="streaming"))


class WrittenInterviewServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_written_mode_generates_and_persists_job_question_set(self):
        session = SimpleNamespace(
            id=uuid4(), mode="written", questions=[], candidate=SimpleNamespace(),
            job=None, interview_type="mixed", difficulty="intermediate", question_count=5,
        )
        inserted = []
        db = SimpleNamespace(add_all=inserted.extend, commit=AsyncMock(), rollback=AsyncMock())
        service = AIInterviewService(db)
        service.get = AsyncMock(side_effect=[session, session])
        service._candidate_ai_context = lambda _candidate: {"skills": ["Python"]}
        generated = {"questions": [{
            "question": f"Describe a practical Python solution for scenario {index}?",
            "category": "practical_problem_solving", "difficulty": "intermediate",
            "competency": "problem solving", "job_relevance": "Relevant to the role.",
            "expected_concepts": ["trade-offs"],
            "evaluation_rubric": {"technical_accuracy": "Accurate", "relevance": "Relevant", "depth": "Detailed", "practical_application": "Practical"},
            "follow_up_question": None,
        } for index in range(5)]}
        with patch("app.services.ai_interview_service.ai_service.generate_assistant_questions", new=AsyncMock(return_value=generated)):
            await service.generate_questions(uuid4(), session.id)
        self.assertEqual(len(inserted), 5)
        self.assertEqual([item.order_index for item in inserted], [1, 2, 3, 4, 5])
        self.assertTrue(all(item.status == "pending" for item in inserted))
        db.commit.assert_awaited_once()

    async def test_written_mode_evaluates_saved_answer_and_includes_it_in_report(self):
        question = SimpleNamespace(
            id=uuid4(), order_index=1, question="How would you improve this API?",
            category="practical_problem_solving", difficulty="intermediate",
            competency="API design", job_relevance="The role builds APIs.",
            expected_concepts=["measurement"], evaluation_rubric={"relevance": "Relevant"},
            answer="I would profile it before changing code.", evaluation=None,
            score=None, answer_quality=None, status="answered", follow_up_question=None,
        )
        session = SimpleNamespace(
            mode="written", status="in_progress", questions=[question], job=None,
            completed_at=None, interview_type="technical", difficulty="intermediate",
        )
        db = SimpleNamespace(commit=AsyncMock(), rollback=AsyncMock())
        service = AIInterviewService(db)
        service.get = AsyncMock(side_effect=[session, session])
        evaluation = {
            "score": 82, "answer_quality": "good", "technical_accuracy": 80,
            "relevance": 90, "depth_of_explanation": 75, "practical_application": 83,
            "strengths": ["Starts with measurement"], "missing_concepts": [],
            "improvements": [], "explanation": "The answer proposes profiling before changes.",
            "confidence": "high", "uncertain": False, "uncertainty_reason": None,
            "suggested_follow_up": None,
        }
        with patch("app.services.ai_interview_service.ai_service.evaluate_interview_answer", new=AsyncMock(return_value=evaluation)):
            await service.evaluate_answer(uuid4(), uuid4(), question.id)
        self.assertEqual(question.score, 82)
        self.assertEqual(question.status, "answered")
        report = build_final_report(session)
        self.assertEqual(report["overall_score"], 82)
        self.assertEqual(report["evaluated_questions"], 1)


class VoiceInterviewServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_voice_mode_transcribes_without_saving_recorded_audio(self):
        question_id = uuid4()
        session = SimpleNamespace(mode="voice", status="in_progress", questions=[SimpleNamespace(id=question_id)])
        db = SimpleNamespace(add=AsyncMock())
        service = AIInterviewService(db)
        service.get = AsyncMock(return_value=session)
        with patch("app.services.ai_interview_service.ai_service.transcribe_interview_audio", new=AsyncMock(return_value="Confirmed words")):
            result = await service.transcribe_answer(uuid4(), uuid4(), question_id, b"audio bytes", "audio/webm")
        self.assertEqual(result, {"transcript": "Confirmed words", "audio_saved": False})
        db.add.assert_not_called()

    async def test_written_mode_cannot_call_audio_transcription(self):
        question_id = uuid4()
        session = SimpleNamespace(mode="written", status="in_progress", questions=[SimpleNamespace(id=question_id)])
        service = AIInterviewService(SimpleNamespace())
        service.get = AsyncMock(return_value=session)
        with self.assertRaisesRegex(ValueError, "voice interview modes"):
            await service.transcribe_answer(uuid4(), uuid4(), question_id, b"audio", "audio/webm")


class LiveAIInterviewServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_live_follow_up_is_appended_as_a_saved_contextual_question(self):
        parent = SimpleNamespace(
            id=uuid4(), parent_question_id=None, order_index=1,
            question="How did you improve database performance?",
            answer="I used an index to reduce query time.",
            evaluation={"explanation": "Described a concrete database optimization."},
            category="practical_problem_solving", difficulty="intermediate",
            competency="database performance", job_relevance="This role optimizes APIs.",
            expected_concepts=["indexing"], evaluation_rubric={"relevance": "Explain trade-offs"},
        )
        session = SimpleNamespace(
            id=uuid4(), mode="live_ai", status="in_progress", questions=[parent],
            question_count=5, job=SimpleNamespace(
                title="Backend Engineer", description="", requirements="", responsibilities="",
                required_skills=[], preferred_skills=[], experience_min=None, experience_max=None,
            ),
        )
        added = []
        db = SimpleNamespace(add=added.append, commit=AsyncMock(), rollback=AsyncMock())
        service = AIInterviewService(db)
        service.get = AsyncMock(side_effect=[session, session])
        recruiter_id, session_id = uuid4(), session.id
        with patch("app.services.ai_interview_service.ai_service.generate_interview_follow_up", new=AsyncMock(return_value={
            "follow_up_question": "How did you measure the index's impact on write performance?",
        })) as generate:
            await service.append_live_follow_up(recruiter_id, session_id, parent.id)
        saved = added[0]
        self.assertEqual(saved.parent_question_id, parent.id)
        self.assertEqual(saved.order_index, 2)
        self.assertEqual(saved.status, "pending")
        self.assertIn("Backend Engineer", saved.job_relevance)
        self.assertEqual(generate.await_args.kwargs["prior_turns"][0]["confirmed_answer"], parent.answer)
        db.commit.assert_awaited_once()

    async def test_voice_mode_cannot_append_live_conversation_follow_up(self):
        session = SimpleNamespace(mode="voice")
        service = AIInterviewService(SimpleNamespace())
        service.get = AsyncMock(return_value=session)
        with self.assertRaisesRegex(ValueError, "Live AI mode"):
            await service.append_live_follow_up(uuid4(), uuid4(), uuid4())


if __name__ == "__main__":
    unittest.main()
