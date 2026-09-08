import csv
import io
from datetime import date, datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import case, desc, func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.deps import get_current_user
from app.models.claim import Claim
from app.models.complaint import Complaint
from app.models.courier import Courier
from app.models.item_master import ItemMaster
from app.models.order import Order, OrderItem
from app.models.serial_history import SerialHistoryEvent
from app.models.vendor import Vendor
from app.models.user import User
from app.schemas.order import (
    ORDER_STATUSES,
    OrderAutocompleteSuggestion,
    OrderCreate,
    OrderItemCreate,
    OrderItemQuantitySummary,
    OrderItemOut,
    OrderItemUpdate,
    OrderListItem,
    OrderListResponse,
    OrderOut,
    OrderUpdate,
)
from app.services.file_service import save_upload
from app.services.permissions import can_act_on
from app.services.serial_history import EVENT_TYPES, create_serial_history_event

router = APIRouter(prefix="/api/orders", tags=["orders"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_vendor_name(db: Session, vendor_id: int | None) -> str | None:
    if vendor_id is None:
        return None
    v = db.get(Vendor, vendor_id)
    return v.name_of_firm if v else None


def _vendor_for_user(db: Session, user: User) -> Vendor | None:
    if user.role != "vendor":
        return None
    return db.scalar(select(Vendor).where(Vendor.email == user.email))


def _apply_order_visibility(stmt, user: User, vendor: Vendor | None):
    if user.role == "vendor":
        if vendor is None:
            return stmt.where(Order.id == -1)
        return stmt.where(Order.vendor_id == vendor.id)
    return stmt


def _trimmed_query(value: str | None) -> str:
    return (value or "").strip()


def _apply_order_search_filter(stmt, search: str | None):
    query = _trimmed_query(search)
    if not query:
        return stmt
    like = f"%{query}%"
    return stmt.where(
        or_(
            Order.customer_contact.ilike(like),
            Order.order_no.ilike(like),
            Order.oem_bill_no.ilike(like),
            Order.customer_name.ilike(like),
            Vendor.vendor_code.ilike(like),
            Vendor.name_of_firm.ilike(like),
        )
    )


def _autocomplete_rank_expressions(query: str):
    q = query.lower()
    prefix = f"{q}%"
    contains = f"%{q}%"
    return [
        (
            "order_no",
            case(
                (func.lower(func.coalesce(Order.order_no, "")) == q, 0),
                (func.lower(func.coalesce(Order.order_no, "")).like(prefix), 1),
                (func.lower(func.coalesce(Order.order_no, "")).like(contains), 2),
                else_=100,
            ),
        ),
        (
            "oem_bill_no",
            case(
                (func.lower(func.coalesce(Order.oem_bill_no, "")) == q, 3),
                (func.lower(func.coalesce(Order.oem_bill_no, "")).like(prefix), 4),
                (func.lower(func.coalesce(Order.oem_bill_no, "")).like(contains), 5),
                else_=100,
            ),
        ),
        (
            "customer_contact",
            case(
                (func.lower(func.coalesce(Order.customer_contact, "")) == q, 6),
                (func.lower(func.coalesce(Order.customer_contact, "")).like(prefix), 7),
                (func.lower(func.coalesce(Order.customer_contact, "")).like(contains), 8),
                else_=100,
            ),
        ),
        (
            "vendor_code",
            case(
                (func.lower(func.coalesce(Vendor.vendor_code, "")) == q, 9),
                (func.lower(func.coalesce(Vendor.vendor_code, "")).like(prefix), 10),
                (func.lower(func.coalesce(Vendor.vendor_code, "")).like(contains), 11),
                else_=100,
            ),
        ),
        (
            "customer_name",
            case(
                (func.lower(func.coalesce(Order.customer_name, "")) == q, 12),
                (func.lower(func.coalesce(Order.customer_name, "")).like(prefix), 13),
                (func.lower(func.coalesce(Order.customer_name, "")).like(contains), 14),
                else_=100,
            ),
        ),
        (
            "vendor_name",
            case(
                (func.lower(func.coalesce(Vendor.name_of_firm, "")) == q, 15),
                (func.lower(func.coalesce(Vendor.name_of_firm, "")).like(prefix), 16),
                (func.lower(func.coalesce(Vendor.name_of_firm, "")).like(contains), 17),
                else_=100,
            ),
        ),
    ]


def _display_order_suggestion(row) -> str:
    bits = []
    if row.order_no:
        bits.append(f"Order: {row.order_no}")
    if row.oem_bill_no:
        bits.append(f"OEM: {row.oem_bill_no}")
    vendor_bits = " / ".join([part for part in [row.vendor_name, row.vendor_code] if part])
    if vendor_bits:
        bits.append(f"Vendor: {vendor_bits}")
    if row.customer_name:
        bits.append(f"Customer: {row.customer_name}")
    if row.customer_contact:
        bits.append(f"Mobile: {row.customer_contact}")
    return " | ".join(bits) if bits else f"Order #{row.order_id}"


def _resolve_courier_name(db: Session, courier_id: int | None) -> str | None:
    if courier_id is None:
        return None
    c = db.get(Courier, courier_id)
    return c.courier_name if c and c.deleted_at is None else None


def _ensure_active_courier(db: Session, courier_id: int | None) -> int | None:
    if courier_id is None:
        return None
    courier = db.get(Courier, courier_id)
    if courier is None or courier.deleted_at is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Selected courier is not active.")
    return courier_id


def _is_admin_or_incool(user: User) -> bool:
    return (user.role or "").lower() in {"admin", "incool"}


def _resolve_item_name(db: Session, item_id: int | None) -> str | None:
    if item_id is None:
        return None
    i = db.get(ItemMaster, item_id)
    return i.item_name if i else None


def _resolve_item_code(db: Session, item_id: int | None, fallback: str | None = None) -> str | None:
    if fallback:
        return fallback
    if item_id is None:
        return None
    i = db.get(ItemMaster, item_id)
    return i.item_code if i else None


def _hydrate_items(db: Session, order: Order) -> list[OrderItemOut]:
    rows = db.scalars(
        select(OrderItem)
        .where(OrderItem.order_id == order.id)
        .order_by(
            func.coalesce(OrderItem.item_code, ""),
            func.coalesce(OrderItem.id, 0),
        )
    ).all()
    out = []
    for row in rows:
        out.append(OrderItemOut(
            id=row.id,
            item_id=row.item_id,
            item_code=_resolve_item_code(db, row.item_id, row.item_code),
            item_name=_resolve_item_name(db, row.item_id),
            serial_no=row.serial_no,
            serial_no_2=row.serial_no_2,
            item_qty=row.item_qty,
            pcb_warranty_years=row.pcb_warranty_years,
            component_warranty_years=row.component_warranty_years,
            machine_warranty_years=row.machine_warranty_years,
            free_service_count=row.free_service_count,
            service_consume_count=row.service_consume_count,
            installation_status=row.installation_status,
        ))
    return out


def _hydrate_order(db: Session, order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        order_no=order.order_no,
        order_date=order.order_date,
        oem_bill_no=order.oem_bill_no,
        vendor_id=order.vendor_id,
        vendor_name=_resolve_vendor_name(db, order.vendor_id),
        customer_name=order.customer_name,
        customer_contact=order.customer_contact,
        customer_email=order.customer_email,
        customer_city=order.customer_city,
        customer_state=order.customer_state,
        customer_address=order.customer_address,
        courier_id=order.courier_id,
        courier_name=_resolve_courier_name(db, order.courier_id),
        lrn_no=order.lrn_no,
        vendor_bill_no=order.vendor_bill_no,
        vendor_bill_date=order.vendor_bill_date,
        status=order.status,
        expected_delivery_date=order.expected_delivery_date,
        actual_delivery_date=order.actual_delivery_date,
        order_file_path=order.order_file_path,
        created_by=order.created_by,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=_hydrate_items(db, order),
    )


def _load_order(db: Session, user: User, order_id: int) -> Order:
    """Load an active order by id, check can_view; raise 404 on any failure."""
    order = db.get(Order, order_id)
    if order is None or order.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    if not can_act_on(db, user, "orders", "can_view", None):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    # If user is a vendor, ensure they can only load their own orders.
    if user.role == "vendor":
        v = db.scalar(select(Vendor).where(Vendor.email == user.email))
        if v is None or order.vendor_id != v.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order


def _can_submit_serials(db: Session, user: User, order: Order) -> bool:
    """Vendors may resubmit serials only for their own orders.

    This keeps the generic order edit permission unchanged while allowing the
    cancel/send-back workflow to return control to the vendor.
    """
    if can_act_on(db, user, "orders", "can_edit", None):
        return True
    if user.role != "vendor":
        return False
    v = db.scalar(select(Vendor).where(Vendor.email == user.email))
    return v is not None and order.vendor_id == v.id


def _order_ready_for_installation_submission(order: Order) -> bool:
    return order.status == "Delivered" and bool((order.oem_bill_no or "").strip())


ORDER_ITEM_IMPORT_EXPORT_COLUMNS = [
    "ID",
    "Item ID",
    "Item Name",
    "Item Code",
    "Serial Number 1",
    "Serial Number 2",
    "PCB Warranty",
    "Component Warranty",
    "Machine Warranty",
    "Free Services",
    "Installation Status",
]


def _can_manage_order_item_csv(user: User) -> bool:
    return (user.role or "").lower() in {"admin", "incool"}


def _serialize_order_item_csv_row(db: Session, item: OrderItem) -> list[str | int]:
    return [
        item.id,
        item.item_id or "",
        _resolve_item_name(db, item.item_id) or "",
        _resolve_item_code(db, item.item_id, item.item_code) or "",
        item.serial_no or "",
        item.serial_no_2 or "",
        item.pcb_warranty_years if item.pcb_warranty_years is not None else "",
        item.component_warranty_years if item.component_warranty_years is not None else "",
        item.machine_warranty_years if item.machine_warranty_years is not None else "",
        item.free_service_count,
        item.installation_status or "",
    ]


def _load_order_items_for_csv(db: Session, order_id: int, item_code: str | None = None) -> list[OrderItem]:
    stmt = select(OrderItem).where(OrderItem.order_id == order_id)
    if item_code:
        stmt = stmt.where(func.coalesce(OrderItem.item_code, "") == item_code)
    stmt = stmt.order_by(
        func.coalesce(OrderItem.item_code, ""),
        func.coalesce(OrderItem.id, 0),
    )
    return db.scalars(stmt).all()


def _normalize_serial(value: str | None) -> str:
    return (value or "").strip().lower()


def _find_global_serial_conflicts(
    db: Session,
    serials: set[str],
    *,
    exclude_item_ids: set[int] | None = None,
) -> dict[str, int]:
    normalized_serials = {serial for serial in serials if serial}
    if not normalized_serials:
        return {}

    stmt = select(OrderItem.id, OrderItem.serial_no, OrderItem.serial_no_2)
    if exclude_item_ids:
        stmt = stmt.where(~OrderItem.id.in_(exclude_item_ids))

    conflicts: dict[str, int] = {}
    for item_id, serial_1, serial_2 in db.execute(stmt).all():
        for serial_value in (serial_1, serial_2):
            normalized = _normalize_serial(serial_value)
            if normalized and normalized in normalized_serials and normalized not in conflicts:
                conflicts[normalized] = item_id
    return conflicts


def _validate_order_item_serials(
    db: Session,
    items: list[OrderItemCreate | OrderItemUpdate],
    *,
    exclude_item_ids: set[int] | None = None,
) -> None:
    serial_owners: dict[str, int] = {}

    for idx, item in enumerate(items, start=1):
        item_id = getattr(item, "id", None)
        row_serials: list[tuple[str, str, str]] = []
        for label, serial_value in (("Serial Number 1", item.serial_no), ("Serial Number 2", item.serial_no_2)):
            trimmed = (serial_value or "").strip()
            normalized = _normalize_serial(trimmed)
            if not normalized:
                continue
            row_serials.append((label, trimmed, normalized))

        if len({normalized for _, _, normalized in row_serials}) != len(row_serials):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Row {idx}: Serial Number 1 and Serial Number 2 cannot be the same",
            )

        for _label, display_value, normalized in row_serials:
            owner = serial_owners.get(normalized)
            if owner is not None and owner != (item_id or -idx):
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"Row {idx}: duplicate serial '{display_value}' already exists in this order payload",
                )
            serial_owners[normalized] = item_id or -idx

    global_conflicts = _find_global_serial_conflicts(
        db,
        set(serial_owners.keys()),
        exclude_item_ids=exclude_item_ids,
    )
    if global_conflicts:
        for idx, item in enumerate(items, start=1):
            for serial_value in (item.serial_no, item.serial_no_2):
                trimmed = (serial_value or "").strip()
                normalized = _normalize_serial(trimmed)
                if normalized and normalized in global_conflicts:
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST,
                        f"Row {idx}: duplicate serial '{trimmed}' already exists in another order",
                    )


