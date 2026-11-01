"""Add interview modes and persisted contextual follow-up links."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005_ai_interview_modes"
down_revision: Union[str, None] = "004_ai_interview_assistant"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ai_interview_sessions",
        sa.Column("mode", sa.String(length=20), nullable=False, server_default="written"),
    )
    op.create_check_constraint(
        "ck_ai_interview_mode", "ai_interview_sessions",
        "mode IN ('written', 'voice', 'live_ai')",
    )
    op.add_column(
        "ai_interview_questions",
        sa.Column(
            "parent_question_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_interview_questions.id", ondelete="SET NULL"), nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("ai_interview_questions", "parent_question_id")
    op.drop_constraint("ck_ai_interview_mode", "ai_interview_sessions", type_="check")
    op.drop_column("ai_interview_sessions", "mode")
