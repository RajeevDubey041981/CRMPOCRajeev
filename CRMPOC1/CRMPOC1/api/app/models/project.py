from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models._mixins import TimestampMixin

TASK_TYPES = [
    "Add Advisor",
    "Fetch Advisor List",
    "Send Rubric Request",
    "Rubric Validation",
    "Send Survey",
    "Gather Responses",
]

PROJECT_STATUSES = ["Draft", "Active", "Completed", "Cancelled"]
TASK_STATUSES = ["Pending", "Running", "Completed", "Failed", "Skipped"]


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="Draft", nullable=False, index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class WorkflowTask(Base, TimestampMixin):
    __tablename__ = "workflow_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="Pending", nullable=False)
    advisor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    input_data: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON string
    output_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)
