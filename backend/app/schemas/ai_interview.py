from datetime import datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field, model_validator

InterviewAssistantType = Literal["technical", "behavioral", "hr", "situational", "project_based", "mixed"]
InterviewDifficulty = Literal["easy", "intermediate", "advanced"]
QuestionCategory = Literal[
    "technical_knowledge", "practical_problem_solving", "project_experience",
    "behavioral_competencies", "role_specific_scenarios",
]
SessionStatus = Literal["draft", "in_progress", "paused", "completed"]
InterviewMode = Literal["written", "voice", "live_ai"]
QuestionStatus = Literal["pending", "answered", "skipped", "unevaluable"]
FinalDecision = Literal["strong_evidence", "potential_fit", "skill_gaps", "insufficient_evidence"]


class AISessionCreate(BaseModel):
    candidate_id: UUID
    job_id: Optional[UUID] = None
    interview_type: InterviewAssistantType
    mode: InterviewMode = "written"
    difficulty: InterviewDifficulty
    question_count: int = Field(ge=5, le=20)
    duration_minutes: Optional[int] = Field(default=None, ge=10, le=240)


class AssistantCandidateOption(BaseModel):
    id: UUID
    name: str
    email: Optional[str] = None
    job_id: Optional[UUID] = None
    job_title: Optional[str] = None
    rank: Optional[str] = None
    summary: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    experience_years: Optional[float] = None
    ats_score: Optional[float] = None


class AssistantJobOption(BaseModel):
    id: UUID
    title: str
    description: str
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None


class AIAnswerUpdate(BaseModel):
    answer: Optional[str] = Field(default=None, max_length=20000)
    skip: bool = False

    @model_validator(mode="after")
    def require_answer_or_skip(self):
        if self.skip and self.answer and self.answer.strip():
            raise ValueError("Skipped questions cannot include an answer")
        if not self.skip and not (self.answer and self.answer.strip()):
            raise ValueError("Enter an answer or skip this question")
        return self


class AISessionReviewUpdate(BaseModel):
    recruiter_notes: Optional[str] = Field(default=None, max_length=10000)
    final_decision: Optional[FinalDecision] = None
class EvaluationRubric(BaseModel):
    technical_accuracy: str
    relevance: str
    depth: str
    practical_application: str


class GeneratedInterviewQuestion(BaseModel):
    question: str = Field(min_length=10, max_length=3000)
    category: QuestionCategory
    difficulty: InterviewDifficulty
    competency: str = Field(min_length=2, max_length=255)
    job_relevance: str = Field(min_length=5, max_length=1500)
    expected_concepts: list[str] = Field(min_length=1, max_length=12)
    evaluation_rubric: EvaluationRubric
    follow_up_question: Optional[str] = Field(default=None, max_length=2000)


class GeneratedInterviewQuestions(BaseModel):
    questions: list[GeneratedInterviewQuestion]


class AIAnswerEvaluation(BaseModel):
    score: Optional[int] = Field(default=None, ge=0, le=100)
    answer_quality: Literal["poor", "fair", "good", "excellent"]
    technical_accuracy: Optional[int] = Field(default=None, ge=0, le=100)
    relevance: Optional[int] = Field(default=None, ge=0, le=100)
    depth_of_explanation: Optional[int] = Field(default=None, ge=0, le=100)
    practical_application: Optional[int] = Field(default=None, ge=0, le=100)
    strengths: list[str] = Field(default_factory=list, max_length=10)
    missing_concepts: list[str] = Field(default_factory=list, max_length=10)
    improvements: list[str] = Field(default_factory=list, max_length=10)
    explanation: str = Field(min_length=5, max_length=2000)
    confidence: Literal["high", "medium", "low"]
    uncertain: bool = False
    uncertainty_reason: Optional[str] = Field(default=None, max_length=1000)
    suggested_follow_up: Optional[str] = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def avoid_unjustified_scores(self):
        scores = (self.score, self.technical_accuracy, self.relevance,
                  self.depth_of_explanation, self.practical_application)
        if self.uncertain and any(value is not None for value in scores):
            raise ValueError("Uncertain evaluations must not include numeric scores")
        if not self.uncertain and any(value is None for value in scores):
            raise ValueError("Reliable evaluations require all rubric scores")
        if self.uncertain and not self.uncertainty_reason:
            raise ValueError("Explain why the answer could not be evaluated reliably")
        return self


class AIInterviewQuestionResponse(BaseModel):
    id: UUID
    order_index: int
    parent_question_id: Optional[UUID] = None
    question: str
    category: QuestionCategory
    difficulty: InterviewDifficulty
    competency: str
    job_relevance: str
    expected_concepts: list[str]
    evaluation_rubric: dict
    follow_up_question: Optional[str] = None
    answer: Optional[str] = None
    evaluation: Optional[AIAnswerEvaluation] = None
    score: Optional[float] = None
    answer_quality: Optional[str] = None
    status: QuestionStatus


class AIInterviewSessionSummary(BaseModel):
    id: UUID
    candidate_id: UUID
    candidate_name: str
    job_id: Optional[UUID] = None
    job_title: Optional[str] = None
    interview_type: InterviewAssistantType
    mode: InterviewMode = "written"
    difficulty: InterviewDifficulty
    question_count: int
    status: SessionStatus
    created_at: datetime
    completed_at: Optional[datetime] = None


class AIInterviewSessionResponse(AIInterviewSessionSummary):
    duration_minutes: Optional[int] = None
    candidate_summary: Optional[str] = None
    candidate_skills: list[str] = Field(default_factory=list)
    candidate_experience_years: Optional[float] = None
    ats_score: Optional[float] = None
    questions: list[AIInterviewQuestionResponse] = Field(default_factory=list)
    overall_report: Optional[dict] = None
    recruiter_notes: Optional[str] = None
    final_decision: Optional[FinalDecision] = None
