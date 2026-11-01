from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException

from app.api.v1 import candidates as candidates_api
from app.repositories.candidate_repo import CandidateRepository


class EmptyScalars:
    def all(self):
        return []


class EmptyResult:
    def scalars(self):
        return EmptyScalars()


class RecordingSession:
    def __init__(self):
        self.statement = None

    async def execute(self, statement):
        self.statement = statement
        return EmptyResult()


class CandidateJobFilterTests(IsolatedAsyncioTestCase):
    async def test_candidate_query_combines_search_rank_and_job_filter(self):
        db = RecordingSession()

        await CandidateRepository(db).list_with_relations(
            skip=5,
            limit=25,
            search="engineer",
            rank="gold",
            job_id=uuid4(),
        )

        sql = str(db.statement)
        self.assertIn("candidates.job_id =", sql)
        self.assertIn("candidates.rank =", sql)
        self.assertIn("candidates.name", sql)
        self.assertIn("LIMIT", sql)
        self.assertIn("OFFSET", sql)

    async def test_candidate_query_can_select_unassigned_candidates(self):
        db = RecordingSession()

        await CandidateRepository(db).list_with_relations(unassigned=True)

        self.assertIn("candidates.job_id IS NULL", str(db.statement))

    async def test_candidate_endpoint_passes_combined_filters(self):
        owner_id = uuid4()
        job_id = uuid4()
        received = {}

        class FakeJobService:
            def __init__(self, db):
                pass

            async def get_job(self, requested_job_id):
                if requested_job_id != job_id:
                    raise AssertionError("The selected job ID was not validated")
                return SimpleNamespace(id=job_id, owner_id=owner_id)

        class FakeCandidateService:
            def __init__(self, db):
                pass

            async def list_candidates(self, **kwargs):
                received.update(kwargs)
                return []

        with patch.object(candidates_api, "JobService", FakeJobService), patch.object(
            candidates_api, "CandidateService", FakeCandidateService
        ):
            result = await candidates_api.list_candidates(
                skip=10,
                limit=20,
                search="react",
                rank="silver",
                job_id=job_id,
                unassigned=False,
                current_user=SimpleNamespace(id=owner_id),
                db=object(),
            )

        self.assertEqual(result, [])
        self.assertEqual(
            received,
            {
                "skip": 10,
                "limit": 20,
                "search": "react",
                "rank": "silver",
                "job_id": job_id,
                "unassigned": False,
            },
        )

    async def test_candidate_endpoint_rejects_missing_or_other_users_job(self):
        owner_id = uuid4()
        job_id = uuid4()

        class FakeJobService:
            def __init__(self, db):
                pass

            async def get_job(self, requested_job_id):
                return SimpleNamespace(id=requested_job_id, owner_id=uuid4())

        class UnexpectedCandidateService:
            def __init__(self, db):
                raise AssertionError("Candidate query should not run for an inaccessible job")

        with patch.object(candidates_api, "JobService", FakeJobService), patch.object(
            candidates_api, "CandidateService", UnexpectedCandidateService
        ):
            with self.assertRaises(HTTPException) as error:
                await candidates_api.list_candidates(
                    skip=0,
                    limit=50,
                    search=None,
                    rank=None,
                    job_id=job_id,
                    unassigned=False,
                    current_user=SimpleNamespace(id=owner_id),
                    db=object(),
                )

        self.assertEqual(error.exception.status_code, 404)

    async def test_candidate_endpoint_rejects_conflicting_job_and_unassigned_filters(self):
        with self.assertRaises(HTTPException) as error:
            await candidates_api.list_candidates(
                skip=0,
                limit=50,
                search=None,
                rank=None,
                job_id=uuid4(),
                unassigned=True,
                current_user=SimpleNamespace(id=uuid4()),
                db=object(),
            )

        self.assertEqual(error.exception.status_code, 400)
