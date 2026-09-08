from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.installation import InstallationRequest
from app.models.order import Order, OrderItem
from app.models.payment import PaymentTransaction
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.installation import (
    BulkAssignRequest,
    BulkCancelRequest,
    InstallationEngineerAssignmentOption,
    InstallationCreate,
    InstallationBulkUpdateRequest,
    InstallationListItem,
    InstallationListResponse,
    InstallationOut,
    InstallationPaymentHistoryGroupItem,
    InstallationPaymentHistoryResponse,
    InstallationPaymentHistoryRequestItem,
    InstallationStatusUpdate,
)
from app.services.file_service import read_upload_bytes, save_upload, to_public_upload_path
from app.services.permissions import can_act_on
from app.services.serial_history import EVENT_TYPES, create_serial_history_event

router = APIRouter(prefix="/api/installations", tags=["installations"])

STATUSES = [
    "Pending", "Submitted", "Assigned", "In Progress", "Payment Pending", "Completed",
    "Settlement Pending", "Settlement Approved", "Returned", "Rejected",
]

PAYMENT_TYPES = {"Cash", "UPI"}
PENDING_ASSIGNMENT_STATUSES = ("Assigned", "In Progress", "Payment Pending", "Settlement Pending")
SUCCESS_ASSIGNMENT_STATUSES = ("Completed", "Settlement Approved")
UNSUCCESS_ASSIGNMENT_STATUSES = ("Returned", "Rejected")


def _payment_qr_view_url(inst: InstallationRequest) -> str | None:
    if inst.payment_qr_code_blob:
        return f"/api/installations/{inst.id}/payment-qr"
    return to_public_upload_path(inst.payment_qr_code_path)


def _validate_installation_request_allowed(db: Session, order_item_id: int | None) -> OrderItem:
    if order_item_id is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Installation request must be linked to an order item",
        )
    item = db.get(OrderItem, order_item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order item not found")
    order = db.get(Order, item.order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    if order.status != "Delivered":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Installation request can be raised only after the order is Delivered",
        )
    if not (order.oem_bill_no or "").strip():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Installation request can be raised only after OEM Bill No is submitted",
        )
    return item


def _resolve_order_vendor(db: Session, order_item_id: int | None) -> tuple[str | None, str | None]:
    """Resolve (order_no, vendor_name) for an InstallationRequest via its order_item_id."""
    if order_item_id is None:
        return None, None
    item = db.get(OrderItem, order_item_id)
    if item is None:
        return None, None
    order = db.get(Order, item.order_id)
    if order is None:
        return None, None
    vendor_name = None
    if order.vendor_id:
        v = db.get(Vendor, order.vendor_id)
        vendor_name = v.name_of_firm if v else None
    return order.order_no, vendor_name


def _list_row(
    db: Session,
    inst: InstallationRequest,
    order_map: dict[int, Order],
    order_item_map: dict[int, OrderItem],
    vendor_map: dict[int, str],
) -> InstallationListItem:
    engineer_name = None
    if inst.assigned_engineer:
        u = db.get(User, inst.assigned_engineer)
        engineer_name = u.name if u else None
    approved_by_name = None
    if inst.settlement_approved_by:
        u = db.get(User, inst.settlement_approved_by)
        approved_by_name = u.name if u else None
    payment_recorded_by_name = None
    if inst.payment_recorded_by:
        u = db.get(User, inst.payment_recorded_by)
        payment_recorded_by_name = u.name if u else None
    order_item = order_item_map.get(inst.order_item_id)
    order = order_map.get(inst.order_item_id)
    order_no = order.order_no if order else None
    vendor_name = vendor_map.get(order.vendor_id) if order and order.vendor_id else None
    return InstallationListItem(
        id=inst.id,
        order_item_id=inst.order_item_id,
        item_code=order_item.item_code if order_item else None,
        customer_name=inst.customer_name,
        contact_number=inst.contact_number,
        product_name=inst.product_name,
        order_no=order_no,
        vendor_name=vendor_name,
        serial_no=inst.serial_no,
        serial_no_2=inst.serial_no_2,
        status=inst.status,
        request_date=inst.request_date,
        installation_date=inst.installation_date,
        assigned_engineer_name=engineer_name,
        settlement_approved_by_name=approved_by_name,
        payment_amount_requested=float(inst.payment_amount_requested) if inst.payment_amount_requested is not None else None,
        payment_type_requested=inst.payment_type_requested,
        payment_qr_code_path=_payment_qr_view_url(inst),
        payment_qr_code_filename=inst.payment_qr_code_filename,
        payment_proof_file_path=to_public_upload_path(inst.payment_proof_file_path),
    )


