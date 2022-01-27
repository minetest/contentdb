"""empty message

Revision ID: 3710e5fbbe87
Revises: f6ef5f35abca
Create Date: 2022-01-27 18:50:11.705061

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3710e5fbbe87'
down_revision = 'f6ef5f35abca'
branch_labels = None
depends_on = None


def upgrade():
    command = """
            CREATE OR REPLACE FUNCTION parse_websearch(config regconfig, search_query text)
            RETURNS tsquery AS $$
            SELECT
                string_agg(
                    (
                        CASE
                            WHEN position('''' IN words.word) > 0 THEN CONCAT(words.word, ':*')
                            ELSE words.word
                        END
                    ),
                    ' '
                )::tsquery
            FROM (
                SELECT trim(
                    regexp_split_to_table(
                        websearch_to_tsquery(config, lower(search_query))::text,
                        ' '
                    )
                ) AS word
            ) AS words
            $$ LANGUAGE SQL IMMUTABLE;
            
            
            CREATE OR REPLACE FUNCTION parse_websearch(search_query text)
            RETURNS tsquery AS $$
            SELECT parse_websearch('pg_catalog.simple', search_query);
            $$ LANGUAGE SQL IMMUTABLE;"""

    op.execute(command)


def downgrade():
    op.execute('DROP FUNCTION public.parse_websearch(regconfig, text);')
    op.execute('DROP FUNCTION public.parse_websearch(text);')
