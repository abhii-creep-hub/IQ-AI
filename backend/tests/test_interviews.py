import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from app.schemas.interview import InterviewCreate, InterviewFeedbackCreate
from app.services.interview_service import InterviewService, candidate_access_clause
from app.models.interview import Interview


class InterviewSchemaTests(unittest.TestCase):
    def create_payload(self, **changes):
        payload = {
            "candidate_id": uuid4(), "interviewer_name": "Interviewer",
            "interview_type": "technical",
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            "timezone": "Asia/Kolkata", "duration_minutes": 45,
        }
        payload.update(changes)
        return payload

    def test_accepts_valid_timezone_aware_interview(self):
        interview = InterviewCreate(**self.create_payload())
        self.assertEqual(interview.duration_minutes, 45)

    def test_rejects_timezone_naive_schedule_and_unknown_timezone(self):
        with self.assertRaises(ValidationError):
            InterviewCreate(**self.create_payload(scheduled_at="2030-01-01T10:00:00"))
        with self.assertRaises(ValidationError):
            InterviewCreate(**self.create_payload(timezone="Mars/Olympus"))

    def test_feedback_ratings_must_be_in_range(self):
        with self.assertRaises(ValidationError):
            InterviewFeedbackCreate(
                skills_rating=6, communication_rating=3, problem_solving_rating=3,
                overall_rating=3, recommendation="yes",
            )


class InterviewServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_candidate_visibility_is_limited_to_owned_jobs_or_uploaded_unassigned(self):
        statement = select_sql = str(candidate_access_clause(uuid4()).compile(dialect=postgresql.dialect()))
        self.assertIn("jobs.owner_id", statement)
        self.assertIn("resumes.uploaded_by", statement)
        self.assertIn("candidates.job_id", select_sql)

    async def test_past_schedule_is_rejected_before_database_access(self):
        db = SimpleNamespace()
        service = InterviewService(db)
        user = SimpleNamespace(id=uuid4())
        payload = {
            "candidate_id": uuid4(), "scheduled_at": datetime.now(timezone.utc) - timedelta(days=1),
        }
        with self.assertRaisesRegex(ValueError, "future"):
            await service.create(user, payload)

    async def test_create_schedules_candidate_interview_and_records_activity(self):
        candidate = SimpleNamespace(id=uuid4(), job_id=None)
        added = []

        class FakeSession:
            interview = None
            def add(self, item):
                added.append(item)
                if isinstance(item, Interview):
                    item.id = uuid4()
                    self.interview = item
            async def flush(self):
                return None
            async def commit(self):
                return None
            async def rollback(self):
                return None
            async def scalar(self, _query):
                return self.interview

        user = SimpleNamespace(id=uuid4())
        service = InterviewService(FakeSession())
        service._candidate = AsyncMock(return_value=candidate)
        service._interviewer = AsyncMock(return_value=None)
        data = {
            "candidate_id": candidate.id, "job_id": None, "interviewer_user_id": None,
            "interviewer_name": "Recruiter", "interview_type": "technical",
            "scheduled_at": datetime.now(timezone.utc) + timedelta(days=1),
            "timezone": "Asia/Kolkata", "duration_minutes": 45,
            "location": None, "meeting_link": None, "notes": None,
        }

        interview = await service.create(user, data)

        self.assertEqual(interview.candidate_id, candidate.id)
        self.assertEqual(interview.status, "scheduled")
        self.assertEqual(added[-1].action, "interview_scheduled")

    async def test_complete_status_is_recorded_and_logged(self):
        user_id, interview_id = uuid4(), uuid4()
        interview = SimpleNamespace(id=interview_id, candidate_id=uuid4(), created_by_id=user_id,
                                    interviewer_user_id=None, status="scheduled")
        added = []
        db = SimpleNamespace(add=added.append, commit=AsyncMock(), rollback=AsyncMock())
        service = InterviewService(db)
        service.get = AsyncMock(return_value=interview)
        service._candidate_owned = AsyncMock(return_value=True)

        result = await service.change_status(SimpleNamespace(id=user_id), interview_id, "completed")

        self.assertIs(result, interview)
        self.assertEqual(interview.status, "completed")
        self.assertEqual(added[0].action, "interview_completed")
        db.commit.assert_awaited_once()

    async def test_only_assigned_interviewer_can_submit_feedback(self):
        interviewer_id = uuid4()
        interview = SimpleNamespace(id=uuid4(), interviewer_user_id=interviewer_id,
                                    created_by_id=uuid4(), status="completed", feedback=None)
        service = InterviewService(SimpleNamespace())
        service.get = AsyncMock(return_value=interview)
        with self.assertRaises(PermissionError):
            await service.save_feedback(SimpleNamespace(id=uuid4()), interview.id, {
                "skills_rating": 4, "communication_rating": 4,
                "problem_solving_rating": 4, "overall_rating": 4,
                "recommendation": "yes", "notes": None,
            })

    async def test_interview_cannot_be_assigned_to_another_recruiter(self):
        user = SimpleNamespace(id=uuid4())
        service = InterviewService(SimpleNamespace())
        service._candidate = AsyncMock(return_value=SimpleNamespace(id=uuid4(), job_id=None))
        data = {
            "candidate_id": uuid4(), "job_id": None, "interviewer_user_id": uuid4(),
            "interviewer_name": "Other recruiter", "scheduled_at": datetime.now(timezone.utc) + timedelta(days=1),
        }
        with self.assertRaisesRegex(PermissionError, "your own account"):
            await service.create(user, data)

    async def test_feedback_requires_completed_interview(self):
        user_id = uuid4()
        interview = SimpleNamespace(id=uuid4(), interviewer_user_id=None,
                                    created_by_id=user_id, status="scheduled", feedback=None)
        service = InterviewService(SimpleNamespace())
        service.get = AsyncMock(return_value=interview)
        with self.assertRaisesRegex(ValueError, "Complete the interview"):
            await service.save_feedback(SimpleNamespace(id=user_id), interview.id, {
                "skills_rating": 4, "communication_rating": 4,
                "problem_solving_rating": 4, "overall_rating": 4,
                "recommendation": "yes", "notes": None,
            })


if __name__ == "__main__":
    unittest.main()