# ---------------------------------------------------------------------------
# IMPORTANT: fixed-path routes must come BEFORE /{order_id}
# ---------------------------------------------------------------------------

@router.get("/lookup/vendors")
def lookup_vendors(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    rows = db.scalars(
        select(Vendor)
        .where(Vendor.deleted_at.is_(None), Vendor.is_active == True)
        .order_by(Vendor.name_of_firm)
    ).all()
    return [
        {
            "id": v.id,
            "name": v.name_of_firm,
            "email": v.email,
            "vendor_code": v.vendor_code,
            "gst_no": v.gst_no,
            "name_of_firm": v.name_of_firm,
            "state": v.state,
        }
        for v in rows
    ]


@router.get("/lookup/couriers")
def lookup_couriers(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    rows = db.scalars(
        select(Courier)
        .where(Courier.deleted_at.is_(None))
        .order_by(Courier.courier_name)
    ).all()
    return [{"id": c.id, "name": c.courier_name} for c in rows]


@router.get("/lookup/items")
def lookup_items(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    rows = db.scalars(
        select(ItemMaster)
        .where(ItemMaster.deleted_at.is_(None))
        .order_by(ItemMaster.item_name)
    ).all()
    return [{"id": i.id, "item_code": i.item_code, "item_name": i.item_name} for i in rows]


@router.get("/search/autocomplete", response_model=list[OrderAutocompleteSuggestion])
def autocomplete_orders(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not can_act_on(db, user, "orders", "can_view", None):
        return []

    query = _trimmed_query(q)
    if len(query) < 2:
        return []

    vendor = _vendor_for_user(db, user)
    rank_expressions = _autocomplete_rank_expressions(query)
    stmt = (
        select(
            Order.id.label("order_id"),
            Order.order_no,
            Order.oem_bill_no,
            Order.vendor_id,
            Vendor.vendor_code,
            Vendor.name_of_firm.label("vendor_name"),
            Order.customer_name,
            Order.customer_contact,
            *[expr.label(f"{field}_rank") for field, expr in rank_expressions],
        )
        .select_from(Order)
        .join(Vendor, Order.vendor_id == Vendor.id, isouter=True)
        .where(Order.deleted_at.is_(None))
    )
    stmt = _apply_order_visibility(stmt, user, vendor)
    stmt = _apply_order_search_filter(stmt, query)
    stmt = stmt.order_by(
        *[expr for _, expr in rank_expressions],
        desc(Order.created_at),
        desc(Order.id),
    ).limit(limit)

    rows = db.execute(stmt).all()
    out: list[OrderAutocompleteSuggestion] = []
    for row in rows:
        best_field = min(
            ((field, getattr(row, f"{field}_rank")) for field, _ in rank_expressions),
            key=lambda item: item[1],
        )[0]
        out.append(
            OrderAutocompleteSuggestion(
                order_id=row.order_id,
                order_no=row.order_no,
                oem_bill_no=row.oem_bill_no,
                vendor_id=row.vendor_id,
                vendor_code=row.vendor_code,
                vendor_name=row.vendor_name,
                customer_name=row.customer_name,
                customer_contact=row.customer_contact,
                match_field=best_field,
                display_label=_display_order_suggestion(row),
            )
        )
    return out


@router.get("/export")
def export_csv(
    status_filter: Literal[ORDER_STATUSES] | None = Query(None, alias="status"),  # type: ignore[valid-type]
    search: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not can_act_on(db, user, "orders", "can_export", None):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot export orders")

    vendor = _vendor_for_user(db, user)
    stmt = (
        select(Order)
        .select_from(Order)
        .join(Vendor, Order.vendor_id == Vendor.id, isouter=True)
        .where(Order.deleted_at.is_(None))
    )
    stmt = _apply_order_visibility(stmt, user, vendor)
    if status_filter:
        stmt = stmt.where(Order.status == status_filter)
    stmt = _apply_order_search_filter(stmt, search)
    if user.role == "vendor" and vendor is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Orders not found")
    stmt = stmt.order_by(desc(Order.created_at))

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "ID", "Order No", "Date", "OEM Bill", "Status",
        "Vendor", "Courier", "Customer", "City",
        "LRN No", "Expected Delivery",
    ])
    for o in db.scalars(stmt).all():
        writer.writerow([
            o.id,
            o.order_no,
            o.order_date.isoformat() if o.order_date else "",
            o.oem_bill_no or "",
            o.status,
            _resolve_vendor_name(db, o.vendor_id) or "",
            _resolve_courier_name(db, o.courier_id) or "",
            o.customer_name or "",
            o.customer_city or "",
            o.lrn_no or "",
            o.expected_delivery_date.isoformat() if o.expected_delivery_date else "",
        ])
    buf.seek(0)
    filename = f"orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([buf.read()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Collection endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=OrderListResponse)
def list_orders(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
    status_filter: Literal[ORDER_STATUSES] | None = Query(None, alias="status"),  # type: ignore[valid-type]
    search: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not can_act_on(db, user, "orders", "can_view", None):
        return OrderListResponse(items=[], total=0, page=page, per_page=per_page, total_item_quantity=0, item_quantity_summary=[])

    vendor = _vendor_for_user(db, user)
    stmt = (
        select(Order)
        .select_from(Order)
        .join(Vendor, Order.vendor_id == Vendor.id, isouter=True)
        .where(Order.deleted_at.is_(None))
    )
    stmt = _apply_order_visibility(stmt, user, vendor)
    if user.role == "vendor" and vendor is None:
        return OrderListResponse(items=[], total=0, page=page, per_page=per_page, total_item_quantity=0, item_quantity_summary=[])
    if status_filter:
        stmt = stmt.where(Order.status == status_filter)
    stmt = _apply_order_search_filter(stmt, search)
    stmt = stmt.order_by(desc(Order.created_at))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.offset((page - 1) * per_page).limit(per_page)).all()
    filtered_order_ids = db.scalars(select(stmt.subquery().c.id)).all()

    # Build vendor/courier lookup maps for this page (avoid N+1)
    vendor_ids = {o.vendor_id for o in rows if o.vendor_id}
    courier_ids = {o.courier_id for o in rows if o.courier_id}
    order_ids = [o.id for o in rows]

    item_code_map: dict[int, list[str]] = {}
    if order_ids:
        item_rows = db.execute(
            select(
                OrderItem.order_id,
                func.coalesce(OrderItem.item_code, ItemMaster.item_code).label("item_code")
            )
            .join(ItemMaster, OrderItem.item_id == ItemMaster.id, isouter=True)
            .where(OrderItem.order_id.in_(order_ids))
            .order_by(OrderItem.order_id, OrderItem.id)
        ).all()
        for order_id, item_code in item_rows:
            if item_code:
                item_code_map.setdefault(order_id, []).append(item_code)

    vendor_map: dict[int, str] = {}
    if vendor_ids:
        for v in db.scalars(select(Vendor).where(Vendor.id.in_(vendor_ids))).all():
            vendor_map[v.id] = v.name_of_firm

    courier_map: dict[int, str] = {}
    if courier_ids:
        for c in db.scalars(select(Courier).where(Courier.id.in_(courier_ids))).all():
            courier_map[c.id] = c.courier_name

    total_item_quantity = 0
    item_quantity_summary: list[OrderItemQuantitySummary] = []
    if filtered_order_ids:
        summary_rows = db.execute(
            select(
                func.coalesce(ItemMaster.item_name, OrderItem.item_code, "Unassigned").label("item_label"),
                func.sum(OrderItem.item_qty).label("total_qty"),
            )
            .select_from(OrderItem)
            .join(ItemMaster, OrderItem.item_id == ItemMaster.id, isouter=True)
            .where(OrderItem.order_id.in_(filtered_order_ids))
            .group_by(func.coalesce(ItemMaster.item_name, OrderItem.item_code, "Unassigned"))
            .order_by(desc(func.sum(OrderItem.item_qty)), func.coalesce(ItemMaster.item_name, OrderItem.item_code, "Unassigned"))
        ).all()
        item_quantity_summary = [
            OrderItemQuantitySummary(label=item_label, quantity=int(total_qty or 0))
            for item_label, total_qty in summary_rows
        ]
        total_item_quantity = sum(row.quantity for row in item_quantity_summary)

    items = []
    for o in rows:
        codes = list(dict.fromkeys(item_code_map.get(o.id, [])))
        items.append(
            OrderListItem(
                id=o.id,
                order_no=o.order_no,
                order_date=o.order_date,
                oem_bill_no=o.oem_bill_no,
                status=o.status,
                item_code=", ".join(codes) if codes else None,
                vendor_name=vendor_map.get(o.vendor_id) if o.vendor_id else None,
                courier_name=courier_map.get(o.courier_id) if o.courier_id else None,
                customer_name=o.customer_name,
                customer_city=o.customer_city,
                expected_delivery_date=o.expected_delivery_date,
                created_at=o.created_at,
            )
        )
    return OrderListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        total_item_quantity=total_item_quantity,
        item_quantity_summary=item_quantity_summary,
    )


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: str = Form(...),
    document: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not can_act_on(db, user, "orders", "can_create", None):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot create orders")

    try:
        body = OrderCreate.model_validate_json(payload)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid order payload: {e}")

    vendor_id = body.vendor_id
    if user.role == "vendor":
        if body.oem_bill_no:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Vendors cannot add OEM bill details")
        vendor = db.scalar(select(Vendor).where(Vendor.email == user.email))
        if vendor is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Vendor account is not linked to a vendor record")
        vendor_id = vendor.id

    # Check order_no uniqueness (only when provided, since it's optional)
    if body.order_no:
        existing = db.scalar(select(Order).where(Order.order_no == body.order_no))
        if existing:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Order No '{body.order_no}' already exists")

    order_file_path = None
    if document is not None and document.filename:
        order_file_path = await save_upload(document, module="orders")

    for item_data in body.items:
        if item_data.free_service_count > 4:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Free service count cannot exceed 4")

    _validate_order_item_serials(db, body.items or [])

    order = Order(
        order_no=body.order_no,
        order_date=body.order_date or date.today(),
        oem_bill_no=body.oem_bill_no,
        vendor_id=vendor_id,
        customer_name=body.customer_name,
        customer_contact=body.customer_contact,
        customer_email=body.customer_email,
        customer_city=body.customer_city,
        customer_state=body.customer_state,
        customer_address=body.customer_address,
        courier_id=_ensure_active_courier(db, body.courier_id),
        lrn_no=body.lrn_no,
        vendor_bill_no=body.vendor_bill_no,
        vendor_bill_date=body.vendor_bill_date,
        status=body.status,
        expected_delivery_date=body.expected_delivery_date,
        order_file_path=order_file_path,
        created_by=user.id,
    )
    db.add(order)
    db.flush()  # get order.id

    for item_data in body.items:
        resolved_item_code = _resolve_item_code(db, item_data.item_id, item_data.item_code)
        order_item = OrderItem(
            order_id=order.id,
            item_id=item_data.item_id,
            item_code=resolved_item_code,
            serial_no=item_data.serial_no,
            serial_no_2=item_data.serial_no_2,
            item_qty=item_data.item_qty,
            pcb_warranty_years=item_data.pcb_warranty_years,
            component_warranty_years=item_data.component_warranty_years,
            machine_warranty_years=item_data.machine_warranty_years,
            free_service_count=item_data.free_service_count,
        )
        db.add(order_item)
        db.flush()
        if order_item.serial_no:
            create_serial_history_event(
                db,
                serial_no=order_item.serial_no,
                serial_no_2=order_item.serial_no_2,
                order_item_id=order_item.id,
                event_type=EVENT_TYPES["ORDER"],
                event_subtype="ORDER_CREATED",
                event_at=order.created_at,
                performed_by_user_id=user.id,
                performed_by_name=user.name,
                source_table="orders",
                source_id=order.id,
                title="Order created",
                description=f"Order {order.order_no or order.id} created with status {order.status}.",
                metadata={
                    "order_no": order.order_no,
                    "customer_name": order.customer_name,
                    "status": order.status,
                    "expected_delivery_date": order.expected_delivery_date.isoformat() if order.expected_delivery_date else None,
                },
            )

    db.commit()
    db.refresh(order)
    return _hydrate_order(db, order)


# ---------------------------------------------------------------------------
# Single-item endpoints — MUST come after fixed-path routes
# ---------------------------------------------------------------------------

@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = _load_order(db, user, order_id)
    return _hydrate_order(db, order)


@router.get("/{order_id}/items/export")
def export_order_items_csv(
    order_id: int,
    item_code: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = _load_order(db, user, order_id)
    if not _can_manage_order_item_csv(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admin or incool users can export line items")

    rows = _load_order_items_for_csv(db, order.id, item_code=item_code)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(ORDER_ITEM_IMPORT_EXPORT_COLUMNS)
    for row in rows:
        writer.writerow(_serialize_order_item_csv_row(db, row))
    buf.seek(0)
    suffix = f"_{item_code}" if item_code else "_all"
    filename = f"order_{order.id}_items{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([buf.read()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{order_id}/items/import", response_model=OrderOut)
async def import_order_items_csv(
    order_id: int,
    file: UploadFile = File(...),
    item_code: str | None = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = _load_order(db, user, order_id)
    if not _can_manage_order_item_csv(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admin or incool users can import line items")
    if not file.filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "CSV file is required")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "CSV must be UTF-8 encoded")

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "CSV header is missing")

    required = {"ID"}
    missing = required - set(reader.fieldnames)
    if missing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"CSV is missing required columns: {', '.join(sorted(missing))}")

    existing_items = {item.id: item for item in _load_order_items_for_csv(db, order.id)}
    updated = 0
    touched_items: list[tuple[int, OrderItem]] = []
    for idx, row in enumerate(reader, start=2):
        raw_id = (row.get("ID") or "").strip()
        if not raw_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Row {idx}: ID is required")
        try:
            item_id_key = int(raw_id)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Row {idx}: invalid ID '{raw_id}'")
        item = existing_items.get(item_id_key)
        if item is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Row {idx}: order item {item_id_key} was not found")
        if item_code and (item.item_code or "") != item_code:
            actual_item_code = item.item_code or "UNASSIGNED"
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Row {idx}: order item {item_id_key} belongs to item code {actual_item_code}, but you are importing into item code {item_code}",
            )

        raw_item_id = (row.get("Item ID") or "").strip()
        if raw_item_id:
            try:
                item.item_id = int(raw_item_id)
            except ValueError:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Row {idx}: invalid Item ID '{raw_item_id}'")
        raw_item_code = (row.get("Item Code") or "").strip()
        item.item_code = raw_item_code or _resolve_item_code(db, item.item_id, item.item_code)
        item.serial_no = (row.get("Serial Number 1") or "").strip() or None
        item.serial_no_2 = (row.get("Serial Number 2") or "").strip() or None

        def parse_optional_int(column: str) -> int | None:
            raw = (row.get(column) or "").strip()
            if raw == "":
                return None
            try:
                return int(raw)
            except ValueError:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Row {idx}: invalid {column} '{raw}'")

        item.pcb_warranty_years = parse_optional_int("PCB Warranty")
        item.component_warranty_years = parse_optional_int("Component Warranty")
        item.machine_warranty_years = parse_optional_int("Machine Warranty")
        free_services = parse_optional_int("Free Services")
        if free_services is not None:
            if free_services not in {0, 2, 4}:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Row {idx}: Free Services must be 0, 2, or 4")
            item.free_service_count = free_services
        raw_status = (row.get("Installation Status") or "").strip()
        item.installation_status = raw_status or "Not Requested"
        touched_items.append((idx, item))
        updated += 1

    serial_owners: dict[str, tuple[int, int]] = {}
    for existing in existing_items.values():
        for serial_value in (existing.serial_no, existing.serial_no_2):
            normalized = _normalize_serial(serial_value)
            if not normalized:
                continue
            serial_owners[normalized] = (existing.id, 0)

    for row_idx, item in touched_items:
        row_serials: list[tuple[str, str]] = []
        for label, serial_value in (("Serial Number 1", item.serial_no), ("Serial Number 2", item.serial_no_2)):
            normalized = _normalize_serial(serial_value)
            if not normalized:
                continue
            row_serials.append((label, normalized))

        if len({normalized for _, normalized in row_serials}) != len(row_serials):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Row {row_idx}: Serial Number 1 and Serial Number 2 cannot be the same",
            )

        for label, normalized in row_serials:
            owner = serial_owners.get(normalized)
            if owner is not None and owner[0] != item.id:
                conflict_row = owner[1]
                if conflict_row:
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST,
                        f"Row {row_idx}: duplicate serial '{normalized}' already used in row {conflict_row}",
                    )
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"Row {row_idx}: duplicate serial '{normalized}' already exists on this order",
                )
            serial_owners[normalized] = (item.id, row_idx)

    global_conflicts = _find_global_serial_conflicts(
        db,
        set(serial_owners.keys()),
        exclude_item_ids=set(existing_items.keys()),
    )
    if global_conflicts:
        for row_idx, item in touched_items:
            for serial_value in (item.serial_no, item.serial_no_2):
                normalized = _normalize_serial(serial_value)
                if normalized and normalized in global_conflicts:
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST,
                        f"Row {row_idx}: duplicate serial '{serial_value}' already exists in another order",
                    )

    db.commit()
    db.refresh(order)
    hydrated = _hydrate_order(db, order)
    hydrated_msg = f"{updated} row(s) imported from CSV"
    hydrated.__dict__["import_message"] = hydrated_msg
    return hydrated


