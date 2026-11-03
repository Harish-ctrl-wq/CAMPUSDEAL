"""Create the products table.

Revision ID: 0001_create_products
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_create_products"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("age", sa.Float(), nullable=True),
        sa.Column("condition", sa.String(length=24), nullable=True),
        sa.Column("original_price", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("source_id", sa.String(length=80), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", name="uq_products_source_id"),
    )
    op.create_index("ix_products_id", "products", ["id"], unique=False)
    op.create_index("ix_products_title", "products", ["title"], unique=False)
    op.create_index("ix_products_category", "products", ["category"], unique=False)


def downgrade() -> None:
    raise RuntimeError(
        "This baseline migration is intentionally forward-only to protect listing data."
    )
