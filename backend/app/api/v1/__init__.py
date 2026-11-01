from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.candidates import router as candidates_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.reports import router as reports_router
from app.api.v1.users import router as users_router
from app.api.v1.pipeline import router as pipeline_router
from app.api.v1.interviews import router as interviews_router
from app.api.v1.ai_interviews import router as ai_interviews_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(jobs_router)
api_router.include_router(candidates_router)
api_router.include_router(dashboard_router)
api_router.include_router(reports_router)
api_router.include_router(users_router)
api_router.include_router(pipeline_router)
api_router.include_router(interviews_router)
api_router.include_router(ai_interviews_router)
