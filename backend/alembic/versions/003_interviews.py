"""Add interview scheduling and feedback."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003_interviews"
down_revision: Union[str, None] = "002_recruitment_pipeline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("interviewer_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("interviewer_name", sa.String(255), nullable=False),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("interview_type", sa.String(40), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(100), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("meeting_link", sa.String(1000), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('scheduled', 'completed', 'cancelled', 'rescheduled')", name="ck_interviews_status"),
        sa.CheckConstraint("duration_minutes BETWEEN 5 AND 720", name="ck_interviews_duration"),
    )
    op.create_index("ix_interviews_candidate_id", "interviews", ["candidate_id"])
    op.create_index("ix_interviews_job_id", "interviews", ["job_id"])
    op.create_index("ix_interviews_interviewer_user_id", "interviews", ["interviewer_user_id"])
    op.create_index("ix_interviews_scheduled_at", "interviews", ["scheduled_at"])
    op.create_index("ix_interviews_status", "interviews", ["status"])

    op.create_table(
        "interview_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("interview_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("submitted_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("skills_rating", sa.Integer(), nullable=False),
        sa.Column("communication_rating", sa.Integer(), nullable=False),
        sa.Column("problem_solving_rating", sa.Integer(), nullable=False),
        sa.Column("overall_rating", sa.Integer(), nullable=False),
        sa.Column("recommendation", sa.String(20), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("skills_rating BETWEEN 1 AND 5", name="ck_interview_feedback_skills_rating"),
        sa.CheckConstraint("communication_rating BETWEEN 1 AND 5", name="ck_interview_feedback_communication_rating"),
        sa.CheckConstraint("problem_solving_rating BETWEEN 1 AND 5", name="ck_interview_feedback_problem_solving_rating"),
        sa.CheckConstraint("overall_rating BETWEEN 1 AND 5", name="ck_interview_feedback_overall_rating"),
        sa.CheckConstraint("recommendation IN ('strong_yes', 'yes', 'maybe', 'no')", name="ck_interview_feedback_recommendation"),
    )


def downgrade() -> None:
    op.drop_table("interview_feedback")
    for name in ("ix_interviews_status", "ix_interviews_scheduled_at", "ix_interviews_interviewer_user_id", "ix_interviews_job_id", "ix_interviews_candidate_id"):
        op.drop_index(name, table_name="interviews")
    op.drop_table("interviews")
