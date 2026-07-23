import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database.base import Base


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), nullable=False)
    question = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    difficulty = Column(String(20), nullable=False)
    expected_answer = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    candidate = relationship("Candidate", back_populates="interview_questions")


class ATSResult(Base):
    __tablename__ = "ats_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), unique=True, nullable=False)
    total_score = Column(Float, nullable=False, default=0.0)
    skills_score = Column(Float, default=0.0)
    experience_score = Column(Float, default=0.0)
    education_score = Column(Float, default=0.0)
    projects_score = Column(Float, default=0.0)
    formatting_score = Column(Float, default=0.0)
    certifications_score = Column(Float, default=0.0)
    keywords_match = Column(JSONB, default=list, nullable=True)
    missing_keywords = Column(JSONB, default=list, nullable=True)
    matched_skills = Column(JSONB, default=list, nullable=True)
    missing_skills = Column(JSONB, default=list, nullable=True)
    recommended_skills = Column(JSONB, default=list, nullable=True)
    learning_roadmap = Column(JSONB, default=list, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    candidate = relationship("Candidate", back_populates="ats_result")


class AIAnalysis(Base):
    __tablename__ = "ai_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id"), unique=True, nullable=False)
    match_score = Column(Float, default=0.0)
    jd_match_score = Column(Float, default=0.0)
    skills_match = Column(JSONB, default=list, nullable=True)
    experience_match = Column(JSONB, default=list, nullable=True)
    education_match = Column(JSONB, default=list, nullable=True)
    projects_match = Column(JSONB, default=list, nullable=True)
    certifications_match = Column(JSONB, default=list, nullable=True)
    summary = Column(Text, nullable=True)
    strengths = Column(JSONB, default=list, nullable=True)
    weaknesses = Column(JSONB, default=list, nullable=True)
    career_highlights = Column(JSONB, default=list, nullable=True)
    hiring_recommendation = Column(String(50), nullable=True)
    recommendation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    candidate = relationship("Candidate", back_populates="ai_analysis")