def _hydrate(db: Session, inst: InstallationRequest) -> dict:
    engineer_name = None
    if inst.assigned_engineer:
        u = db.get(User, inst.assigned_engineer)
        engineer_name = u.name if u else None
    approved_by_name = None
    if inst.settlement_approved_by:
        u = db.get(User, inst.settlement_approved_by)
        approved_by_name = u.name if u else None
    payment_recorded_by_name = None
    if inst.payment_recorded_by:
        u = db.get(User, inst.payment_recorded_by)
        payment_recorded_by_name = u.name if u else None
    order_no, vendor_name = _resolve_order_vendor(db, inst.order_item_id)
    return {
        **{k: getattr(inst, k) for k in (
            "id", "customer_name", "contact_number", "address", "order_item_id", "product_name",
            "serial_no", "serial_no_2",
            "request_date", "assigned_engineer", "status", "installation_date",
            "work_report", "work_report_file_path", "settlement_approved_by",
            "payment_type_requested", "payment_qr_code_path", "payment_qr_code_filename", "payment_proof_file_path", "payment_requested_at",
            "payment_type_paid", "payment_recorded_at", "payment_recorded_by",
            "created_at", "updated_at",
        )},
        "payment_amount_requested": float(inst.payment_amount_requested) if inst.payment_amount_requested is not None else None,
        "payment_amount_paid": float(inst.payment_amount_paid) if inst.payment_amount_paid is not None else None,
        "work_report_file_path": to_public_upload_path(inst.work_report_file_path),
        "payment_qr_code_path": _payment_qr_view_url(inst),
        "payment_qr_code_filename": inst.payment_qr_code_filename,
        "payment_proof_file_path": to_public_upload_path(inst.payment_proof_file_path),
        "order_no": order_no,
        "vendor_name": vendor_name,
        "assigned_engineer_name": engineer_name,
        "settlement_approved_by_name": approved_by_name,
        "payment_recorded_by_name": payment_recorded_by_name,
    }


def _apply_payment_transition(
    inst: InstallationRequest,
    *,
    requested_status: str,
    actor: User,
    installation_date: str | None,
    payment_amount: str | None = None,
    payment_type: str | None = None,
    payment_qr_code_path: str | None = None,
    payment_qr_code_blob: bytes | None = None,
    payment_qr_code_filename: str | None = None,
    payment_qr_code_content_type: str | None = None,
    payment_qr_code_size_bytes: int | None = None,
) -> str:
    normalized_payment_type = (payment_type or "").strip() or None
    if normalized_payment_type is not None and normalized_payment_type not in PAYMENT_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Payment type must be Cash or UPI")

    if requested_status == "Completed" and actor.role == "engineer":
        if not installation_date:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Installation date is required when status is Completed")
        if payment_amount in (None, ""):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Payment Amount is required when status is Completed")
        if normalized_payment_type is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Payment Type is required when status is Completed")
        if normalized_payment_type == "UPI" and not payment_qr_code_blob and not inst.payment_qr_code_blob and not inst.payment_qr_code_path:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "QR Code is required when payment type is UPI")

        inst.payment_amount_requested = float(payment_amount)
        inst.payment_type_requested = normalized_payment_type
        if payment_qr_code_blob:
            inst.payment_qr_code_blob = payment_qr_code_blob
            inst.payment_qr_code_filename = payment_qr_code_filename
            inst.payment_qr_code_content_type = payment_qr_code_content_type
            inst.payment_qr_code_size_bytes = payment_qr_code_size_bytes
            inst.payment_qr_code_path = None
        inst.payment_requested_at = datetime.now(timezone.utc)
        return "Payment Pending"

    if requested_status == "Completed" and actor.role in {"admin", "incool"} and inst.status == "Payment Pending":
        if payment_amount in (None, "") and inst.payment_amount_requested is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Payment Amount is required to complete payment")
        effective_amount = float(payment_amount) if payment_amount not in (None, "") else float(inst.payment_amount_requested)
        effective_type = normalized_payment_type or inst.payment_type_requested
        if effective_type is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Payment Type is required to complete payment")
        if effective_type == "UPI" and not payment_qr_code_blob and not inst.payment_qr_code_blob and not inst.payment_qr_code_path:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "QR Code is required when payment type is UPI")

        inst.payment_amount_requested = effective_amount
        inst.payment_amount_paid = effective_amount
        inst.payment_type_requested = effective_type
        inst.payment_type_paid = effective_type
        if payment_qr_code_blob:
            inst.payment_qr_code_blob = payment_qr_code_blob
            inst.payment_qr_code_filename = payment_qr_code_filename
            inst.payment_qr_code_content_type = payment_qr_code_content_type
            inst.payment_qr_code_size_bytes = payment_qr_code_size_bytes
            inst.payment_qr_code_path = None
        inst.payment_recorded_at = datetime.now(timezone.utc)
        inst.payment_recorded_by = actor.id
        return "Completed"

    return requested_status


