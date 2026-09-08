import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator


class ProjectCreate(BaseModel):
    title: str
    description: str | None = None
    status: str = "Draft"


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None


class ProjectOut(BaseModel):
    id: int
    title: str
    description: str | None
    status: str
    owner_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    task_name: str
    task_type: str
    sequence: int = 1
    advisor_id: str | None = None
    input_data: Any | None = None  # accepts dict or raw JSON string

    @field_validator("input_data", mode="before")
    @classmethod
    def coerce_input(cls, v):
        if isinstance(v, dict):
            return json.dumps(v)
        return v


class TaskUpdate(BaseModel):
    task_name: str | None = None
    sequence: int | None = None
    advisor_id: str | None = None
    input_data: Any | None = None

    @field_validator("input_data", mode="before")
    @classmethod
    def coerce_input(cls, v):
        if isinstance(v, dict):
            return json.dumps(v)
        return v


class TaskOut(BaseModel):
    id: int
    project_id: int
    task_name: str
    task_type: str
    sequence: int
    status: str
    advisor_id: str | None
    input_data: Any | None
    output_data: Any | None
    error_message: str | None
    started_at: str | None
    completed_at: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("input_data", "output_data", mode="before")
    @classmethod
    def parse_json(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return v
        return v


class ProjectDetail(ProjectOut):
    tasks: list[TaskOut] = []
    summary: dict = {}
