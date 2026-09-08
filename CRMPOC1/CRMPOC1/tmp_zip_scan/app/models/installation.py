from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, Numeric, LargeBinary, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base
from app.models._mixins import TimestampMixin


class InstallationRequest(Base, TimestampMixin):
    __tablename__ = "installation_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_number: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_item_id: Mapped[int | None] = mapped_column(ForeignKey("order_items.id"), nullable=True)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    serial_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    serial_no_2: Mapped[str | None] = mapped_column(String(100), nullable=True)
    request_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    assigned_engineer: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Pending", nullable=False, index=True)
    installation_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    work_report: Mapped[str | None] = mapped_column(Text, nullable=True)
    work_report_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    settlement_approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    payment_amount_requested: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    payment_type_requested: Mapped[str | None] = mapped_column(String(20), nullable=True)
    payment_qr_code_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    payment_qr_code_blob: Mapped[bytes | None] = mapped_column(LargeBinary().with_variant(LargeBinary(length=(2**32) - 1), "mysql"), nullable=True)
    payment_qr_code_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_qr_code_content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payment_qr_code_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payment_proof_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    payment_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_amount_paid: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    payment_type_paid: Mapped[str | None] = mapped_column(String(20), nullable=True)
    payment_recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_recorded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    payment_transaction_id: Mapped[int | None] = mapped_column(ForeignKey("payment_transactions.id"), nullable=True)