def _create_payment_transaction(
    db: Session,
    *,
    rows: list[InstallationRequest],
    actor: User,
    payment_type: str,
) -> PaymentTransaction:
    total_amount = sum(float(row.payment_amount_paid or row.payment_amount_requested or 0) for row in rows)
    engineer_ids = {row.assigned_engineer for row in rows if row.assigned_engineer}
    transaction = PaymentTransaction(
        payment_type=payment_type,
        total_amount=total_amount,
        request_count=len(rows),
        recorded_by_user_id=actor.id,
        engineer_user_id=next(iter(engineer_ids)) if len(engineer_ids) == 1 else None,
    )
    db.add(transaction)
    db.flush()
    for row in rows:
        row.payment_transaction_id = transaction.id
    return transaction


def _engineer_assignment_options(db: Session) -> list[InstallationEngineerAssignmentOption]:
    engineers = db.scalars(
        select(User)
        .where(User.deleted_at.is_(None), User.is_active.is_(True), User.role == "engineer")
        .order_by(User.name)
    ).all()
    if not engineers:
        return []

    engineer_ids = [engineer.id for engineer in engineers]

    pending_rows = db.execute(
        select(
            InstallationRequest.assigned_engineer,
            func.count(InstallationRequest.id),
        )
        .where(
            InstallationRequest.assigned_engineer.in_(engineer_ids),
            InstallationRequest.status.in_(PENDING_ASSIGNMENT_STATUSES),
        )
        .group_by(InstallationRequest.assigned_engineer)
    ).all()
    pending_map = {engineer_id: count for engineer_id, count in pending_rows if engineer_id is not None}

    performance_rows = db.execute(
        select(
            InstallationRequest.assigned_engineer,
            func.sum(
                case(
                    (InstallationRequest.status.in_(SUCCESS_ASSIGNMENT_STATUSES), 1),
                    else_=0,
                )
            ).label("completed_count"),
            func.sum(
                case(
                    (InstallationRequest.status.in_(UNSUCCESS_ASSIGNMENT_STATUSES), 1),
                    else_=0,
                )
            ).label("unsuccessful_count"),
        )
        .where(InstallationRequest.assigned_engineer.in_(engineer_ids))
        .group_by(InstallationRequest.assigned_engineer)
    ).all()

    performance_map: dict[int, tuple[int, int]] = {}
    for engineer_id, completed_count, unsuccessful_count in performance_rows:
        if engineer_id is not None:
            performance_map[engineer_id] = (int(completed_count or 0), int(unsuccessful_count or 0))

    options: list[InstallationEngineerAssignmentOption] = []
    for engineer in engineers:
        completed_count, unsuccessful_count = performance_map.get(engineer.id, (0, 0))
        rated_jobs = completed_count + unsuccessful_count
        if rated_jobs == 0:
            rating = 0.0
        else:
            rating = round((completed_count / rated_jobs) * 5, 1)
        options.append(
            InstallationEngineerAssignmentOption(
                id=engineer.id,
                name=engineer.name,
                email=engineer.email,
                pending_requests=int(pending_map.get(engineer.id, 0)),
                rating=rating,
                completed_requests=completed_count,
            )
        )
    return options


