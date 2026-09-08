"""Add projects and workflow_tasks tables

Revision ID: 0004_projects_workflow
Revises: 0003_enhance_calls
Create Date: 2026-05-27 12:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = '0004_projects_workflow'
down_revision = '0003_enhance_calls'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(30), server_default='Draft', nullable=False),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_projects_status', 'projects', ['status'])

    op.create_table(
        'workflow_tasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('task_name', sa.String(255), nullable=False),
        sa.Column('task_type', sa.String(50), nullable=False),
        sa.Column('sequence', sa.Integer(), server_default='1', nullable=False),
        sa.Column('status', sa.String(20), server_default='Pending', nullable=False),
        sa.Column('advisor_id', sa.String(100), nullable=True),
        sa.Column('input_data', sa.Text(), nullable=True),
        sa.Column('output_data', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.String(50), nullable=True),
        sa.Column('completed_at', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_workflow_tasks_project_id', 'workflow_tasks', ['project_id'])


def downgrade() -> None:
    op.drop_table('workflow_tasks')
    op.drop_table('projects')
