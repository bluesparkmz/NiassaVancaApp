"""add generic company gallery images

Revision ID: 20260507_0006
Revises: 20260423_0005
Create Date: 2026-05-07 10:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "20260507_0006"
down_revision: Union[str, Sequence[str], None] = "20260423_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("companies")}
    if "gallery_images" not in columns:
        op.add_column("companies", sa.Column("gallery_images", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("companies")}
    if "gallery_images" in columns:
        op.drop_column("companies", "gallery_images")