@router.get("", response_model=InstallationListResponse)
def list_installations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    order_id: int | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not can_act_on(db, user, "installations", "can_view", None):
        return InstallationListResponse(items=[], total=0, page=page, per_page=per_page)

    stmt = select(InstallationRequest)

    # Engineers only ever see installation requests assigned to them.
    if user.role == "engineer":
        stmt = stmt.where(InstallationRequest.assigned_engineer == user.id)

    if order_id is not None:
        stmt = stmt.join(OrderItem, OrderItem.id == InstallationRequest.order_item_id).where(
            OrderItem.order_id == order_id
        )
    if status_filter and status_filter in STATUSES:
        stmt = stmt.where(InstallationRequest.status == status_filter)
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(
            InstallationRequest.customer_name.ilike(like) |
            InstallationRequest.contact_number.ilike(like) |
            InstallationRequest.product_name.ilike(like)
        )
    if date_from:
        stmt = stmt.where(InstallationRequest.request_date >= date_from)
    if date_to:
        stmt = stmt.where(InstallationRequest.request_date <= date_to)

    stmt = stmt.order_by(desc(InstallationRequest.request_date))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.offset((page - 1) * per_page).limit(per_page)).all()

    # Batch-resolve order/vendor lookups for the page (avoid N+1)
    order_item_ids = {r.order_item_id for r in rows if r.order_item_id}
    order_map: dict[int, Order] = {}
    order_item_map: dict[int, OrderItem] = {}
    if order_item_ids:
        items = db.scalars(select(OrderItem).where(OrderItem.id.in_(order_item_ids))).all()
        order_item_map = {item.id: item for item in items}
        order_ids = {i.order_id for i in items}
        orders_by_id = {
            o.id: o for o in db.scalars(select(Order).where(Order.id.in_(order_ids))).all()
        } if order_ids else {}
        for i in items:
            order_map[i.id] = orders_by_id.get(i.order_id)

    vendor_ids = {o.vendor_id for o in order_map.values() if o and o.vendor_id}
    vendor_map: dict[int, str] = {}
    if vendor_ids:
        for v in db.scalars(select(Vendor).where(Vendor.id.in_(vendor_ids))).all():
            vendor_map[v.id] = v.name_of_firm

    return InstallationListResponse(
        items=[_list_row(db, inst, order_map, order_item_map, vendor_map) for inst in rows],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/payment-history", response_model=InstallationPaymentHistoryResponse)
def payment_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
    search: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role not in {"admin", "incool"}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot view payment history")

    stmt = select(PaymentTransaction)
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.join(
            InstallationRequest,
            InstallationRequest.payment_transaction_id == PaymentTransaction.id,
        ).where(
            InstallationRequest.customer_name.ilike(like) |
            InstallationRequest.product_name.ilike(like) |
            InstallationRequest.serial_no.ilike(like)
        )
    stmt = stmt.order_by(desc(PaymentTransaction.recorded_at))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.offset((page - 1) * per_page).limit(per_page)).all()

    transaction_ids = [row.id for row in rows]
    linked_installations = db.scalars(
        select(InstallationRequest).where(InstallationRequest.payment_transaction_id.in_(transaction_ids))
    ).all() if transaction_ids else []

    order_item_ids = {r.order_item_id for r in linked_installations if r.order_item_id}
    order_item_map: dict[int, OrderItem] = {}
    order_map: dict[int, Order] = {}
    if order_item_ids:
        items = db.scalars(select(OrderItem).where(OrderItem.id.in_(order_item_ids))).all()
        order_item_map = {item.id: item for item in items}
        order_ids = {i.order_id for i in items}
        orders_by_id = {
            o.id: o for o in db.scalars(select(Order).where(Order.id.in_(order_ids))).all()
        } if order_ids else {}
        for item in items:
            order_map[item.id] = orders_by_id.get(item.order_id)

    linked_by_transaction: dict[int, list[InstallationRequest]] = {}
    for installation in linked_installations:
        linked_by_transaction.setdefault(installation.payment_transaction_id, []).append(installation)

    items: list[InstallationPaymentHistoryGroupItem] = []
    for txn in rows:
        recorded_by_name = None
        if txn.recorded_by_user_id:
            recorded_by = db.get(User, txn.recorded_by_user_id)
            recorded_by_name = recorded_by.name if recorded_by else None
        engineer_name = None
        if txn.engineer_user_id:
            engineer = db.get(User, txn.engineer_user_id)
            engineer_name = engineer.name if engineer else None
        request_items: list[InstallationPaymentHistoryRequestItem] = []
        for inst in linked_by_transaction.get(txn.id, []):
            order_item = order_item_map.get(inst.order_item_id)
            order = order_map.get(inst.order_item_id)
            request_items.append(InstallationPaymentHistoryRequestItem(
                id=inst.id,
                order_no=order.order_no if order else None,
                item_code=order_item.item_code if order_item else None,
                customer_name=inst.customer_name,
                installation_date=inst.installation_date,
                requested_amount=float(inst.payment_amount_requested) if inst.payment_amount_requested is not None else None,
                paid_amount=float(inst.payment_amount_paid) if inst.payment_amount_paid is not None else None,
                status=inst.status,
            ))
        items.append(InstallationPaymentHistoryGroupItem(
            id=txn.id,
            payment_type=txn.payment_type,
            total_amount=float(txn.total_amount),
            request_count=txn.request_count,
            recorded_at=txn.recorded_at,
            recorded_by_name=recorded_by_name,
            engineer_name=engineer_name,
            requests=request_items,
        ))

    return InstallationPaymentHistoryResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/engineer-assignment-options", response_model=list[InstallationEngineerAssignmentOption])
