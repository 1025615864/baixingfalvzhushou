"""add full-text search

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('posts', sa.Column('search_vector', sa.Text(), nullable=True))

    op.execute("""
        CREATE INDEX idx_posts_search ON posts
        USING gin(to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(content, '')))
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION update_post_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector := to_tsvector('simple', coalesce(NEW.title, '') || ' ' || coalesce(NEW.content, ''));
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_update_post_search_vector
        BEFORE INSERT OR UPDATE ON posts
        FOR EACH ROW
        EXECUTE FUNCTION update_post_search_vector();
    """)

    op.execute("""
        UPDATE posts SET search_vector = to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(content, ''))
        WHERE search_vector IS NULL;
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_update_post_search_vector ON posts")
    op.execute("DROP FUNCTION IF EXISTS update_post_search_vector()")
    op.drop_index('idx_posts_search', table_name='posts')
    op.drop_column('posts', 'search_vector')
