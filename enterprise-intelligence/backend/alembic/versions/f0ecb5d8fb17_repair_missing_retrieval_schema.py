"""Preserve historical retrieval schema revision.

The retrieval schema is already created by 0cc8791f14b7.
This revision is retained because later migrations depend on it.
"""

revision = "f0ecb5d8fb17"
down_revision = "0cc8791f14b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Intentionally empty.
    # The parent migration already creates the retrieval schema.
    pass


def downgrade() -> None:
    # Intentionally empty.
    pass