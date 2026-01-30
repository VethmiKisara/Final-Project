"""Initial schema migration
Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-01-30 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create tables (matches models.py initial schema)
    op.create_table(
        'data_streams',
        sa.Column('stream_id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('source_platform', sa.String(length=128), nullable=False),
        sa.Column('last_update_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_post_id', postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_table(
        'disasters',
        sa.Column('disaster_id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('disaster_type', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('date_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
    )

    op.create_table(
        'social_media_posts',
        sa.Column('post_id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('post_text', sa.Text(), nullable=True),
        sa.Column('post_image', sa.String(length=512), nullable=True),
        sa.Column('language', sa.String(length=8), nullable=True),
        sa.Column('platform', sa.String(length=64), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('disaster_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('data_stream_id', postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.create_table(
        'locations',
        sa.Column('location_id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('district', sa.String(length=128), nullable=True),
        sa.Column('province', sa.String(length=128), nullable=True),
    )

    op.create_table(
        'results',
        sa.Column('result_id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('accuracy', sa.Float(), nullable=False),
        sa.Column('disaster_label', sa.String(length=64), nullable=True),
        sa.Column('model_type', sa.String(length=128), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
    )

    op.create_table(
        'credibility',
        sa.Column('credibility_id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('source_verification_status', sa.Boolean(), nullable=False),
        sa.Column('assessed_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'users',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=128), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=64), nullable=False),
    )

    # Association tables
    op.create_table(
        'disaster_location',
        sa.Column('disaster_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint('disaster_id', 'location_id')
    )

    op.create_table(
        'user_result',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('result_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint('user_id', 'result_id')
    )

    # Foreign keys
    op.create_foreign_key(None, 'social_media_posts', 'disasters', ['disaster_id'], ['disaster_id'], ondelete='SET NULL')
    op.create_foreign_key(None, 'social_media_posts', 'data_streams', ['data_stream_id'], ['stream_id'], ondelete='SET NULL')
    op.create_foreign_key(None, 'results', 'social_media_posts', ['post_id'], ['post_id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'credibility', 'social_media_posts', ['post_id'], ['post_id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'disaster_location', 'disasters', ['disaster_id'], ['disaster_id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'disaster_location', 'locations', ['location_id'], ['location_id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'user_result', 'users', ['user_id'], ['user_id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'user_result', 'results', ['result_id'], ['result_id'], ondelete='CASCADE')

    # Indexes and constraints
    op.create_index('ix_social_posts_ts_platform', 'social_media_posts', ['timestamp', 'platform'])
    op.create_index('ix_disasters_date_time', 'disasters', ['date_time'])
    op.create_index('ix_results_post_confidence', 'results', ['post_id', 'confidence_score'])
    op.create_index('ix_cred_post', 'credibility', ['post_id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)


def downgrade():
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_cred_post', table_name='credibility')
    op.drop_index('ix_results_post_confidence', table_name='results')
    op.drop_index('ix_disasters_date_time', table_name='disasters')
    op.drop_index('ix_social_posts_ts_platform', table_name='social_media_posts')

    op.drop_constraint(None, 'user_result', type_='foreignkey')
    op.drop_constraint(None, 'disaster_location', type_='foreignkey')
    op.drop_constraint(None, 'credibility', type_='foreignkey')
    op.drop_constraint(None, 'results', type_='foreignkey')
    op.drop_constraint(None, 'social_media_posts', type_='foreignkey')

    op.drop_table('user_result')
    op.drop_table('disaster_location')
    op.drop_table('users')
    op.drop_table('credibility')
    op.drop_table('results')
    op.drop_table('locations')
    op.drop_table('social_media_posts')
    op.drop_table('disasters')
    op.drop_table('data_streams')
