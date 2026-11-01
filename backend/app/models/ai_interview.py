import uuid
from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base


class AIInterviewSession(Base):
    __tablename__ = "ai_interview_sessions"
    __table_args__ = (
        CheckConstraint("interview_type IN ('technical', 'behavioral', 'hr', 'situational', 'project_based', 'mixed')", name="ck_ai_interview_type"),
        CheckConstraint("difficulty IN ('easy', 'intermediate', 'advanced')", name="ck_ai_interview_difficulty"),
        CheckConstraint("question_count BETWEEN 5 AND 20", name="ck_ai_interview_question_count"),
        CheckConstraint("status IN ('draft', 'in_progress', 'paused', 'completed')", name="ck_ai_interview_status"),
        CheckConstraint("mode IN ('written', 'voice', 'live_ai')", name="ck_ai_interview_mode"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    recruiter_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    interview_type = Column(String(30), nullable=False)
    mode = Column(String(20), nullable=False, default="written", server_default="written")
    difficulty = Column(String(20), nullable=False)
    question_count = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="draft", index=True)
    overall_report = Column(JSONB, nullable=True)
    recruiter_notes = Column(Text, nullable=True)
    final_decision = Column(String(50), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    candidate = relationship("Candidate")
    job = relationship("Job")
    recruiter = relationship("User")
    questions = relationship(
        "AIInterviewQuestion", back_populates="session", cascade="all, delete-orphan",
        order_by="AIInterviewQuestion.order_index",
    )


class AIInterviewQuestion(Base):
    __tablename__ = "ai_interview_questions"
    __table_args__ = (
        UniqueConstraint("session_id", "order_index", name="uq_ai_interview_question_order"),
        CheckConstraint("status IN ('pending', 'answered', 'skipped', 'unevaluable')", name="ck_ai_interview_question_status"),
        CheckConstraint("score IS NULL OR score BETWEEN 0 AND 100", name="ck_ai_interview_question_score"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("ai_interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_question_id = Column(UUID(as_uuid=True), ForeignKey("ai_interview_questions.id", ondelete="SET NULL"), nullable=True)
    order_index = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    difficulty = Column(String(20), nullable=False)
    competency = Column(String(255), nullable=False)
    job_relevance = Column(Text, nullable=False)
    expected_concepts = Column(JSONB, nullable=False, default=list)
    evaluation_rubric = Column(JSONB, nullable=False, default=dict)
    follow_up_question = Column(Text, nullable=True)
    answer = Column(Text, nullable=True)
    evaluation = Column(JSONB, nullable=True)
    score = Column(Float, nullable=True)
    answer_quality = Column(String(20), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    session = relationship("AIInterviewSession", back_populates="questions")
