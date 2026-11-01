from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, Field, field_validator

InterviewType = Literal["technical", "behavioral", "hr", "hiring_manager", "phone_screen", "other"]
InterviewStatus = Literal["scheduled", "completed", "cancelled", "rescheduled"]
Recommendation = Literal["strong_yes", "yes", "maybe", "no"]


class InterviewCreate(BaseModel):
    candidate_id: UUID
    job_id: Optional[UUID] = None
    interviewer_user_id: Optional[UUID] = None
    interviewer_name: str = Field(min_length=1, max_length=255)
    interview_type: InterviewType
    scheduled_at: datetime
    timezone: str = Field(min_length=1, max_length=100)
    duration_minutes: int = Field(default=60, ge=5, le=720)
    location: Optional[str] = Field(default=None, max_length=500)
    meeting_link: Optional[str] = Field(default=None, max_length=1000)
    notes: Optional[str] = Field(default=None, max_length=10000)

    @field_validator("scheduled_at")
    @classmethod
    def require_aware_date(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Scheduled date/time must include a timezone offset")
        return value

    @field_validator("timezone")
    @classmethod
    def require_known_timezone(cls, value):
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Enter a valid IANA timezone, such as Asia/Kolkata") from exc
        return value

    @field_validator("meeting_link")
    @classmethod
    def validate_meeting_link(cls, value):
        if value and not value.startswith(("https://", "http://")):
            raise ValueError("Meeting link must start with http:// or https://")
        return value


class InterviewUpdate(BaseModel):
    job_id: Optional[UUID] = None
    interviewer_user_id: Optional[UUID] = None
    interviewer_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    interview_type: Optional[InterviewType] = None
    scheduled_at: Optional[datetime] = None
    timezone: Optional[str] = Field(default=None, min_length=1, max_length=100)
    duration_minutes: Optional[int] = Field(default=None, ge=5, le=720)
    location: Optional[str] = Field(default=None, max_length=500)
    meeting_link: Optional[str] = Field(default=None, max_length=1000)
    notes: Optional[str] = Field(default=None, max_length=10000)

    @field_validator("scheduled_at")
    @classmethod
    def require_aware_date(cls, value):
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Scheduled date/time must include a timezone offset")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value):
        if value is not None:
            try:
                ZoneInfo(value)
            except ZoneInfoNotFoundError as exc:
                raise ValueError("Enter a valid IANA timezone, such as Asia/Kolkata") from exc
        return value

    @field_validator("meeting_link")
    @classmethod
    def validate_meeting_link(cls, value):
        if value and not value.startswith(("https://", "http://")):
            raise ValueError("Meeting link must start with http:// or https://")
        return value


class InterviewFeedbackCreate(BaseModel):
    skills_rating: int = Field(ge=1, le=5)
    communication_rating: int = Field(ge=1, le=5)
    problem_solving_rating: int = Field(ge=1, le=5)
    overall_rating: int = Field(ge=1, le=5)
    recommendation: Recommendation
    notes: Optional[str] = Field(default=None, max_length=10000)


class InterviewFeedbackResponse(InterviewFeedbackCreate):
    id: UUID
    submitted_by_id: Optional[UUID] = None
    submitted_by_name: Optional[str] = None
    updated_at: datetime


class InterviewResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    candidate_name: str
    candidate_email: Optional[str] = None
    job_id: Optional[UUID] = None
    job_title: Optional[str] = None
    interviewer_user_id: Optional[UUID] = None
    interviewer_name: str
    interview_type: InterviewType
    scheduled_at: datetime
    timezone: str
    duration_minutes: int
    location: Optional[str] = None
    meeting_link: Optional[str] = None
    notes: Optional[str] = None
    status: InterviewStatus
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime
    feedback: Optional[InterviewFeedbackResponse] = None


class InterviewFilters(BaseModel):
    search: Optional[str] = None
    status: Optional[InterviewStatus] = None
    job_id: Optional[UUID] = None
    interview_type: Optional[InterviewType] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
