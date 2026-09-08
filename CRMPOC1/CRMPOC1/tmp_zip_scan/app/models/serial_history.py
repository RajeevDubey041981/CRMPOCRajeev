from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class SerialHistoryEvent(Base):
    __tablename__ = "serial_history_events"
    __table_args__ = (
        UniqueConstraint(
            "source_table",
            "source_id",
            "event_type",
            "serial_no",
            name="uq_serial_history_source_event",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_item_id: Mapped[int | None] = mapped_column(ForeignKey("order_items.id"), nullable=True, index=True)
    serial_no: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    serial_no_2: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_subtype: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    performed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    performed_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_table: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
