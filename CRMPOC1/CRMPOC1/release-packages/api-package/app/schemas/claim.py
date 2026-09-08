from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr

STATUSES = ("Processing", "Completed", "Rejected")


class ClaimCreate(BaseModel):
    order_no: str | None = None
    serial_number: str | None = None
    customer_name: str | None = None
    customer_contact: str | None = None
    customer_email: EmailStr | None = None
    notes: str | None = None  # issue description
    bank_name: str | None = None
    account_holder_name: str | None = None
    account_number: str | None = None
    ifsc_code: str | None = None


class ClaimUpdate(BaseModel):
    order_no: str | None = None
    serial_number: str | None = None
    customer_name: str | None = None
    customer_contact: str | None = None
    customer_email: EmailStr | None = None
    notes: str | None = None
    bank_name: str | None = None
    account_holder_name: str | None = None
    account_number: str | None = None
    ifsc_code: str | None = None


class ClaimStatusUpdate(BaseModel):
    status: Literal[STATUSES]  # type: ignore[valid-type]
    admin_remark: str | None = None


class ClaimOut(BaseModel):
    id: int
    claim_id: str
    order_no: str | None
    serial_number: str | None
    customer_name: str | None
    customer_contact: str | None
    customer_email: str | None
    status: str
    submitted_at: datetime
    processed_by: int | None
    processed_by_name: str | None = None
    notes: str | None
    bank_name: str | None
    account_holder_name: str | None
    account_number: str | None
    ifsc_code: str | None
    admin_remark: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ClaimListItem(BaseModel):
    id: int
    claim_id: str
    order_no: str | None
    serial_number: str | None
    customer_name: str | None
    customer_contact: str | None
    status: str
    submitted_at: datetime


class ClaimListResponse(BaseModel):
    items: list[ClaimListItem]
    total: int
    page: int
    per_page: int