def engineer_assignment_options(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not can_act_on(db, user, "installations", "can_view", None):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot view installation engineers")
    if user.role == "engineer":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Engineers cannot assign installation requests")
    return _engineer_assignment_options(db)


@router.post("", response_model=InstallationOut, status_code=status.HTTP_201_CREATED)
def create_installation(
    body: InstallationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not can_act_on(db, user, "installations", "can_create", None):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot create installation requests")

    _validate_installation_request_allowed(db, body.order_item_id)
    order_item = db.get(OrderItem, body.order_item_id) if body.order_item_id else None

    inst = InstallationRequest(
        customer_name=body.customer_name,
        contact_number=body.contact_number,
        address=body.address,
        order_item_id=body.order_item_id,
        product_name=body.product_name,
        request_date=body.request_date or datetime.now(timezone.utc),
        status="Pending",
        serial_no=order_item.serial_no if order_item else None,
        serial_no_2=order_item.serial_no_2 if order_item else None,
    )
    db.add(inst)
    db.flush()
    if inst.serial_no:
        create_serial_history_event(
            db,
            serial_no=inst.serial_no,
            serial_no_2=inst.serial_no_2,
            order_item_id=inst.order_item_id,
            event_type=EVENT_TYPES["INSTALLATION"],
            event_subtype="REQUEST_CREATED",
            event_at=inst.request_date,
            performed_by_user_id=user.id,
            performed_by_name=user.name,
            source_table="installation_requests",
            source_id=inst.id,
            title="Installation request created",
            description=f"Installation request {inst.id} created with status {inst.status}.",
            metadata={"status": inst.status, "product_name": inst.product_name},
        )
    db.commit()
    db.refresh(inst)
    return InstallationOut(**_hydrate(db, inst))


@router.post("/bulk-assign")
def bulk_assign(
    body: BulkAssignRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Assign (or re-assign) engineers to one or more installation requests in a single call.

    Each pair may target a row by installation_id or order_item_id. Rows not currently in
    Submitted or Assigned status are skipped (not overwritten) rather than failing the batch.
    """
    if not can_act_on(db, user, "installations", "can_edit", None):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot assign installation requests")
    if user.role == "engineer":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Engineers cannot assign installation requests")

    if not body.assignments:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No assignments provided")

    engineer_ids = {a.engineer_id for a in body.assignments}
    engineers = {
        u.id: u for u in db.scalars(
            select(User).where(User.id.in_(engineer_ids), User.role == "engineer")
        ).all()
    }
    invalid_engineer_ids = sorted(engineer_ids - engineers.keys())
    if invalid_engineer_ids:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Invalid engineer id(s): {invalid_engineer_ids}",
        )

    assigned: list[int] = []
    not_found: list[dict] = []
    skipped_wrong_status: list[dict] = []

    for pair in body.assignments:
        if pair.installation_id is not None:
            inst = db.get(InstallationRequest, pair.installation_id)
        elif pair.order_item_id is not None:
            inst = db.scalar(
                select(InstallationRequest).where(InstallationRequest.order_item_id == pair.order_item_id)
            )
        else:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Each assignment must specify installation_id or order_item_id",
            )

        if inst is None:
            not_found.append({"installation_id": pair.installation_id, "order_item_id": pair.order_item_id})
            continue
        if inst.status not in ("Submitted", "Assigned"):
            skipped_wrong_status.append({"installation_id": inst.id, "status": inst.status})
            continue

        inst.assigned_engineer = pair.engineer_id
        inst.status = "Assigned"
        assigned.append(inst.id)

    db.commit()

    return {
        "assigned": assigned,
        "not_found": not_found,
        "skipped_wrong_status": skipped_wrong_status,
    }


def _cancel_one(db: Session, inst: InstallationRequest) -> None:
    """Revert a single InstallationRequest to its pre-submission state: delete the request
    and unlock its linked OrderItem back to "Not Requested" so the vendor can re-select it.
    Caller must have already validated inst.status is Submitted or Assigned.
    """
    if inst.order_item_id is not None:
        item = db.get(OrderItem, inst.order_item_id)
        if item is not None:
            item.installation_status = "Not Requested"
    db.delete(inst)


@router.post("/bulk-cancel", status_code=status.HTTP_200_OK)
def bulk_cancel(
    body: BulkCancelRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Cancel (revert) multiple installation requests in one call. Each must be in
    Submitted or Assigned status (before work starts); others are skipped, not failed.
    """
    if not can_act_on(db, user, "installations", "can_edit", None):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot cancel installation requests")
    if user.role == "engineer":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Engineers cannot cancel installation requests")

    if not body.installation_ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No installation ids provided")

    cancelled: list[int] = []
    not_found: list[int] = []
    skipped_wrong_status: list[dict] = []

    for inst_id in body.installation_ids:
        inst = db.get(InstallationRequest, inst_id)
        if inst is None:
            not_found.append(inst_id)
            continue
        if inst.status not in ("Submitted", "Assigned"):
            skipped_wrong_status.append({"installation_id": inst.id, "status": inst.status})
            continue
        _cancel_one(db, inst)
        cancelled.append(inst_id)

    db.commit()

    return {
        "cancelled": cancelled,
        "not_found": not_found,
        "skipped_wrong_status": skipped_wrong_status,
    }


@router.post("/{installation_id}/cancel", status_code=status.HTTP_200_OK)
def cancel_submission(
    installation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Revert a vendor's submission back to its original open state: allowed while status
    is "Submitted" or "Assigned" (i.e. before work has actually started). Deletes the
    InstallationRequest and unlocks the linked OrderItem back to "Not Requested" so the
    vendor can re-select it. Not allowed once work is "In Progress" or later.
    """
    inst = db.get(InstallationRequest, installation_id)
    if inst is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Installation request not found")
    if not can_act_on(db, user, "installations", "can_edit", None):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot cancel installation requests")
    if user.role == "engineer":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Engineers cannot cancel installation requests")
    if inst.status not in ("Submitted", "Assigned"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Can only cancel requests still in Submitted or Assigned status (before work starts)",
        )

    _cancel_one(db, inst)
    db.commit()
    return {"message": "Submission cancelled", "installation_id": installation_id}


def _load_visible(db: Session, user: User, inst_id: int) -> InstallationRequest:
    inst = db.get(InstallationRequest, inst_id)
    if inst is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Installation request not found")
    if not can_act_on(db, user, "installations", "can_view", None):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Installation request not found")
    if user.role == "engineer" and inst.assigned_engineer != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Installation request not found")
    return inst


@router.get("/{installation_id}", response_model=InstallationOut)
def get_installation(
    installation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    inst = _load_visible(db, user, installation_id)
    return InstallationOut(**_hydrate(db, inst))


@router.get("/{installation_id}/payment-qr")
def get_installation_payment_qr(
    installation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    inst = _load_visible(db, user, installation_id)
    if user.role not in {"admin", "incool", "engineer"}:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot view payment QR codes")
    if not inst.payment_qr_code_blob:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Payment QR code not found")
    return Response(
        content=inst.payment_qr_code_blob,
        media_type=inst.payment_qr_code_content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'inline; filename="{inst.payment_qr_code_filename or "payment-qr"}"'
        },
    )


@router.put("/{installation_id}", response_model=InstallationOut)
def update_installation(
    installation_id: int,
    body: InstallationStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    inst = _load_visible(db, user, installation_id)
    if not can_act_on(db, user, "installations", "can_edit", None):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot edit installation requests")

    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(inst, field, value)
    db.commit()
    db.refresh(inst)
    return InstallationOut(**_hydrate(db, inst))


@router.put("/{installation_id}/status", response_model=InstallationOut)
async def update_status(
    installation_id: int,
    new_status: str = Form(...),
    assigned_engineer: int | None = Form(None),
    installation_date: str | None = Form(None),
    work_report: str | None = Form(None),
    document: UploadFile | None = File(None),
    settlement_approved_by: int | None = Form(None),
    payment_amount: str | None = Form(None),
    payment_type: str | None = Form(None),
    qr_code: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Engineer-only pseudo-status: sends the job back to admin/Incool for reassignment
    # (status -> "Submitted", engineer unassigned) rather than a real lifecycle state.
    if new_status == "Send Back to Admin":
        inst = _load_visible(db, user, installation_id)
        if user.role != "engineer":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Only engineers can send a job back to admin")
        if inst.status != "Assigned":
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Can only send back to admin while status is still Assigned (before work starts)",
            )
        inst.status = "Submitted"
        inst.assigned_engineer = None
        db.commit()
        db.refresh(inst)
        return InstallationOut(**_hydrate(db, inst))

    if new_status not in STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid status")

    inst = _load_visible(db, user, installation_id)
    if not can_act_on(db, user, "installations", "can_edit", None):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot edit this installation request")
    if user.role == "engineer" and assigned_engineer is not None and assigned_engineer != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Engineers cannot reassign installation requests")

    doc_path = None
    if document is not None and document.filename:
        doc_path = await save_upload(document, module="installations")
    qr_blob = None
    qr_filename = None
    qr_content_type = None
    qr_size_bytes = None
    if qr_code is not None and qr_code.filename:
        qr_blob, qr_filename, qr_content_type, qr_size_bytes = await read_upload_bytes(qr_code)

    inst.status = _apply_payment_transition(
        inst,
        requested_status=new_status,
        actor=user,
        installation_date=installation_date,
        payment_amount=payment_amount,
        payment_type=payment_type,
        payment_qr_code_path=None,
        payment_qr_code_blob=qr_blob,
        payment_qr_code_filename=qr_filename,
        payment_qr_code_content_type=qr_content_type,
        payment_qr_code_size_bytes=qr_size_bytes,
    )
    if assigned_engineer is not None:
        inst.assigned_engineer = assigned_engineer
    if installation_date:
        inst.installation_date = datetime.fromisoformat(installation_date)
    if work_report is not None:
        inst.work_report = work_report
    if doc_path:
        if user.role in {"admin", "incool"} and inst.status in {"Payment Pending", "Completed"}:
            inst.payment_proof_file_path = doc_path
        else:
            inst.work_report_file_path = doc_path
    if settlement_approved_by is not None:
        inst.settlement_approved_by = settlement_approved_by
    if qr_blob:
        inst.payment_qr_code_blob = qr_blob
        inst.payment_qr_code_filename = qr_filename
        inst.payment_qr_code_content_type = qr_content_type
        inst.payment_qr_code_size_bytes = qr_size_bytes
        inst.payment_qr_code_path = None
    if user.role in {"admin", "incool"} and inst.status == "Completed" and inst.payment_recorded_at:
        _create_payment_transaction(
            db,
            rows=[inst],
            actor=user,
            payment_type=inst.payment_type_paid or inst.payment_type_requested or "Cash",
        )

    if inst.serial_no:
        create_serial_history_event(
            db,
            serial_no=inst.serial_no,
            serial_no_2=inst.serial_no_2,
            order_item_id=inst.order_item_id,
            event_type=EVENT_TYPES["INSTALLATION"],
            event_subtype=f"STATUS_{new_status.upper().replace(' ', '_')}",
            event_at=inst.installation_date or datetime.now(timezone.utc),
            performed_by_user_id=user.id,
            performed_by_name=user.name,
            source_table="installation_requests",
            source_id=inst.id + 1000000,
            title="Installation status updated",
            description=f"Installation request {inst.id} updated to {new_status}.",
            remarks=work_report,
            metadata={"status": new_status, "document_path": doc_path},
        )

    db.commit()
    db.refresh(inst)
    return InstallationOut(**_hydrate(db, inst))


@router.post("/bulk-status-update", response_model=list[InstallationOut])
async def bulk_update_status(
    installation_ids: str = Form(...),
    new_status: str = Form(...),
    installation_date: str | None = Form(None),
    work_report: str | None = Form(None),
    payment_amount: str | None = Form(None),
    payment_type: str | None = Form(None),
    settlement_approved_by: int | None = Form(None),
    assigned_engineer: int | None = Form(None),
    document: UploadFile | None = File(None),
    qr_code: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if new_status not in STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid status")
    if not can_act_on(db, user, "installations", "can_edit", None):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot edit installation requests")

    try:
        parsed_ids = [int(raw.strip()) for raw in installation_ids.split(",") if raw.strip()]
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid installation id list")
    if not parsed_ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No installation requests selected")

    rows = [_load_visible(db, user, installation_id) for installation_id in parsed_ids]
    item_codes = {
        ((db.get(OrderItem, row.order_item_id).item_code if row.order_item_id else None) or "").strip() or "UNASSIGNED"
        for row in rows
    }
    if len(item_codes) > 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Bulk editing is allowed only within the same Item Code group")

    qr_blob = None
    qr_filename = None
    qr_content_type = None
    qr_size_bytes = None
    if qr_code is not None and qr_code.filename:
        qr_blob, qr_filename, qr_content_type, qr_size_bytes = await read_upload_bytes(qr_code)
    doc_path = None
    if document is not None and document.filename:
        doc_path = await save_upload(document, module="installations")

    updated: list[InstallationOut] = []
    for inst in rows:
        inst.status = _apply_payment_transition(
            inst,
            requested_status=new_status,
            actor=user,
            installation_date=installation_date,
            payment_amount=payment_amount,
            payment_type=payment_type,
            payment_qr_code_path=None,
            payment_qr_code_blob=qr_blob,
            payment_qr_code_filename=qr_filename,
            payment_qr_code_content_type=qr_content_type,
            payment_qr_code_size_bytes=qr_size_bytes,
        )
        if assigned_engineer is not None:
            inst.assigned_engineer = assigned_engineer
        if installation_date:
            inst.installation_date = datetime.fromisoformat(installation_date)
        if work_report is not None:
            inst.work_report = work_report
        if doc_path:
            if user.role in {"admin", "incool"} and (inst.status == "Payment Pending" or new_status == "Completed"):
                inst.payment_proof_file_path = doc_path
            else:
                inst.work_report_file_path = doc_path
        if settlement_approved_by is not None:
            inst.settlement_approved_by = settlement_approved_by
        if qr_blob:
            inst.payment_qr_code_blob = qr_blob
            inst.payment_qr_code_filename = qr_filename
            inst.payment_qr_code_content_type = qr_content_type
            inst.payment_qr_code_size_bytes = qr_size_bytes
            inst.payment_qr_code_path = None
        updated.append(InstallationOut(**_hydrate(db, inst)))

    if user.role in {"admin", "incool"} and new_status == "Completed":
        completed_rows = [inst for inst in rows if inst.status == "Completed" and inst.payment_recorded_at]
        if completed_rows:
            _create_payment_transaction(
                db,
                rows=completed_rows,
                actor=user,
                payment_type=completed_rows[0].payment_type_paid or completed_rows[0].payment_type_requested or "Cash",
            )

    db.commit()
    for inst in rows:
        db.refresh(inst)
    return [InstallationOut(**_hydrate(db, inst)) for inst in rows]


@router.delete("/{installation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_installation(
    installation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    inst = _load_visible(db, user, installation_id)
    if not can_act_on(db, user, "installations", "can_delete", None):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot delete this installation request")
    db.delete(inst)
    db.commit()
