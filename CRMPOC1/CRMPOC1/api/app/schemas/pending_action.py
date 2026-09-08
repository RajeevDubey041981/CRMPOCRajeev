from datetime import datetime

from pydantic import BaseModel


class PendingActionOut(BaseModel):
    id: int
    module: str
    entity_id: int
    title: str
    message: str
    action_label: str
    href: str
    entity_status: str
    occurred_at: datetime
    is_read: bool

    model_config = {"from_attributes": True}


class PendingActionsResponse(BaseModel):
    total: int
    items: list[PendingActionOut]


class MarkPendingActionsReadIn(BaseModel):
    ids: list[int] | None = None
