import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy.dialects import postgresql

from app.schemas.pipeline import PipelineStageUpdate
from app.services.pipeline_service import PIPELINE_STAGES, PipelineService


class PipelineSchemaTests(unittest.TestCase):
    def test_all_supported_stages_are_accepted(self):
        for stage in PIPELINE_STAGES:
            self.assertEqual(PipelineStageUpdate(stage=stage).stage, stage)

    def test_unknown_stage_is_rejected(self):
        with self.assertRaises(ValidationError):
            PipelineStageUpdate(stage="processing")


class FakeScalars:
    def __init__(self, values):
        self.values = values

    def all(self):
        return self.values


class PipelineServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_list_query_is_scoped_to_owned_jobs_and_uploaded_unassigned_candidates(self):
        db = SimpleNamespace(
            scalars=AsyncMock(return_value=FakeScalars([])),
        )
        service = PipelineService(db)
        await service.list_candidates(uuid4(), search="dev", stage="interview")
        query = db.scalars.await_args.args[0]
        sql = str(query.compile(dialect=postgresql.dialect()))
        self.assertIn("jobs.owner_id", sql)
        self.assertIn("resumes.uploaded_by", sql)
        self.assertIn("candidates.recruitment_stage", sql)
        self.assertIn("candidates.name", sql)

    async def test_move_writes_stage_and_audit_event_together(self):
        user_id = uuid4()
        candidate = SimpleNamespace(id=uuid4(), recruitment_stage="applied")
        db = SimpleNamespace(add=lambda item: added.append(item), commit=AsyncMock(), refresh=AsyncMock(), rollback=AsyncMock())
        added = []
        service = PipelineService(db)
        service.get_candidate = AsyncMock(return_value=candidate)

        result = await service.move_candidate(SimpleNamespace(id=user_id), candidate.id, "screening")

        self.assertIs(result, candidate)
        self.assertEqual(candidate.recruitment_stage, "screening")
        self.assertEqual(len(added), 1)
        self.assertEqual(added[0].action, "candidate_stage_changed")
        self.assertEqual(added[0].details, {"previous_stage": "applied", "new_stage": "screening"})
        db.commit.assert_awaited_once()

    async def test_same_stage_does_not_create_an_audit_event(self):
        candidate = SimpleNamespace(id=uuid4(), recruitment_stage="applied")
        added = []
        db = SimpleNamespace(add=added.append, commit=AsyncMock(), refresh=AsyncMock(), rollback=AsyncMock())
        service = PipelineService(db)
        service.get_candidate = AsyncMock(return_value=candidate)

        await service.move_candidate(SimpleNamespace(id=uuid4()), candidate.id, "applied")

        self.assertEqual(added, [])
        db.commit.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
