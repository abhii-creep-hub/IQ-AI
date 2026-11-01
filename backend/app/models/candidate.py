import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, Integer, Boolean, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from app.database.base import Base


class Candidate(Base):
    __tablename__ = "candidates"
    __table_args__ = (CheckConstraint(
        "recruitment_stage IN ('applied', 'screening', 'shortlisted', 'interview', 'offer', 'hired', 'rejected')",
        name="ck_candidates_recruitment_stage",
    ),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    total_experience_years = Column(Float, nullable=True)
    rank = Column(String(20), default="pending", nullable=False)
    status = Column(String(20), default="uploaded", nullable=False)
    recruitment_stage = Column(String(20), default="applied", nullable=False, index=True)
    ai_summary = Column(Text, nullable=True)
    ai_strengths = Column(JSONB, default=list, nullable=True)
    ai_weaknesses = Column(JSONB, default=list, nullable=True)
    ai_career_highlights = Column(JSONB, default=list, nullable=True)
    hiring_recommendation = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    job = relationship("Job", back_populates="candidates")
    resume = relationship("Resume", back_populates="candidate", uselist=False, cascade="all, delete-orphan")
    skills = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    education = relationship("Education", back_populates="candidate", cascade="all, delete-orphan")
    experience = relationship("Experience", back_populates="candidate", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="candidate", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="candidate", cascade="all, delete-orphan")
    ats_result = relationship("ATSResult", back_populates="candidate", uselist=False, cascade="all, delete-orphan")
    ai_analysis = relationship("AIAnalysis", back_populates="candidate", uselist=False, cascade="all, delete-orphan")
    interview_questions = relationship("InterviewQuestion", back_populates="candidate", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="candidate", cascade="all, delete-orphan")
