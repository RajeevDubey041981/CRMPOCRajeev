from datetime import datetime
from pydantic import BaseModel, Field


class InstallationCreate(BaseModel):
    customer_name: str
    contact_number: str
    address: str | None = None
    order_item_id: int | None = None
    product_name: str | None = None
    request_date: datetime | None = None


class InstallationStatusUpdate(BaseModel):
    customer_name: str | None = None
    contact_number: str | None = None
    address: str | None = None
    product_name: str | None = None
    installation_date: datetime | None = None
    work_report: str | None = None
    status: str | None = None


class InstallationBulkUpdateRequest(BaseModel):
    installation_ids: list[int]
    new_status: str
    installation_date: datetime | None = None
    work_report: str | None = None
    payment_amount: float | None = None
    payment_type: str | None = None


class InstallationListItem(BaseModel):
    id: int
    order_item_id: int | None = None
    item_code: str | None = None
    customer_name: str
    contact_number: str
    product_name: str | None
    order_no: str | None = None
    vendor_name: str | None = None
    serial_no: str | None = None
    serial_no_2: str | None = None
    status: str
    request_date: datetime
    installation_date: datetime | None
    assigned_engineer_name: str | None
    settlement_approved_by_name: str | None
    payment_amount_requested: float | None = None
    payment_type_requested: str | None = None
    payment_qr_code_path: str | None = None
    payment_qr_code_filename: str | None = None
    payment_proof_file_path: str | None = None


class InstallationListResponse(BaseModel):
    items: list[InstallationListItem]
    total: int
    page: int
    per_page: int


class InstallationPaymentHistoryItem(BaseModel):
    id: int
    order_no: str | None = None
    item_code: str | None = None
    customer_name: str
    assigned_engineer_name: str | None = None
    payment_amount_requested: float | None = None
    payment_amount_paid: float | None = None
    payment_type_requested: str | None = None
    payment_type_paid: str | None = None
    payment_recorded_at: datetime | None = None
    payment_recorded_by_name: str | None = None
    installation_date: datetime | None = None
    status: str


class InstallationPaymentHistoryRequestItem(BaseModel):
    id: int
    source_type: str = "installation"
    order_no: str | None = None
    item_code: str | None = None
    customer_name: str
    installation_date: datetime | None = None
    requested_amount: float | None = None
    paid_amount: float | None = None
    status: str


class InstallationPaymentHistoryGroupItem(BaseModel):
    id: int
    payment_type: str
    total_amount: float
    request_count: int
    recorded_at: datetime
    recorded_by_name: str | None = None
    engineer_name: str | None = None
    requests: list[InstallationPaymentHistoryRequestItem]


class InstallationPaymentHistoryResponse(BaseModel):
    items: list[InstallationPaymentHistoryGroupItem]
    total: int
    page: int
    per_page: int


class InstallationEngineerAssignmentOption(BaseModel):
    id: int
    name: str
    email: str
    pending_requests: int = 0
    rating: float = 0.0
    completed_requests: int = 0


class InstallationOut(BaseModel):
    id: int
    customer_name: str
    contact_number: str
    address: str | None
    order_item_id: int | None
    product_name: str | None
    order_no: str | None = None
    vendor_name: str | None = None
    serial_no: str | None = None
    serial_no_2: str | None = None
    request_date: datetime
    assigned_engineer: int | None
    assigned_engineer_name: str | None
    status: str
    installation_date: datetime | None
    work_report: str | None
    work_report_file_path: str | None
    settlement_approved_by: int | None
    settlement_approved_by_name: str | None
    payment_amount_requested: float | None = None
    payment_type_requested: str | None = None
    payment_qr_code_path: str | None = None
    payment_qr_code_filename: str | None = None
    payment_proof_file_path: str | None = None
    payment_requested_at: datetime | None = None
    payment_amount_paid: float | None = None
    payment_type_paid: str | None = None
    payment_recorded_at: datetime | None = None
    payment_recorded_by: int | None = None
    payment_recorded_by_name: str | None = None
    created_at: datetime
    updated_at: datetime


class InstallationAssignPair(BaseModel):
    installation_id: int | None = None
    order_item_id: int | None = None
    engineer_id: int


class BulkAssignRequest(BaseModel):
    assignments: list[InstallationAssignPair]


class BulkCancelRequest(BaseModel):
    installation_ids: list[int]
