"""Add persistent AI interview assistant sessions and questions."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004_ai_interview_assistant"
down_revision: Union[str, None] = "003_interviews"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_interview_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recruiter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interview_type", sa.String(30), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("overall_report", postgresql.JSONB(), nullable=True),
        sa.Column("recruiter_notes", sa.Text(), nullable=True),
        sa.Column("final_decision", sa.String(50), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("interview_type IN ('technical', 'behavioral', 'hr', 'situational', 'project_based', 'mixed')", name="ck_ai_interview_type"),
        sa.CheckConstraint("difficulty IN ('easy', 'intermediate', 'advanced')", name="ck_ai_interview_difficulty"),
        sa.CheckConstraint("question_count BETWEEN 5 AND 20", name="ck_ai_interview_question_count"),
        sa.CheckConstraint("status IN ('draft', 'in_progress', 'paused', 'completed')", name="ck_ai_interview_status"),
    )
    for name, table, columns in (
        ("ix_ai_interview_sessions_candidate_id", "ai_interview_sessions", ["candidate_id"]),
        ("ix_ai_interview_sessions_job_id", "ai_interview_sessions", ["job_id"]),
        ("ix_ai_interview_sessions_recruiter_id", "ai_interview_sessions", ["recruiter_id"]),
        ("ix_ai_interview_sessions_status", "ai_interview_sessions", ["status"]),
    ):
        op.create_index(name, table, columns)

    op.create_table(
        "ai_interview_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ai_interview_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("competency", sa.String(255), nullable=False),
        sa.Column("job_relevance", sa.Text(), nullable=False),
        sa.Column("expected_concepts", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("evaluation_rubric", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("follow_up_question", sa.Text(), nullable=True),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("evaluation", postgresql.JSONB(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("answer_quality", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("session_id", "order_index", name="uq_ai_interview_question_order"),
        sa.CheckConstraint("status IN ('pending', 'answered', 'skipped', 'unevaluable')", name="ck_ai_interview_question_status"),
        sa.CheckConstraint("score IS NULL OR score BETWEEN 0 AND 100", name="ck_ai_interview_question_score"),
    )
    op.create_index("ix_ai_interview_questions_session_id", "ai_interview_questions", ["session_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_interview_questions_session_id", table_name="ai_interview_questions")
    op.drop_table("ai_interview_questions")
    for name in ("ix_ai_interview_sessions_status", "ix_ai_interview_sessions_recruiter_id", "ix_ai_interview_sessions_job_id", "ix_ai_interview_sessions_candidate_id"):
        op.drop_index(name, table_name="ai_interview_sessions")
    op.drop_table("ai_interview_sessions")
