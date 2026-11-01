import uuid
from datetime import datetime, timezone
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database.base import Base


class Interview(Base):
    __tablename__ = "interviews"
    __table_args__ = (
        CheckConstraint("status IN ('scheduled', 'completed', 'cancelled', 'rescheduled')", name="ck_interviews_status"),
        CheckConstraint("duration_minutes BETWEEN 5 AND 720", name="ck_interviews_duration"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True, index=True)
    interviewer_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    interviewer_name = Column(String(255), nullable=False)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    interview_type = Column(String(40), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    timezone = Column(String(100), nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=60)
    location = Column(String(500), nullable=True)
    meeting_link = Column(String(1000), nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="scheduled", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    candidate = relationship("Candidate", back_populates="interviews")
    job = relationship("Job", back_populates="interviews")
    interviewer = relationship("User", foreign_keys=[interviewer_user_id])
    creator = relationship("User", foreign_keys=[created_by_id])
    feedback = relationship("InterviewFeedback", back_populates="interview", uselist=False, cascade="all, delete-orphan")


class InterviewFeedback(Base):
    __tablename__ = "interview_feedback"
    __table_args__ = (
        CheckConstraint("skills_rating BETWEEN 1 AND 5", name="ck_interview_feedback_skills_rating"),
        CheckConstraint("communication_rating BETWEEN 1 AND 5", name="ck_interview_feedback_communication_rating"),
        CheckConstraint("problem_solving_rating BETWEEN 1 AND 5", name="ck_interview_feedback_problem_solving_rating"),
        CheckConstraint("overall_rating BETWEEN 1 AND 5", name="ck_interview_feedback_overall_rating"),
        CheckConstraint("recommendation IN ('strong_yes', 'yes', 'maybe', 'no')", name="ck_interview_feedback_recommendation"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    interview_id = Column(UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, unique=True)
    submitted_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    skills_rating = Column(Integer, nullable=False)
    communication_rating = Column(Integer, nullable=False)
    problem_solving_rating = Column(Integer, nullable=False)
    overall_rating = Column(Integer, nullable=False)
    recommendation = Column(String(20), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    interview = relationship("Interview", back_populates="feedback")
    submitted_by = relationship("User", foreign_keys=[submitted_by_id])
