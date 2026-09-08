from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.order import Order, OrderItem
from app.models.service import ServiceRequest

COMPLETED_PAID_SERVICE_STATUSES = (
    "Service Completed",
    "Payment Requested",
    "Payment Completed",
    "Closed",
)


def _add_years(base_date: date | None, years: int | None) -> date | None:
    if base_date is None or years is None:
        return None
    try:
        return base_date.replace(year=base_date.year + years)
    except ValueError:
        return base_date.replace(month=2, day=28, year=base_date.year + years)


def resolve_order_item(db: Session, complaint: Complaint) -> OrderItem | None:
    if complaint.order_item_id:
        return db.get(OrderItem, complaint.order_item_id)
    serial = (complaint.serial_no or "").strip()
    if not serial:
        return None
    return db.scalar(
        select(OrderItem).where(
            or_(
                func.lower(OrderItem.serial_no) == func.lower(serial),
                func.lower(OrderItem.serial_no_2) == func.lower(serial),
            )
        )
    )


def derive_service_type_for_item(db: Session, item: OrderItem) -> str:
    order = db.get(Order, item.order_id) if item.order_id else None
    warranty_base = None
    if order is not None:
        warranty_base = order.actual_delivery_date or order.expected_delivery_date or order.order_date
    machine_warranty_date = _add_years(warranty_base, item.machine_warranty_years)
    today = date.today()
    in_warranty = machine_warranty_date is not None and today <= machine_warranty_date
    if item.free_service_count and item.service_consume_count < item.free_service_count:
        return "Free Service"
    if in_warranty:
        return "Warranty Service"
    return "Paid Service"


def serial_fields_for_item(
    db: Session,
    item: OrderItem | None,
    paid_service_count: int | None = None,
) -> dict[str, str | int | None]:
    if item is None:
        return {
            "warranty_status": None,
            "part_warranty_status": None,
            "free_service_count": None,
            "paid_service_count": None,
        }

    order = db.get(Order, item.order_id) if item.order_id else None
    warranty_base = None
    if order is not None:
        warranty_base = order.actual_delivery_date or order.expected_delivery_date or order.order_date

    machine_warranty_date = _add_years(warranty_base, item.machine_warranty_years)
    component_warranty_date = _add_years(warranty_base, item.component_warranty_years)
    today = date.today()

    warranty_status = None
    if machine_warranty_date is not None:
        warranty_status = "IN WARRANTY" if today <= machine_warranty_date else "OUT OF WARRANTY"

    part_warranty_status = None
    if component_warranty_date is not None:
        part_warranty_status = "IN WARRANTY" if today <= component_warranty_date else "OUT OF WARRANTY"

    if paid_service_count is None:
        paid_service_count = count_paid_services(db, item.id)

    return {
        "warranty_status": warranty_status,
        "part_warranty_status": part_warranty_status,
        "free_service_count": item.free_service_count,
        "paid_service_count": paid_service_count,
    }


def count_paid_services(db: Session, order_item_id: int) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(ServiceRequest)
            .where(
                ServiceRequest.order_item_id == order_item_id,
                ServiceRequest.deleted_at.is_(None),
                ServiceRequest.service_type == "Paid Service",
                ServiceRequest.status.in_(COMPLETED_PAID_SERVICE_STATUSES),
            )
        )
        or 0
    )


def batch_order_items_for_complaints(db: Session, complaints: list[Complaint]) -> dict[int, OrderItem]:
    if not complaints:
        return {}

    item_ids = {c.order_item_id for c in complaints if c.order_item_id}
    items_by_id: dict[int, OrderItem] = {}
    if item_ids:
        for row in db.scalars(select(OrderItem).where(OrderItem.id.in_(item_ids))).all():
            items_by_id[row.id] = row

    serial_complaints = [
        c for c in complaints if not c.order_item_id and (c.serial_no or "").strip()
    ]
    serial_items: dict[int, OrderItem] = {}
    for complaint in serial_complaints:
        item = resolve_order_item(db, complaint)
        if item is not None:
            serial_items[complaint.id] = item

    resolved: dict[int, OrderItem] = {}
    for complaint in complaints:
        if complaint.order_item_id and complaint.order_item_id in items_by_id:
            resolved[complaint.id] = items_by_id[complaint.order_item_id]
        elif complaint.id in serial_items:
            resolved[complaint.id] = serial_items[complaint.id]
    return resolved


def batch_paid_service_counts(db: Session, order_item_ids: list[int]) -> dict[int, int]:
    if not order_item_ids:
        return {}
    rows = db.execute(
        select(ServiceRequest.order_item_id, func.count())
        .where(
            ServiceRequest.order_item_id.in_(order_item_ids),
            ServiceRequest.deleted_at.is_(None),
            ServiceRequest.service_type == "Paid Service",
            ServiceRequest.status.in_(COMPLETED_PAID_SERVICE_STATUSES),
        )
        .group_by(ServiceRequest.order_item_id)
    ).all()
    return {row[0]: row[1] for row in rows}


def service_billing_label(service_type: str | None) -> str | None:
    if not service_type:
        return None
    return "Paid" if service_type == "Paid Service" else "Free"
