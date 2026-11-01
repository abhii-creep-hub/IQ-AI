"""Add recruitment pipeline stage to candidates."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_recruitment_pipeline"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("candidates", sa.Column("recruitment_stage", sa.String(20), nullable=False, server_default="applied"))
    op.create_check_constraint(
        "ck_candidates_recruitment_stage", "candidates",
        "recruitment_stage IN ('applied', 'screening', 'shortlisted', 'interview', 'offer', 'hired', 'rejected')",
    )
    op.create_index("ix_candidates_recruitment_stage", "candidates", ["recruitment_stage"])


def downgrade() -> None:
    op.drop_index("ix_candidates_recruitment_stage", table_name="candidates")
    op.drop_constraint("ck_candidates_recruitment_stage", "candidates", type_="check")
    op.drop_column("candidates", "recruitment_stage")
