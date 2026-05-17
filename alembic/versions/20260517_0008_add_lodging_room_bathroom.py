"""add bathroom fields to lodging_rooms

Revision ID: 20260517_0008
Revises: 20260511_0007
Create Date: 2026-05-17 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "20260517_0008"
down_revision: Union[str, Sequence[str], None] = "20260511_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "lodging_rooms" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("lodging_rooms")}
    if "has_private_bathroom" not in columns:
        op.add_column(
            "lodging_rooms",
            sa.Column("has_private_bathroom", sa.Boolean(), nullable=False, server_default=sa.true()),
        )
    if "bathroom_description" not in columns:
        op.add_column("lodging_rooms", sa.Column("bathroom_description", sa.String(length=500), nullable=True))
    if "bathroom_images" not in columns:
        op.add_column("lodging_rooms", sa.Column("bathroom_images", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "lodging_rooms" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("lodging_rooms")}
    if "bathroom_images" in columns:
        op.drop_column("lodging_rooms", "bathroom_images")
    if "bathroom_description" in columns:
        op.drop_column("lodging_rooms", "bathroom_description")
    if "has_private_bathroom" in columns:
        op.drop_column("lodging_rooms", "has_private_bathroom")
