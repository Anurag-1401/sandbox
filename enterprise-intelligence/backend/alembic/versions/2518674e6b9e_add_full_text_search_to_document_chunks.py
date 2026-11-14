from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR


from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = '2518674e6b9e'
down_revision: Union[str, Sequence[str], None] = 'f0ecb5d8fb17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    op.add_column(
        "document_chunks",
        sa.Column(
            "search_vector",
            TSVECTOR(),
            sa.Computed(
                "to_tsvector('simple', coalesce(content, ''))",
                persisted=True,
            ),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_document_chunks_search_vector",
        "document_chunks",
        ["search_vector"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_chunks_search_vector",
        table_name="document_chunks",
    )

    op.drop_column(
        "document_chunks",
        "search_vector",
    )