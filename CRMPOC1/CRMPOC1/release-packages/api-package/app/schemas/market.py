from datetime import datetime

from pydantic import BaseModel, EmailStr

MARKET_USER_ROLES = ("Retailer", "Distributor", "Sales", "Admin")
MARKET_USER_STATUSES = ("Active", "Pending")
MARKET_FEE_STATUSES = ("Paid", "Pending")
MARKET_ITEM_STATUSES = ("Active", "Inactive")
MARKET_ORDER_STATUSES = ("Pending", "Processing", "Delivered", "Cancelled")


# ---------------------------------------------------------------------------
# MarketCategory
# ---------------------------------------------------------------------------

class MarketCategoryCreate(BaseModel):
    name: str
    parent_id: int | None = None


class MarketCategoryUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None


class MarketCategoryOut(BaseModel):
    id: int
    name: str
    parent_id: int | None
    parent_name: str | None = None
    item_count: int = 0
    child_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# MarketItem
# ---------------------------------------------------------------------------

class MarketItemCreate(BaseModel):
    sku: str
    name: str
    company: str | None = None
    category_id: int | None = None
    base_price: float | None = None
    mrp: float | None = None
    status: str = "Active"
    stock_count: int = 0
    description: str | None = None


class MarketItemUpdate(BaseModel):
    name: str | None = None
    company: str | None = None
    category_id: int | None = None
    base_price: float | None = None
    mrp: float | None = None
    status: str | None = None
    stock_count: int | None = None
    description: str | None = None


class MarketItemOut(BaseModel):
    id: int
    sku: str
    name: str
    company: str | None
    category_id: int | None
    category_name: str | None = None
    base_price: float | None
    mrp: float | None
    status: str
    stock_count: int
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# MarketUser
# ---------------------------------------------------------------------------

class MarketUserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    role: str = "Retailer"
    status: str = "Pending"
    fee_status: str = "Pending"
    onboarding_fee: float | None = None


class MarketUserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    role: str | None = None
    status: str | None = None
    fee_status: str | None = None
    onboarding_fee: float | None = None


class MarketUserOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None
    address: str | None
    city: str | None
    state: str | None
    role: str
    status: str
    fee_status: str
    onboarding_fee: float | None
    joined_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class MarketUserLookup(BaseModel):
    id: int
    name: str
    role: str


# ---------------------------------------------------------------------------
# MarketOrder
# ---------------------------------------------------------------------------

class MarketOrderItemIn(BaseModel):
    item_id: int | None = None
    qty: int = 1
    unit_price: float | None = None


class MarketOrderCreate(BaseModel):
    retailer_id: int | None = None
    distributor_id: int | None = None
    status: str = "Pending"
    notes: str | None = None
    items: list[MarketOrderItemIn] = []


class MarketOrderUpdate(BaseModel):
    retailer_id: int | None = None
    distributor_id: int | None = None
    status: str | None = None
    notes: str | None = None


class MarketOrderItemOut(BaseModel):
    id: int
    item_id: int | None
    item_name: str | None = None
    qty: int
    unit_price: float | None
    subtotal: float | None


class MarketOrderOut(BaseModel):
    id: int
    order_no: str
    retailer_id: int | None
    retailer_name: str | None = None
    distributor_id: int | None
    distributor_name: str | None = None
    total_amount: float | None
    status: str
    notes: str | None
    created_at: datetime
    items: list[MarketOrderItemOut] = []

    class Config:
        from_attributes = True


class MarketOrderListItem(BaseModel):
    id: int
    order_no: str
    retailer_name: str | None = None
    distributor_name: str | None = None
    total_amount: float | None
    status: str
    created_at: datetime


class MarketOrderListResponse(BaseModel):
    items: list[MarketOrderListItem]
    total: int
    page: int
    per_page: int


# ---------------------------------------------------------------------------
# Generic list wrappers
# ---------------------------------------------------------------------------

class MarketUserListResponse(BaseModel):
    items: list[MarketUserOut]
    total: int
    page: int
    per_page: int


class MarketItemListResponse(BaseModel):
    items: list[MarketItemOut]
    total: int
    page: int
    per_page: int


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class MarketDashboard(BaseModel):
    total_users: int
    active_users: int
    pending_users: int
    total_items: int
    active_items: int
    low_stock_items: int
    total_orders: int
    pending_orders: int
    delivered_orders: int
    total_sales: float
    total_categories: int
