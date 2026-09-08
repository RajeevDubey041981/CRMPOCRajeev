from datetime import datetime

from pydantic import BaseModel, EmailStr


class CourierCreate(BaseModel):
    courier_name: str
    contact_name: str | None = None
    contact_mobile: str | None = None
    email: EmailStr | None = None
    address: str | None = None


class CourierUpdate(BaseModel):
    courier_name: str | None = None
    contact_name: str | None = None
    contact_mobile: str | None = None
    email: EmailStr | None = None
    address: str | None = None


class CourierOut(BaseModel):
    id: int
    courier_name: str
    contact_name: str | None
    contact_mobile: str | None
    email: str | None
    address: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CourierListItem(BaseModel):
    id: int
    courier_name: str
    contact_name: str | None
    contact_mobile: str | None
    email: str | None
    address: str | None
    created_at: datetime


class CourierListResponse(BaseModel):
    items: list[CourierListItem]
    total: int
    page: int
    per_page: int
