"""add unique external identifiers

Revision ID: 562c5611260f
Revises: bfaf009b6d24
Create Date: 2026-10-05
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "562c5611260f"
down_revision: Union[str, Sequence[str], None] = "bfaf009b6d24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("courses") as batch_op:
        batch_op.create_unique_constraint(
            "uq_courses_source",
            ["source", "external_id"],
        )

    with op.batch_alter_table("assignments") as batch_op:
        batch_op.create_unique_constraint(
            "uq_assignments_source",
            ["source", "external_id"],
        )

    with op.batch_alter_table("events") as batch_op:
        batch_op.create_unique_constraint(
            "uq_events_source",
            ["source", "external_id"],
        )

    with op.batch_alter_table("documents") as batch_op:
        batch_op.create_unique_constraint(
            "uq_documents_source",
            ["source", "external_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("documents") as batch_op:
        batch_op.drop_constraint(
            "uq_documents_source",
            type_="unique",
        )

    with op.batch_alter_table("events") as batch_op:
        batch_op.drop_constraint(
            "uq_events_source",
            type_="unique",
        )

    with op.batch_alter_table("assignments") as batch_op:
        batch_op.drop_constraint(
            "uq_assignments_source",
            type_="unique",
        )

    with op.batch_alter_table("courses") as batch_op:
        batch_op.drop_constraint(
            "uq_courses_source",
            type_="unique",
        )