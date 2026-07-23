"""initial migration

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, index=True, nullable=False),
        sa.Column('username', sa.String(100), unique=True, index=True, nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='recruiter'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('designation', sa.String(255), nullable=True),
        sa.Column('reset_token', sa.String(255), nullable=True),
        sa.Column('reset_token_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('requirements', sa.Text(), nullable=True),
        sa.Column('responsibilities', sa.Text(), nullable=True),
        sa.Column('required_skills', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('preferred_skills', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('experience_min', sa.Integer(), nullable=True),
        sa.Column('experience_max', sa.Integer(), nullable=True),
        sa.Column('education_level', sa.String(100), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('job_type', sa.String(50), nullable=True),
        sa.Column('salary_min', sa.Integer(), nullable=True),
        sa.Column('salary_max', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'candidates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('email', sa.String(255), nullable=True, index=True),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('linkedin_url', sa.String(500), nullable=True),
        sa.Column('github_url', sa.String(500), nullable=True),
        sa.Column('portfolio_url', sa.String(500), nullable=True),
        sa.Column('total_experience_years', sa.Float(), nullable=True),
        sa.Column('rank', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('status', sa.String(20), nullable=False, server_default='uploaded'),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('ai_strengths', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('ai_weaknesses', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('ai_career_highlights', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('hiring_recommendation', sa.String(50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('jobs.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'resumes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('original_filename', sa.String(500), nullable=False),
        sa.Column('file_path', sa.String(1000), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='uploaded'),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('parsed_data', postgresql.JSONB(), nullable=True),
        sa.Column('parsing_error', sa.Text(), nullable=True),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidates.id'), unique=True, nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), unique=True, index=True, nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'candidate_skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidates.id'), nullable=False),
        sa.Column('skill_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('skills.id'), nullable=False),
        sa.Column('proficiency', sa.String(50), nullable=True),
        sa.Column('years_experience', sa.Float(), nullable=True),
        sa.Column('is_match', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'education',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidates.id'), nullable=False),
        sa.Column('institution', sa.String(500), nullable=False),
        sa.Column('degree', sa.String(255), nullable=True),
        sa.Column('field_of_study', sa.String(255), nullable=True),
        sa.Column('start_year', sa.Integer(), nullable=True),
        sa.Column('end_year', sa.Integer(), nullable=True),
        sa.Column('gpa', sa.String(20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'experience',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidates.id'), nullable=False),
        sa.Column('company', sa.String(500), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('start_date', sa.String(50), nullable=True),
        sa.Column('end_date', sa.String(50), nullable=True),
        sa.Column('is_current', sa.String(10), server_default='false', nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('achievements', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidates.id'), nullable=False),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('technologies', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('url', sa.String(500), nullable=True),
        sa.Column('github_url', sa.String(500), nullable=True),
        sa.Column('start_date', sa.String(50), nullable=True),
        sa.Column('end_date', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'certifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidates.id'), nullable=False),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('issuer', sa.String(255), nullable=True),
        sa.Column('date_obtained', sa.String(50), nullable=True),
        sa.Column('expiry_date', sa.String(50), nullable=True),
        sa.Column('credential_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'interview_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidates.id'), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('difficulty', sa.String(20), nullable=False),
        sa.Column('expected_answer', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'ats_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidates.id'), unique=True, nullable=False),
        sa.Column('total_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('skills_score', sa.Float(), server_default='0'),
        sa.Column('experience_score', sa.Float(), server_default='0'),
        sa.Column('education_score', sa.Float(), server_default='0'),
        sa.Column('projects_score', sa.Float(), server_default='0'),
        sa.Column('formatting_score', sa.Float(), server_default='0'),
        sa.Column('certifications_score', sa.Float(), server_default='0'),
        sa.Column('keywords_match', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('missing_keywords', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('matched_skills', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('missing_skills', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('recommended_skills', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('learning_roadmap', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'ai_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('candidates.id'), unique=True, nullable=False),
        sa.Column('match_score', sa.Float(), server_default='0'),
        sa.Column('jd_match_score', sa.Float(), server_default='0'),
        sa.Column('skills_match', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('experience_match', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('education_match', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('projects_match', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('certifications_match', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('strengths', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('weaknesses', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('career_highlights', postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('hiring_recommendation', sa.String(50), nullable=True),
        sa.Column('recommendation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'activity_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('report_type', sa.String(50), nullable=False),
        sa.Column('format', sa.String(10), nullable=False),
        sa.Column('file_path', sa.String(1000), nullable=True),
        sa.Column('file_size', sa.String(50), nullable=True),
        sa.Column('generated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('parameters', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('reports')
    op.drop_table('activity_logs')
    op.drop_table('ai_analysis')
    op.drop_table('ats_results')
    op.drop_table('interview_questions')
    op.drop_table('certifications')
    op.drop_table('projects')
    op.drop_table('experience')
    op.drop_table('education')
    op.drop_table('candidate_skills')
    op.drop_table('skills')
    op.drop_table('resumes')
    op.drop_table('candidates')
    op.drop_table('jobs')
    op.drop_table('users')