@router.put("/{order_id}", response_model=OrderOut)
def update_order(
    order_id: int,
    body: OrderUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = _load_order(db, user, order_id)
    if not can_act_on(db, user, "orders", "can_edit", None):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot edit orders")

    data = body.model_dump(exclude_unset=True)
    if user.role == "vendor":
        if order.status != "Pending" and order.oem_bill_no:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Vendors can no longer edit this order after the OEM bill is updated")
        if order.status != "Pending" and "oem_bill_no" in data and data["oem_bill_no"] not in (None, ""):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Vendors cannot update OEM bill details")

    item_updates = data.pop("items", None)
    order_expected_delivery_before = order.expected_delivery_date

    for field, value in data.items():
        if field == "courier_id":
            value = _ensure_active_courier(db, value)
        setattr(order, field, value)

    if item_updates is not None:
        existing_items = {
            item.id: item
            for item in db.scalars(select(OrderItem).where(OrderItem.order_id == order.id)).all()
        }
        validated_updates: list[OrderItemUpdate] = []
        for item_data in item_updates:
            item_payload = item_data if isinstance(item_data, OrderItemUpdate) else OrderItemUpdate.model_validate(item_data)
            item = existing_items.get(item_payload.id)
            if item is None:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Order item {item_payload.id} does not belong to this order")
            validated_updates.append(
                OrderItemUpdate(
                    id=item.id,
                    item_code=item_payload.item_code,
                    item_id=item_payload.item_id if item_payload.item_id is not None else item.item_id,
                    serial_no=item_payload.serial_no if item_payload.serial_no is not None else item.serial_no,
                    serial_no_2=item_payload.serial_no_2 if item_payload.serial_no_2 is not None else item.serial_no_2,
                    pcb_warranty_years=item_payload.pcb_warranty_years,
                    component_warranty_years=item_payload.component_warranty_years,
                    machine_warranty_years=item_payload.machine_warranty_years,
                    free_service_count=item_payload.free_service_count,
                    installation_status=item_payload.installation_status,
                )
            )

        _validate_order_item_serials(db, validated_updates, exclude_item_ids=set(existing_items.keys()))

        for item_payload in validated_updates:
            item = existing_items.get(item_payload.id)
            if item is None:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Order item {item_payload.id} does not belong to this order")
            previous_values = {
                "item_code": item.item_code,
                "item_id": item.item_id,
                "serial_no": item.serial_no,
                "serial_no_2": item.serial_no_2,
                "pcb_warranty_years": item.pcb_warranty_years,
                "component_warranty_years": item.component_warranty_years,
                "machine_warranty_years": item.machine_warranty_years,
                "free_service_count": item.free_service_count,
                "installation_status": item.installation_status,
            }

            item.item_code = item_payload.item_code.strip() if item_payload.item_code else None
            item.item_id = item_payload.item_id
            item.serial_no = item_payload.serial_no.strip() if item_payload.serial_no else None
            item.serial_no_2 = item_payload.serial_no_2.strip() if item_payload.serial_no_2 else None
            if item_payload.pcb_warranty_years is not None:
                item.pcb_warranty_years = item_payload.pcb_warranty_years
            if item_payload.component_warranty_years is not None:
                item.component_warranty_years = item_payload.component_warranty_years
            if item_payload.machine_warranty_years is not None:
                item.machine_warranty_years = item_payload.machine_warranty_years
            if item_payload.free_service_count is not None:
                item.free_service_count = item_payload.free_service_count
            if item_payload.installation_status is not None:
                item.installation_status = item_payload.installation_status

            latest_serial = item.serial_no or item.serial_no_2
            if latest_serial:
                changes: dict[str, dict[str, object | None]] = {}
                current_values = {
                    "item_code": item.item_code,
                    "item_id": item.item_id,
                    "serial_no": item.serial_no,
                    "serial_no_2": item.serial_no_2,
                    "pcb_warranty_years": item.pcb_warranty_years,
                    "component_warranty_years": item.component_warranty_years,
                    "machine_warranty_years": item.machine_warranty_years,
                    "free_service_count": item.free_service_count,
                    "installation_status": item.installation_status,
                }
                for field_name, current_value in current_values.items():
                    if previous_values[field_name] != current_value:
                        changes[field_name] = {
                            "from": previous_values[field_name],
                            "to": current_value,
                        }

                if changes or order_expected_delivery_before != order.expected_delivery_date:
                    metadata = {
                        "order_id": order.id,
                        "order_no": order.order_no,
                        "changes": changes,
                    }
                    if order_expected_delivery_before != order.expected_delivery_date:
                        metadata["expected_delivery_date"] = {
                            "from": order_expected_delivery_before.isoformat() if order_expected_delivery_before else None,
                            "to": order.expected_delivery_date.isoformat() if order.expected_delivery_date else None,
                        }
                    create_serial_history_event(
                        db,
                        serial_no=latest_serial,
                        serial_no_2=item.serial_no_2 if latest_serial == item.serial_no else item.serial_no,
                        order_item_id=item.id,
                        event_type=EVENT_TYPES["ORDER"],
                        event_subtype="ORDER_ITEM_UPDATED",
                        event_at=datetime.now(timezone.utc),
                        performed_by_user_id=user.id,
                        performed_by_name=user.name,
                        source_table="order_items",
                        source_id=item.id,
                        title="Order line item updated",
                        description="Warranty or serial details were updated from the order page.",
                        metadata=metadata,
                    )

    db.commit()
    db.refresh(order)
    return _hydrate_order(db, order)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = _load_order(db, user, order_id)
    if not can_act_on(db, user, "orders", "can_delete", None):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot delete orders")
    order.deleted_at = datetime.now(timezone.utc)
    db.commit()


# ---------------------------------------------------------------------------
# Bulk serial assignment endpoint
# ---------------------------------------------------------------------------

from pydantic import BaseModel

class BulkSerialSubmitRequest(BaseModel):
    order_id: int
    order_item_ids: list[int] = []  # validation cross-check only; grouping is driven by selected_serials
    selected_serials: list[str]  # ordered list of "{order_item_id}-serial1"/"serial2" identifiers


def _chunk_pairs(values: list) -> list[tuple]:
    """Group a list into consecutive pairs, in order; a trailing odd item forms a 1-tuple."""
    chunks = []
    for i in range(0, len(values), 2):
        pair = values[i:i + 2]
        chunks.append(tuple(pair))
    return chunks


@router.post("/{order_id}/submit-serials", status_code=status.HTTP_200_OK)
def submit_serials_for_assignment(
    order_id: int,
    body: BulkSerialSubmitRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Vendor submits selected serial numbers (which may span multiple OrderItem rows) for
    engineer assignment. Selected serials are re-paired, two at a time in selection order,
    into brand-new locked ("Submitted") OrderItem rows, each backed by one InstallationRequest.
    Any leftover (non-selected) serials on the touched original rows are likewise re-paired
    into brand-new OPEN ("Not Requested") rows, and the original rows are deleted. Selecting a
    serial that already belongs to a locked row is a no-op for that serial (reported as
    skipped) rather than failing the whole batch.
    """
    from app.models.installation import InstallationRequest

    order = _load_order(db, user, order_id)
    if not _can_submit_serials(db, user, order):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot edit this order")

    if order.status != "Delivered":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Can only submit serials from Delivered orders",
        )
    if not (order.oem_bill_no or "").strip():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "OEM Bill No is required before submitting installation requests",
        )

    if not body.selected_serials:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No serials selected")

    # Parse "{order_item_id}-serial1"/"serial2" identifiers, preserving selection order.
    parsed: list[tuple[int, str]] = []
    for key in body.selected_serials:
        try:
            item_id_str, slot = key.rsplit("-", 1)
            item_id = int(item_id_str)
        except ValueError:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid serial selection: {key}")
        if slot not in ("serial1", "serial2"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Invalid serial selection: {key}")
        parsed.append((item_id, slot))

    referenced_ids = {item_id for item_id, _ in parsed}
    items_by_id = {
        item.id: item
        for item in db.scalars(
            select(OrderItem).where(
                OrderItem.id.in_(referenced_ids),
                OrderItem.order_id == order_id,
            )
        ).all()
    }
    if len(items_by_id) != len(referenced_ids):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Some order items do not belong to this order",
        )

    selected_item_codes = {
        (item.item_code or "").strip() or "UNASSIGNED"
        for item in items_by_id.values()
    }
    if len(selected_item_codes) > 1:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Installation request submission can include serials from only one item code at a time",
        )

    # Resolve to (item, slot, serial_value) in selection order, skipping already-locked rows.
    resolved: list[tuple[OrderItem, str, str]] = []
    skipped_already_submitted: list[str] = []
    for item_id, slot in parsed:
        item = items_by_id[item_id]
        if item.installation_status != "Not Requested":
            skipped_already_submitted.append(getattr(item, "serial_no" if slot == "serial1" else "serial_no_2") or f"item#{item_id}:{slot}")
            continue
        serial_value = item.serial_no if slot == "serial1" else item.serial_no_2
        if not serial_value:
            continue  # nothing selected in that slot; ignore silently
        resolved.append((item, slot, serial_value))

    if not resolved:
        return {
            "message": "No new serials submitted",
            "count": 0,
            "order_id": order_id,
            "order_no": order.order_no,
            "submitted_order_item_ids": [],
            "repaired_open_order_item_ids": [],
            "consumed_order_item_ids": [],
            "skipped_already_submitted": skipped_already_submitted,
        }

    global_conflicts = _find_global_serial_conflicts(
        db,
        {serial_value for _, _, serial_value in resolved},
        exclude_item_ids=referenced_ids,
    )
    if global_conflicts:
        serial_value = next(
            value for _, _, value in resolved
            if _normalize_serial(value) in global_conflicts
        )
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Serial '{serial_value}' already exists in another order and cannot be submitted",
        )

    touched_items = {item.id: item for item, _, _ in resolved}
    selected_keys = {(item.id, slot) for item, slot, _ in resolved}

    # Leftover serials: the non-selected slot(s) on any touched row, in row-encounter order.
    leftover: list[tuple[OrderItem, str, str]] = []
    for item in touched_items.values():
        for slot in ("serial1", "serial2"):
            if (item.id, slot) in selected_keys:
                continue
            serial_value = item.serial_no if slot == "serial1" else item.serial_no_2
            if serial_value:
                leftover.append((item, slot, serial_value))

    def _make_row(chunk: list[tuple[OrderItem, str, str]], locked: bool) -> OrderItem:
        source_item = chunk[0][0]
        # Preserve each serial's original slot (serial1 -> serial_no, serial2 -> serial_no_2)
        # rather than assigning by chunk position, so a "Serial 2" origin never lands in the
        # new row's "Serial 1" column.
        serial1_val = next((val for _, slot, val in chunk if slot == "serial1"), None)
        serial2_val = next((val for _, slot, val in chunk if slot == "serial2"), None)
        # If both selected serials came from the same original slot (e.g. two serial1's),
        # there's no slot collision to worry about -- just place them in order.
        if serial1_val is not None and serial2_val is not None:
            new_serial_no, new_serial_no_2 = serial1_val, serial2_val
        else:
            values = [val for _, _, val in chunk]
            new_serial_no = values[0]
            new_serial_no_2 = values[1] if len(values) > 1 else None

        new_item = OrderItem(
            order_id=order_id,
            item_id=source_item.item_id,
            item_code=source_item.item_code,
            serial_no=new_serial_no,
            serial_no_2=new_serial_no_2,
            item_qty=source_item.item_qty,
            pcb_warranty_years=source_item.pcb_warranty_years,
            component_warranty_years=source_item.component_warranty_years,
            machine_warranty_years=source_item.machine_warranty_years,
            free_service_count=source_item.free_service_count,
            service_consume_count=source_item.service_consume_count,
            installation_status="Submitted" if locked else "Not Requested",
        )
        db.add(new_item)
        db.flush()  # obtain new_item.id
        if locked:
            db.add(InstallationRequest(
                customer_name=order.customer_name or "Unknown",
                contact_number=order.customer_contact or "",
                address=order.customer_city or "",
                order_item_id=new_item.id,
                product_name=_resolve_item_name(db, new_item.item_id),
                serial_no=new_item.serial_no,
                serial_no_2=new_item.serial_no_2,
                request_date=datetime.now(timezone.utc),
                assigned_engineer=None,
                status="Submitted",
            ))
        return new_item

    submitted_ids: list[int] = []
    for chunk_values in _chunk_pairs(resolved):
        new_item = _make_row(list(chunk_values), locked=True)
        submitted_ids.append(new_item.id)

    repaired_ids: list[int] = []
    for chunk_values in _chunk_pairs(leftover):
        new_item = _make_row(list(chunk_values), locked=False)
        repaired_ids.append(new_item.id)

    consumed_ids = list(touched_items.keys())
    blocking_claim = db.scalar(
        select(Claim.id).where(Claim.order_item_id.in_(consumed_ids)).limit(1)
    )
    if blocking_claim is not None:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "One or more selected serial rows are already linked to a claim and cannot be rearranged",
        )

    blocking_complaint = db.scalar(
        select(func.count()).select_from(Complaint).where(Complaint.order_item_id.in_(consumed_ids))
    )
    if blocking_complaint:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "One or more selected serial rows are already linked to a complaint and cannot be rearranged",
        )

    # Historical serial events should remain, but they must be detached from the soon-to-be
    # deleted source rows because serial_history_events.order_item_id is a foreign key.
    db.query(SerialHistoryEvent).filter(
        SerialHistoryEvent.order_item_id.in_(consumed_ids)
    ).update(
        {SerialHistoryEvent.order_item_id: None},
        synchronize_session=False,
    )

    for item in touched_items.values():
        db.delete(item)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Selected serial rows are still referenced elsewhere and could not be submitted. Please refresh the order and try again.",
        )

    return {
        "message": f"Submitted {len(submitted_ids)} row(s) for engineer assignment",
        "count": len(submitted_ids),
        "order_id": order_id,
        "order_no": order.order_no,
        "submitted_order_item_ids": submitted_ids,
        "repaired_open_order_item_ids": repaired_ids,
        "consumed_order_item_ids": consumed_ids,
        "skipped_already_submitted": skipped_already_submitted,
    }
