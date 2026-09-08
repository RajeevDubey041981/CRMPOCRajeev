import json
import secrets
import time
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.complaint import Complaint, ComplaintStatusLog
from app.models.order import Order, OrderItem
from app.models.payment import PaymentTransaction
from app.models.service import (
    ServiceApproval,
    ServiceAssignment,
    ServiceCompletion,
    ServiceDocument,
    ServiceDocumentRule,
    ServiceObservation,
    ServicePaymentRequest,
    ServiceNotification,
    ServiceRequest,
    ServiceStatusLog,
)
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.serial import SerialLookup
from app.schemas.service import (
    SERVICE_STATUSES,
    ServiceApprovalIn,
    ServiceApprovalOut,
    ServiceAssignmentIn,
    ServiceAssignmentOut,
    ServiceCompletionIn,
    ServiceCompletionOut,
    ServiceCreate,
    ServiceDocumentOut,
    ServiceDocumentLinkOut,
    ServiceDocumentReviewIn,
    ServiceHistoryEntry,
    ServiceIdentifyCustomer,
    ServiceListItem,
    ServiceListResponse,
    ServiceObservationIn,
    ServiceObservationOut,
    ServiceOut,
    ServicePaymentRequestIn,
    ServicePaymentRequestOut,
    ServicePaymentCompleteIn,
    ServicePublicDocumentContext,
    ServiceSerialVerifyIn,
    ServiceSummary,
    ServiceUpdate,
)
from app.services.file_service import save_upload
from app.services.service_documents import (
    CUSTOMER_DOCUMENT_EXTENSIONS,
    CUSTOMER_DOCUMENT_MIME_TYPES,
    CUSTOMER_DOCUMENT_TYPES,
    build_public_upload_url,
)
from app.services.serial_history import EVENT_TYPES, create_serial_history_event

router = APIRouter(prefix="/api/services", tags=["services"])

SERVICE_STATUS_FLOW = {
    "New": {"Service Team Review", "Cancelled"},
    "Service Team Review": {"Assigned", "Cancelled", "Rejected"},
    "Assigned": {"Engineer Visit", "Cancelled", "Rejected"},
    "Engineer Visit": {"Serial Verified", "Cancelled"},
    "Serial Verified": {"Pending Service Approval", "Service In Progress"},
    "Pending Service Approval": {"Approved for Service", "Rejected"},
    "Approved for Service": {"Service In Progress", "Cancelled"},
    "Service In Progress": {"Service Completed", "Cancelled"},
    "Service Completed": {"Payment Requested", "Closed"},
    "Payment Requested": {"Payment Completed", "Closed"},
    "Payment Completed": {"Closed"},
    "Closed": set(),
    "Rejected": {"Assigned", "Cancelled"},
    "Cancelled": set(),
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _role(user: User) -> str:
    return (user.role or "").lower()


def _is_service_team(user: User) -> bool:
    return _role(user) in {"admin", "incool", "indcool service", "indcool_service"}


def _is_call_center(user: User) -> bool:
    return _role(user) in {"callcenter", "call center", "admin", "incool", "indcool service", "indcool_service"}


def _is_engineer(user: User) -> bool:
    return _role(user) == "engineer"


def _is_vendor(user: User) -> bool:
    return _role(user) == "vendor"


def _resolve_linked_complaint_from_service(db: Session, service: ServiceRequest, user: User, remark: str | None = None) -> None:
    if not service.complaint_id or service.status not in {"Payment Completed", "Closed"}:
        return
    complaint = db.get(Complaint, service.complaint_id)
    if complaint is None or complaint.status == "Resolved":
        return

    old_status = complaint.status
    complaint.status = "Resolved"
    complaint.status_date = _now()
    complaint.remark = remark or f"Auto resolved after service request {service.request_no} reached {service.status}."
    db.add(ComplaintStatusLog(
        complaint_id=complaint.id,
        old_status=old_status,
        new_status="Resolved",
        changed_by=user.id,
        remark=complaint.remark,
        action_taken="Service Request Completed",
    ))


def _generate_request_no() -> str:
    return f"SRV_{int(time.time() * 1000)}"


def _generate_access_token() -> str:
    return secrets.token_urlsafe(24)


def _json_load(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def _json_dump(value) -> str | None:
    if value in (None, "", [], {}):
        return None
    return json.dumps(value)


def _user_name(db: Session, user_id: int | None) -> str | None:
    if not user_id:
        return None
    user = db.get(User, user_id)
    return user.name if user else None


def _vendor_name(db: Session, vendor_id: int | None) -> str | None:
    if not vendor_id:
        return None
    vendor = db.get(Vendor, vendor_id)
    return vendor.name_of_firm if vendor else None


def _active_vendor_for_user(db: Session, user: User) -> Vendor | None:
    if not _is_vendor(user):
        return None
    return db.scalar(select(Vendor).where(Vendor.email == user.email))


def _service_visible_to_user(db: Session, service: ServiceRequest, user: User) -> bool:
    if _is_service_team(user) or _is_call_center(user):
        return True
    if _is_engineer(user):
        return service.assigned_engineer_id == user.id
    if _is_vendor(user):
        vendor = _active_vendor_for_user(db, user)
        return vendor is not None and service.assigned_vendor_id == vendor.id
    return False


def _load_visible_service(db: Session, service_id: int, user: User) -> ServiceRequest:
    service = db.get(ServiceRequest, service_id)
    if service is None or service.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Service request not found")
    if not _service_visible_to_user(db, service, user):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Service request not found")
    return service


def _count_service_documents(db: Session, service_id: int) -> int:
    return db.scalar(select(func.count()).select_from(ServiceDocument).where(ServiceDocument.service_request_id == service_id)) or 0


def _count_unread_notifications(db: Session, user: User) -> int:
    if not _is_service_team(user):
        return 0
    return db.scalar(
        select(func.count()).select_from(ServiceNotification).where(
            ServiceNotification.recipient_user_id == user.id,
            ServiceNotification.is_read == False,
        )
    ) or 0


def _find_order_item_by_serial(db: Session, serial_no: str) -> OrderItem | None:
    return db.scalar(
        select(OrderItem).where(
            or_(
                func.lower(func.coalesce(OrderItem.serial_no, "")) == func.lower(serial_no.strip()),
                func.lower(func.coalesce(OrderItem.serial_no_2, "")) == func.lower(serial_no.strip()),
            )
        )
    )


def _add_years(base_date: date | None, years: int | None) -> date | None:
    if base_date is None or years is None:
        return None
    try:
        return base_date.replace(year=base_date.year + years)
    except ValueError:
        return base_date.replace(month=2, day=28, year=base_date.year + years)


def _derive_service_context(db: Session, item: OrderItem | None):
    if item is None:
        return {"warranty_status": None, "service_type": None, "order": None}
    order = db.get(Order, item.order_id) if item.order_id else None
    warranty_base = None
    if order is not None:
        warranty_base = order.actual_delivery_date or order.expected_delivery_date or order.order_date
    machine_warranty_date = _add_years(warranty_base, item.machine_warranty_years)
    today = date.today()
    in_warranty = machine_warranty_date is not None and today <= machine_warranty_date
    warranty_status = "IN WARRANTY" if in_warranty else "OUT OF WARRANTY"
    if item.free_service_count and item.service_consume_count < item.free_service_count:
        service_type = "Free Service"
    elif in_warranty:
        service_type = "Warranty Service"
    else:
        service_type = "Paid Service"
    return {
        "warranty_status": warranty_status,
        "service_type": service_type,
        "order": order,
        "warranty_base": warranty_base,
        "pcb_warranty_date": _add_years(warranty_base, item.pcb_warranty_years),
        "component_warranty_date": _add_years(warranty_base, item.component_warranty_years),
        "machine_warranty_date": machine_warranty_date,
    }


def _required_documents(db: Session, service_type: str | None, warranty_status: str | None, query_type: str | None) -> list[str]:
    stmt = select(ServiceDocumentRule).where(ServiceDocumentRule.is_active == True, ServiceDocumentRule.is_required == True)
    rules = db.scalars(stmt).all()
    docs: list[str] = []
    for rule in rules:
        if rule.service_type and rule.service_type != service_type:
            continue
        if rule.warranty_status and rule.warranty_status != warranty_status:
            continue
        if rule.query_type and rule.query_type != query_type:
            continue
        docs.append(rule.document_type)
    if not docs and service_type in {"Warranty Service", "Paid Service"}:
        docs = ["Invoice Copy"]
        if service_type == "Warranty Service":
            docs.append("Warranty Proof")
    return docs


def _customer_document_types(db: Session, service: ServiceRequest) -> list[str]:
    configured = [doc for doc in _required_documents(db, service.service_type, service.warranty_status, service.query_type) if doc in CUSTOMER_DOCUMENT_TYPES]
    if configured:
        return configured
    return sorted(CUSTOMER_DOCUMENT_TYPES)


def _mark_service_notifications_read(db: Session, service: ServiceRequest, user: User) -> None:
    if not _is_service_team(user):
        return
    rows = db.scalars(
        select(ServiceNotification).where(
            ServiceNotification.service_request_id == service.id,
            ServiceNotification.recipient_user_id == user.id,
            ServiceNotification.is_read == False,
        )
    ).all()
    if not rows:
        return
    when = _now()
    for row in rows:
        row.is_read = True
        row.read_at = when


def _notify_service_team(db: Session, service: ServiceRequest, title: str, message: str, notification_type: str) -> None:
    users = db.scalars(select(User).where(User.is_active == True)).all()
    now = _now()
    for candidate in users:
        if _is_service_team(candidate):
            db.add(
                ServiceNotification(
                    service_request_id=service.id,
                    recipient_user_id=candidate.id,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    is_read=False,
                    created_at=now,
                    updated_at=now,
                )
            )


def _validate_customer_document_upload(document_type: str, file: UploadFile) -> None:
    if document_type not in CUSTOMER_DOCUMENT_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid customer document type")
    filename = (file.filename or "").lower()
    if not any(filename.endswith(ext) for ext in CUSTOMER_DOCUMENT_EXTENSIONS):
        if file.content_type not in CUSTOMER_DOCUMENT_MIME_TYPES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only PDF, JPG, JPEG, and PNG files are allowed")


def _send_document_link_email(service: ServiceRequest, upload_url: str) -> None:
    print(
        f"[service-doc-link] request={service.request_no} email={service.customer_email or ''} "
        f"url={upload_url}"
    )


def _log_status(
    db: Session,
    service: ServiceRequest,
    *,
    action: str,
    user: User,
    old_status: str | None,
    new_status: str | None,
    remarks: str | None = None,
    metadata: dict | None = None,
):
    log = ServiceStatusLog(
        service_request_id=service.id,
        action=action,
        old_status=old_status,
        new_status=new_status,
        performed_by=user.id,
        performed_role=user.role,
        remarks=remarks,
        metadata_json=_json_dump(metadata),
        created_at=_now(),
    )
    db.add(log)
    db.flush()


def _write_service_summary_to_serial_history(
    db: Session,
    service: ServiceRequest,
    completion: ServiceCompletion,
    user: User,
) -> None:
    if not service.serial_no:
        return
    latest_observation = db.scalar(
        select(ServiceObservation)
        .where(ServiceObservation.service_request_id == service.id)
        .order_by(desc(ServiceObservation.submitted_at))
    )
    problem = latest_observation.problem_found if latest_observation and latest_observation.problem_found else service.problem_description
    action = completion.work_performed or (latest_observation.recommended_action if latest_observation else None)
    parts = _json_load(completion.parts_replaced_json, [])
    if not parts and latest_observation:
        parts = _json_load(latest_observation.parts_required_json, [])
    summary_bits = []
    if problem:
        summary_bits.append(f"Problem: {problem}")
    if action:
        summary_bits.append(f"Final action: {action}")
    if parts:
        summary_bits.append(f"Parts replaced: {', '.join(parts)}")
    summary = ". ".join(summary_bits) or f"Service completed for request {service.request_no}"
    create_serial_history_event(
        db,
        serial_no=service.serial_no,
        order_item_id=service.order_item_id,
        event_type=EVENT_TYPES["SERVICE"],
        event_subtype="SERVICE_SUMMARY",
        event_at=completion.completed_at,
        performed_by_user_id=user.id,
        performed_by_name=user.name,
        source_table="service_requests",
        source_id=service.id,
        title="Service completed",
        description=summary,
        remarks=completion.completion_remarks or (latest_observation.remarks if latest_observation else None),
        metadata={
            "request_no": service.request_no,
            "status": service.status,
            "service_type": service.service_type,
            "warranty_status": service.warranty_status,
            "problem_found": problem,
            "final_action": action,
            "parts_replaced": parts,
            "proof_document": completion.customer_acknowledgement_path,
        },
    )


def _enforce_transition(current: str, new_status: str):
    if new_status not in SERVICE_STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid status")
    if new_status == current:
        return
    allowed = SERVICE_STATUS_FLOW.get(current, set())
    if new_status not in allowed:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Status transition from '{current}' to '{new_status}' is not allowed")


def _doc_out(db: Session, row: ServiceDocument) -> ServiceDocumentOut:
    return ServiceDocumentOut(
        id=row.id,
        document_type=row.document_type,
        file_path=row.file_path,
        uploaded_by_type=row.uploaded_by_type,
        uploaded_by_user_id=row.uploaded_by_user_id,
        uploaded_by_customer_name=row.uploaded_by_customer_name,
        status=row.status,
        reviewed_by=row.reviewed_by,
        reviewed_by_name=_user_name(db, row.reviewed_by),
        reviewed_at=row.reviewed_at,
        review_remarks=row.review_remarks,
        uploaded_at=row.uploaded_at,
    )


def _assignment_out(db: Session, row: ServiceAssignment) -> ServiceAssignmentOut:
    return ServiceAssignmentOut(
        id=row.id,
        assignee_type=row.assignee_type,
        assignee_user_id=row.assignee_user_id,
        assignee_user_name=_user_name(db, row.assignee_user_id),
        assignee_vendor_id=row.assignee_vendor_id,
        assignee_vendor_name=_vendor_name(db, row.assignee_vendor_id),
        assigned_by=row.assigned_by,
        assigned_by_name=_user_name(db, row.assigned_by),
        assigned_at=row.assigned_at,
        remarks=row.remarks,
        is_active=row.is_active,
    )


def _observation_out(db: Session, row: ServiceObservation) -> ServiceObservationOut:
    return ServiceObservationOut(
        id=row.id,
        submitted_by_user_id=row.submitted_by_user_id,
        submitted_by_name=_user_name(db, row.submitted_by_user_id),
        serial_no=row.serial_no,
        warranty_status=row.warranty_status,
        service_type=row.service_type,
        problem_found=row.problem_found,
        observation=row.observation,
        recommended_action=row.recommended_action,
        parts_required=_json_load(row.parts_required_json, []),
        estimated_service_charge=float(row.estimated_service_charge) if row.estimated_service_charge is not None else None,
        estimated_parts_charge=float(row.estimated_parts_charge) if row.estimated_parts_charge is not None else None,
        remarks=row.remarks,
        submitted_at=row.submitted_at,
    )


def _approval_out(db: Session, row: ServiceApproval) -> ServiceApprovalOut:
    return ServiceApprovalOut(
        id=row.id,
        observation_id=row.observation_id,
        decision=row.decision,
        remarks=row.remarks,
        approved_by=row.approved_by,
        approved_by_name=_user_name(db, row.approved_by),
        approved_at=row.approved_at,
    )


def _completion_out(db: Session, row: ServiceCompletion) -> ServiceCompletionOut:
    return ServiceCompletionOut(
        id=row.id,
        performed_by_type=row.performed_by_type,
        performed_by_user_id=row.performed_by_user_id,
        performed_by_name=_user_name(db, row.performed_by_user_id),
        performed_by_vendor_id=row.performed_by_vendor_id,
        performed_by_vendor_name=_vendor_name(db, row.performed_by_vendor_id),
        work_performed=row.work_performed,
        parts_replaced=_json_load(row.parts_replaced_json, []),
        service_notes=row.service_notes,
        service_date=row.service_date,
        old_part_serial_no=row.old_part_serial_no,
        new_part_serial_no=row.new_part_serial_no,
        customer_acknowledgement_path=row.customer_acknowledgement_path,
        final_amount=float(row.final_amount) if row.final_amount is not None else None,
        completion_remarks=row.completion_remarks,
        completed_at=row.completed_at,
    )


def _payment_out(db: Session, row: ServicePaymentRequest) -> ServicePaymentRequestOut:
    return ServicePaymentRequestOut(
        id=row.id,
        requested_by_type=row.requested_by_type,
        requested_by_user_id=row.requested_by_user_id,
        requested_by_name=_user_name(db, row.requested_by_user_id),
        requested_by_vendor_id=row.requested_by_vendor_id,
        requested_by_vendor_name=_vendor_name(db, row.requested_by_vendor_id),
        service_type=row.service_type,
        customer_charge_amount=float(row.customer_charge_amount) if row.customer_charge_amount is not None else None,
        settlement_service_amount=float(row.settlement_service_amount) if row.settlement_service_amount is not None else None,
        settlement_parts_amount=float(row.settlement_parts_amount) if row.settlement_parts_amount is not None else None,
        total_requested_amount=float(row.total_requested_amount) if row.total_requested_amount is not None else None,
        payment_type=row.payment_type,
        payment_qr_code_path=row.payment_qr_code_path,
        approved_amount=float(row.approved_amount) if row.approved_amount is not None else None,
        remarks=row.remarks,
        status=row.status,
        processed_at=row.processed_at,
        processed_by_user_id=row.processed_by_user_id,
        processed_by_name=_user_name(db, row.processed_by_user_id),
        payment_transaction_id=row.payment_transaction_id,
        created_at=row.created_at,
    )


def _hydrate_service(db: Session, service: ServiceRequest) -> ServiceOut:
    order = db.get(Order, service.order_id) if service.order_id else None
    order_item = db.get(OrderItem, service.order_item_id) if service.order_item_id else None
    serial_context = _derive_service_context(db, order_item) if order_item else {}
    documents = db.scalars(select(ServiceDocument).where(ServiceDocument.service_request_id == service.id).order_by(desc(ServiceDocument.uploaded_at))).all()
    assignments = db.scalars(select(ServiceAssignment).where(ServiceAssignment.service_request_id == service.id).order_by(desc(ServiceAssignment.assigned_at))).all()
    observations = db.scalars(select(ServiceObservation).where(ServiceObservation.service_request_id == service.id).order_by(desc(ServiceObservation.submitted_at))).all()
    approvals = db.scalars(select(ServiceApproval).where(ServiceApproval.service_request_id == service.id).order_by(desc(ServiceApproval.approved_at))).all()
    completions = db.scalars(select(ServiceCompletion).where(ServiceCompletion.service_request_id == service.id).order_by(desc(ServiceCompletion.completed_at))).all()
    payment_requests = db.scalars(select(ServicePaymentRequest).where(ServicePaymentRequest.service_request_id == service.id).order_by(desc(ServicePaymentRequest.created_at))).all()
    return ServiceOut(
        id=service.id,
        request_no=service.request_no,
        request_date=service.request_date,
        query_type=service.query_type,
        customer_name=service.customer_name,
        customer_mobile=service.customer_mobile,
        customer_email=service.customer_email,
        customer_address=service.customer_address,
        model_details=service.model_details,
        problem_description=service.problem_description,
        additional_remarks=service.additional_remarks,
        status=service.status,
        status_date=service.status_date,
        source=service.source,
        created_by=service.created_by,
        created_by_name=_user_name(db, service.created_by),
        complaint_id=service.complaint_id,
        order_id=service.order_id,
        order_item_id=service.order_item_id,
        order_no=order.order_no if order else None,
        serial_no=service.serial_no,
        pcb_warranty_date=serial_context.get("pcb_warranty_date"),
        component_warranty_date=serial_context.get("component_warranty_date"),
        machine_warranty_date=serial_context.get("machine_warranty_date"),
        service_type=service.service_type,
        warranty_status=service.warranty_status,
        assigned_engineer_id=service.assigned_engineer_id,
        assigned_engineer_name=_user_name(db, service.assigned_engineer_id),
        assigned_vendor_id=service.assigned_vendor_id,
        assigned_vendor_name=_vendor_name(db, service.assigned_vendor_id),
        requires_documents=service.requires_documents,
        ask_for_documents=service.ask_for_documents,
        document_request_sent_at=service.document_request_sent_at,
        document_access_token=service.document_access_token,
        customer_identified_at=service.customer_identified_at,
        approved_at=service.approved_at,
        completed_at=service.completed_at,
        closed_at=service.closed_at,
        created_at=service.created_at,
        updated_at=service.updated_at,
        documents=[_doc_out(db, row) for row in documents],
        assignments=[_assignment_out(db, row) for row in assignments],
        observations=[_observation_out(db, row) for row in observations],
        approvals=[_approval_out(db, row) for row in approvals],
        completions=[_completion_out(db, row) for row in completions],
        payment_requests=[_payment_out(db, row) for row in payment_requests],
    )


@router.get("/summary", response_model=ServiceSummary)
def service_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(ServiceRequest).where(ServiceRequest.deleted_at.is_(None))
    if _is_engineer(user):
        stmt = stmt.where(ServiceRequest.assigned_engineer_id == user.id)
    elif _is_vendor(user):
        vendor = _active_vendor_for_user(db, user)
        if vendor is None:
            return ServiceSummary(new_requests=0, unassigned=0, assigned=0, pending_observation=0, pending_approval=0, approved=0, in_progress=0, payment_pending=0, completed=0, closed=0, unread_notifications=0)
        stmt = stmt.where(ServiceRequest.assigned_vendor_id == vendor.id)
    def cnt(status_value: str) -> int:
        return db.scalar(select(func.count()).select_from(stmt.where(ServiceRequest.status == status_value).subquery())) or 0
    unassigned_stmt = select(func.count()).select_from(
        select(ServiceRequest).where(
            ServiceRequest.deleted_at.is_(None),
            ServiceRequest.assigned_engineer_id.is_(None),
            ServiceRequest.assigned_vendor_id.is_(None),
        ).subquery()
    )
    if _is_engineer(user) or _is_vendor(user):
        unassigned = 0
    else:
        unassigned = db.scalar(unassigned_stmt) or 0
    return ServiceSummary(
        new_requests=cnt("New"),
        unassigned=unassigned,
        assigned=cnt("Assigned"),
        pending_observation=cnt("Engineer Visit"),
        pending_approval=cnt("Pending Service Approval"),
        approved=cnt("Approved for Service"),
        in_progress=cnt("Service In Progress"),
        payment_pending=cnt("Payment Requested"),
        completed=cnt("Service Completed"),
        closed=cnt("Closed"),
        unread_notifications=_count_unread_notifications(db, user),
    )


@router.get("", response_model=ServiceListResponse)
def list_services(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
    search: str | None = None,
    status_filter: str | None = Query(None, alias="status"),
    service_type: str | None = None,
    engineer_id: int | None = None,
    vendor_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(ServiceRequest).where(ServiceRequest.deleted_at.is_(None))
    if _is_engineer(user):
        stmt = stmt.where(ServiceRequest.assigned_engineer_id == user.id)
    elif _is_vendor(user):
        vendor = _active_vendor_for_user(db, user)
        if vendor is None:
            return ServiceListResponse(items=[], total=0, page=page, per_page=per_page)
        stmt = stmt.where(ServiceRequest.assigned_vendor_id == vendor.id)
    elif not (_is_service_team(user) or _is_call_center(user)):
        return ServiceListResponse(items=[], total=0, page=page, per_page=per_page)
    if status_filter:
        stmt = stmt.where(ServiceRequest.status == status_filter)
    if service_type:
        stmt = stmt.where(ServiceRequest.service_type == service_type)
    if engineer_id:
        stmt = stmt.where(ServiceRequest.assigned_engineer_id == engineer_id)
    if vendor_id:
        stmt = stmt.where(ServiceRequest.assigned_vendor_id == vendor_id)
    if date_from:
        stmt = stmt.where(ServiceRequest.request_date >= date_from)
    if date_to:
        stmt = stmt.where(ServiceRequest.request_date <= date_to)
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                ServiceRequest.request_no.ilike(like),
                ServiceRequest.customer_name.ilike(like),
                ServiceRequest.customer_mobile.ilike(like),
                ServiceRequest.serial_no.ilike(like),
            )
        )
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.order_by(desc(ServiceRequest.created_at)).offset((page - 1) * per_page).limit(per_page)).all()
    items: list[ServiceListItem] = []
    for row in rows:
        order = db.get(Order, row.order_id) if row.order_id else None
        items.append(
            ServiceListItem(
                id=row.id,
                request_no=row.request_no,
                request_date=row.request_date,
                customer_name=row.customer_name,
                customer_mobile=row.customer_mobile,
                order_no=order.order_no if order else None,
                serial_no=row.serial_no,
                status=row.status,
                service_type=row.service_type,
                warranty_status=row.warranty_status,
                assigned_engineer_name=_user_name(db, row.assigned_engineer_id),
                assigned_vendor_name=_vendor_name(db, row.assigned_vendor_id),
                requires_documents=row.requires_documents,
                document_count=_count_service_documents(db, row.id),
                created_at=row.created_at,
            )
        )
    return ServiceListResponse(items=items, total=total, page=page, per_page=per_page)


@router.post("", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def create_service(body: ServiceCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not _is_call_center(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot create service requests")
    service = ServiceRequest(
        request_no=_generate_request_no(),
        request_date=body.request_date or date.today(),
        query_type=body.query_type,
        customer_name=body.customer_name,
        customer_mobile=body.customer_mobile,
        customer_email=body.customer_email,
        customer_address=body.customer_address,
        model_details=body.model_details,
        problem_description=body.problem_description,
        additional_remarks=body.additional_remarks,
        status="New",
        status_date=_now(),
        source="callcenter",
        created_by=user.id,
        document_access_token=_generate_access_token(),
    )
    docs = _required_documents(db, service.service_type, service.warranty_status, service.query_type)
    service.requires_documents = bool(docs)
    service.ask_for_documents = bool(docs)
    if docs:
        service.document_request_sent_at = _now()
    db.add(service)
    db.flush()
    _log_status(db, service, action="Request Created", user=user, old_status=None, new_status="New", remarks=body.additional_remarks, metadata={"requested_documents": docs})
    db.commit()
    db.refresh(service)
    return _hydrate_service(db, service)


@router.get("/lookup/engineers")
def engineer_lookup(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not (_is_service_team(user) or _is_call_center(user)):
        return []
    rows = db.scalars(select(User).where(User.deleted_at.is_(None), User.is_active == True, func.lower(User.role) == "engineer").order_by(User.name)).all()
    return [{"id": row.id, "name": row.name, "email": row.email, "phone": row.phone} for row in rows]


@router.get("/lookup/vendors")
def vendor_lookup(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not (_is_service_team(user) or _is_call_center(user)):
        return []
    rows = db.scalars(select(Vendor).where(Vendor.deleted_at.is_(None), Vendor.is_active == True).order_by(Vendor.name_of_firm)).all()
    return [{"id": row.id, "name": row.name_of_firm, "email": row.email, "phone": row.contact_mobile} for row in rows]


@router.get("/customers/search")
def customer_search(
    mobile: str | None = None,
    name: str | None = None,
    order_no: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not (_is_service_team(user) or _is_call_center(user)):
        return []
    seen: set[tuple] = set()
    results: list[dict] = []

    def add_result(payload: dict) -> None:
        key = (
            (payload.get("customer_name") or "").strip().lower(),
            (payload.get("customer_mobile") or "").strip(),
            payload.get("order_id"),
        )
        if key in seen:
            return
        seen.add(key)
        results.append(payload)

    stmt = select(Order).where(Order.deleted_at.is_(None))
    order_terms = []
    if mobile and mobile.strip():
        order_terms.append(Order.customer_contact.ilike(f"%{mobile.strip()}%"))
    if name and name.strip():
        order_terms.append(Order.customer_name.ilike(f"%{name.strip()}%"))
    if order_no and order_no.strip():
        order_terms.append(Order.order_no.ilike(f"%{order_no.strip()}%"))
    if order_terms:
        stmt = stmt.where(or_(*order_terms))
    rows = db.scalars(stmt.order_by(desc(Order.created_at)).limit(20)).all()
    for row in rows:
        add_result({
            "order_id": row.id,
            "order_no": row.order_no,
            "customer_name": row.customer_name,
            "customer_mobile": row.customer_contact,
            "customer_email": row.customer_email,
            "customer_address": row.customer_address,
            "source_type": "order",
        })

    complaint_stmt = select(Complaint).where(Complaint.deleted_at.is_(None))
    complaint_terms = []
    if mobile and mobile.strip():
        complaint_terms.append(Complaint.customer_mobile.ilike(f"%{mobile.strip()}%"))
    if name and name.strip():
        complaint_terms.append(Complaint.customer_name.ilike(f"%{name.strip()}%"))
    if complaint_terms:
        complaint_stmt = complaint_stmt.where(or_(*complaint_terms))
    complaint_rows = db.scalars(complaint_stmt.order_by(desc(Complaint.created_at)).limit(20)).all()
    for row in complaint_rows:
        add_result({
            "order_id": None,
            "order_no": None,
            "customer_name": row.customer_name,
            "customer_mobile": row.customer_mobile,
            "customer_email": row.customer_email,
            "customer_address": row.customer_address,
            "source_type": "complaint",
        })
    return results[:20]


@router.get("/{service_id}", response_model=ServiceOut)
def get_service(service_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = _load_visible_service(db, service_id, user)
    _mark_service_notifications_read(db, service, user)
    db.commit()
    return _hydrate_service(db, service)


@router.put("/{service_id}", response_model=ServiceOut)
def update_service(service_id: int, body: ServiceUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = _load_visible_service(db, service_id, user)
    if not (_is_service_team(user) or (_is_call_center(user) and service.created_by == user.id)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot update this service request")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(service, field, value)
    db.commit()
    db.refresh(service)
    return _hydrate_service(db, service)


@router.post("/{service_id}/identify-customer", response_model=ServiceOut)
def identify_customer(service_id: int, body: ServiceIdentifyCustomer, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = _load_visible_service(db, service_id, user)
    if not _is_service_team(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only Indcool Service can identify customer context")
    order = db.get(Order, body.order_id) if body.order_id else None
    item = db.get(OrderItem, body.order_item_id) if body.order_item_id else None
    if item and order is None:
        order = db.get(Order, item.order_id)
    if item and order and item.order_id != order.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Order item does not belong to selected order")
    if order:
        service.order_id = order.id
        service.customer_name = order.customer_name or service.customer_name
        service.customer_mobile = order.customer_contact or service.customer_mobile
        service.customer_email = order.customer_email or service.customer_email
        service.customer_address = order.customer_address or service.customer_address
    elif any([body.customer_name, body.customer_mobile, body.customer_email, body.customer_address]):
        service.customer_name = body.customer_name or service.customer_name
        service.customer_mobile = body.customer_mobile or service.customer_mobile
        service.customer_email = body.customer_email or service.customer_email
        service.customer_address = body.customer_address or service.customer_address
    if item:
        service.order_item_id = item.id
        if not service.serial_no:
            service.serial_no = item.serial_no or item.serial_no_2
        context = _derive_service_context(db, item)
        service.warranty_status = context["warranty_status"]
        service.service_type = context["service_type"]
        docs = _required_documents(db, service.service_type, service.warranty_status, service.query_type)
        service.requires_documents = bool(docs)
        service.ask_for_documents = bool(docs)
    old_status = service.status
    if service.status == "New":
        service.status = "Service Team Review"
        service.status_date = _now()
    service.customer_identified_at = _now()
    _log_status(db, service, action="Customer Identified", user=user, old_status=old_status, new_status=service.status, metadata={"order_id": service.order_id, "order_item_id": service.order_item_id})
    db.commit()
    db.refresh(service)
    return _hydrate_service(db, service)


@router.post("/{service_id}/assign", response_model=ServiceOut)
def assign_service(service_id: int, body: ServiceAssignmentIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = _load_visible_service(db, service_id, user)
    if not _is_service_team(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only Indcool Service can assign requests")
    active_assignment = db.scalar(
        select(ServiceAssignment)
        .where(ServiceAssignment.service_request_id == service.id, ServiceAssignment.is_active == True)
        .order_by(desc(ServiceAssignment.assigned_at))
    )
    if active_assignment is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This request is already assigned. Cancel the current assignment before reassigning.")
    old_status = service.status
    if body.assignee_type == "engineer":
        engineer = db.get(User, body.assignee_id)
        if engineer is None or engineer.deleted_at is not None or not engineer.is_active or _role(engineer) != "engineer":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Selected engineer is not active")
        service.assigned_engineer_id = engineer.id
        service.assigned_vendor_id = None
    else:
        vendor = db.get(Vendor, body.assignee_id)
        if vendor is None or vendor.deleted_at is not None or not vendor.is_active:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Selected vendor is not active")
        service.assigned_vendor_id = vendor.id
        service.assigned_engineer_id = None
    db.query(ServiceAssignment).filter(ServiceAssignment.service_request_id == service.id, ServiceAssignment.is_active == True).update({ServiceAssignment.is_active: False}, synchronize_session=False)
    db.add(
        ServiceAssignment(
            service_request_id=service.id,
            assignee_type=body.assignee_type,
            assignee_user_id=service.assigned_engineer_id if body.assignee_type == "engineer" else None,
            assignee_vendor_id=service.assigned_vendor_id if body.assignee_type == "vendor" else None,
            assigned_by=user.id,
            assigned_at=_now(),
            remarks=body.remarks,
            is_active=True,
        )
    )
    if service.status in {"New", "Service Team Review", "Rejected"}:
        service.status = "Assigned"
        service.status_date = _now()
    _log_status(db, service, action="Assigned", user=user, old_status=old_status, new_status=service.status, remarks=body.remarks, metadata={"assignee_type": body.assignee_type, "assignee_id": body.assignee_id})
    db.commit()
    db.refresh(service)
    return _hydrate_service(db, service)


@router.post("/{service_id}/assignment-cancel", response_model=ServiceOut)
def cancel_assignment(service_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = _load_visible_service(db, service_id, user)
    vendor = _active_vendor_for_user(db, user) if _is_vendor(user) else None
    if not _is_service_team(user):
        if _is_engineer(user):
            if service.assigned_engineer_id != user.id:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "This request is not assigned to you")
        elif _is_vendor(user):
            if vendor is None or service.assigned_vendor_id != vendor.id:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "This request is not assigned to your vendor")
        else:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot cancel assignments")

    active_assignments = db.scalars(
        select(ServiceAssignment).where(
            ServiceAssignment.service_request_id == service.id,
            ServiceAssignment.is_active == True,
        )
    ).all()
    if not active_assignments and service.assigned_engineer_id is None and service.assigned_vendor_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This request does not have an active assignment")

    for assignment in active_assignments:
        assignment.is_active = False

    old_status = service.status
    service.assigned_engineer_id = None
    service.assigned_vendor_id = None
    service.status = "Service Team Review"
    service.status_date = _now()
    _log_status(
        db,
        service,
        action="Assignment Cancelled",
        user=user,
        old_status=old_status,
        new_status=service.status,
    )
    db.commit()
    db.refresh(service)
    return _hydrate_service(db, service)


@router.post("/{service_id}/verify-serial", response_model=ServiceOut)
def verify_serial(service_id: int, body: ServiceSerialVerifyIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = _load_visible_service(db, service_id, user)
    if not (_is_engineer(user) or _is_vendor(user) or _is_service_team(user)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot verify serials")
    if _is_engineer(user) and service.assigned_engineer_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This request is not assigned to you")
    if _is_vendor(user):
        vendor = _active_vendor_for_user(db, user)
        if vendor is None or service.assigned_vendor_id != vendor.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This request is not assigned to your vendor")
    item = _find_order_item_by_serial(db, body.serial_no)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Serial number not found")
    context = _derive_service_context(db, item)
    order = context["order"]
    service.serial_no = body.serial_no.strip()
    service.order_item_id = item.id
    service.order_id = order.id if order else service.order_id
    service.warranty_status = context["warranty_status"]
    service.service_type = context["service_type"]
    docs = _required_documents(db, service.service_type, service.warranty_status, service.query_type)
    service.requires_documents = bool(docs)
    service.ask_for_documents = bool(docs)
    old_status = service.status
    if service.status in {"Assigned", "Engineer Visit"}:
        service.status = "Serial Verified"
        service.status_date = _now()
    _log_status(db, service, action="Serial Verified", user=user, old_status=old_status, new_status=service.status, metadata={"serial_no": service.serial_no, "service_type": service.service_type, "warranty_status": service.warranty_status})
    db.commit()
    db.refresh(service)
    return _hydrate_service(db, service)


@router.post("/{service_id}/observations", response_model=ServiceOut)
def submit_observation(service_id: int, body: ServiceObservationIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = _load_visible_service(db, service_id, user)
    if not (_is_engineer(user) or _is_vendor(user)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only engineer or vendor can submit observation")
    if _is_engineer(user) and service.assigned_engineer_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This request is not assigned to you")
    if _is_vendor(user):
        vendor = _active_vendor_for_user(db, user)
        if vendor is None or service.assigned_vendor_id != vendor.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This request is not assigned to your vendor")
    if service.status == "Pending Service Approval":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Observation is already submitted. Cancel it before submitting again.")
    observation = ServiceObservation(
        service_request_id=service.id,
        submitted_by_user_id=user.id,
        serial_no=service.serial_no,
        warranty_status=service.warranty_status,
        service_type=service.service_type,
        problem_found=body.problem_found,
        observation=body.observation,
        recommended_action=body.recommended_action,
        parts_required_json=_json_dump(body.parts_required),
        estimated_service_charge=body.estimated_service_charge,
        estimated_parts_charge=body.estimated_parts_charge,
        remarks=body.remarks,
        submitted_at=_now(),
    )
    db.add(observation)
    old_status = service.status
    service.status = "Pending Service Approval"
    service.status_date = _now()
    _log_status(db, service, action="Observation Submitted", user=user, old_status=old_status, new_status=service.status, remarks=body.remarks)
    db.commit()
    db.refresh(service)
    return _hydrate_service(db, service)


@router.post("/{service_id}/observations/cancel", response_model=ServiceOut)
def cancel_observation(service_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = _load_visible_service(db, service_id, user)
    if not (_is_engineer(user) or _is_vendor(user) or _is_service_team(user)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot cancel observations")
    if _is_engineer(user) and service.assigned_engineer_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This request is not assigned to you")
    if _is_vendor(user):
        vendor = _active_vendor_for_user(db, user)
        if vendor is None or service.assigned_vendor_id != vendor.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This request is not assigned to your vendor")
    if service.status != "Pending Service Approval":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only pending observations can be cancelled")

    latest_observation = db.scalar(
        select(ServiceObservation)
        .where(ServiceObservation.service_request_id == service.id)
        .order_by(desc(ServiceObservation.submitted_at))
    )
    if latest_observation is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No observation found to cancel")

    linked_approval = db.scalar(select(ServiceApproval).where(ServiceApproval.observation_id == latest_observation.id))
    if linked_approval is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Observation already has an approval decision")

    db.delete(latest_observation)
    old_status = service.status
    service.status = "Serial Verified"
    service.status_date = _now()
    _log_status(
        db,
        service,
        action="Observation Cancelled",
        user=user,
        old_status=old_status,
        new_status=service.status,
    )
    db.commit()
    db.refresh(service)
    return _hydrate_service(db, service)


@router.post("/{service_id}/approval", response_model=ServiceOut)
def service_approval(service_id: int, body: ServiceApprovalIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = _load_visible_service(db, service_id, user)
    if not _is_service_team(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only Indcool Service can approve service")
    if service.status != "Pending Service Approval":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Approval is enabled only after observation is submitted")
    if body.decision == "Reject" and not body.remarks:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Remarks are mandatory when rejecting")
    latest_observation = db.scalar(
        select(ServiceObservation)
        .where(ServiceObservation.service_request_id == service.id)
        .order_by(desc(ServiceObservation.submitted_at))
    )
    approval = ServiceApproval(
        service_request_id=service.id,
        observation_id=latest_observation.id if latest_observation else None,
        decision=body.decision,
        remarks=body.remarks,
        approved_by=user.id,
        approved_at=_now(),
    )
    db.add(approval)
    old_status = service.status
    service.status = "Approved for Service" if body.decision == "Approve" else "Rejected"
    service.status_date = _now()
    if body.decision == "Approve":
        service.approved_at = _now()
    _log_status(db, service, action="Service Approved" if body.decision == "Approve" else "Service Rejected", user=user, old_status=old_status, new_status=service.status, remarks=body.remarks)
    db.commit()
    db.refresh(service)
    return _hydrate_service(db, service)


@router.post("/{service_id}/approval/cancel", response_model=ServiceOut)
def cancel_service_approval(service_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = _load_visible_service(db, service_id, user)
    if not _is_service_team(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only Indcool Service can cancel approval")
    if service.status not in {"Approved for Service", "Rejected"}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only the current approval decision can be cancelled")

    latest_approval = db.scalar(
        select(ServiceApproval)
        .where(ServiceApproval.service_request_id == service.id)
        .order_by(desc(ServiceApproval.approved_at))
    )
    if latest_approval is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No approval decision found to cancel")

    db.delete(latest_approval)
    old_status = service.status
    service.status = "Pending Service Approval"
    service.status_date = _now()
    service.approved_at = None
    _log_status(db, service, action="Approval Cancelled", user=user, old_status=old_status, new_status=service.status)
    db.commit()
    db.refresh(service)
    return _hydrate_service(db, service)


@router.post("/{service_id}/completion", response_model=ServiceOut)
async def complete_service(
    service_id: int,
    work_performed: str | None = Form(None),
    parts_replaced: str | None = Form(None),
    service_notes: str | None = Form(None),
    service_date: date | None = Form(None),
    old_part_serial_no: str | None = Form(None),
    new_part_serial_no: str | None = Form(None),
    final_amount: float | None = Form(None),
    completion_remarks: str | None = Form(None),
    proof_document: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = _load_visible_service(db, service_id, user)
    if not (_is_engineer(user) or _is_vendor(user)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only engineer or vendor can complete service")
    if _is_engineer(user) and service.assigned_engineer_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This request is not assigned to you")
    if _is_vendor(user):
        vendor = _active_vendor_for_user(db, user)
        if vendor is None or service.assigned_vendor_id != vendor.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This request is not assigned to your vendor")
    if service.status not in {"Approved for Service", "Service In Progress"}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Service can be completed only after approval")
    if proof_document is None or not proof_document.filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Completion proof document is required")
    proof_path = await save_upload(proof_document, module="services")
    completion = ServiceCompletion(
        service_request_id=service.id,
        performed_by_type="engineer" if _is_engineer(user) else "vendor",
        performed_by_user_id=user.id if _is_engineer(user) else None,
        performed_by_vendor_id=service.assigned_vendor_id if _is_vendor(user) else None,
        work_performed=work_performed,
        parts_replaced_json=_json_dump(_json_load(parts_replaced, [])),
        service_notes=service_notes,
        service_date=service_date or date.today(),
        old_part_serial_no=old_part_serial_no,
        new_part_serial_no=new_part_serial_no,
        customer_acknowledgement_path=proof_path,
        final_amount=final_amount,
        completion_remarks=completion_remarks,
        completed_at=_now(),
    )
    db.add(completion)
    old_status = service.status
    service.status = "Service Completed"
    service.status_date = _now()
    service.completed_at = _now()
    if service.order_item_id:
        item = db.get(OrderItem, service.order_item_id)
        if item is not None and service.service_type == "Free Service":
            item.service_consume_count = (item.service_consume_count or 0) + 1
    _log_status(
        db,
        service,
        action="Service Completed",
        user=user,
        old_status=old_status,
        new_status=service.status,
        remarks=completion_remarks,
        metadata={"proof_document": proof_path},
    )
    _write_service_summary_to_serial_history(db, service, completion, user)
    db.commit()
    db.refresh(service)
    return _hydrate_service(db, service)


@router.post("/{service_id}/completion/cancel", response_model=ServiceOut)
def cancel_service_completion(service_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = _load_visible_service(db, service_id, user)
    if not (_is_engineer(user) or _is_vendor(user) or _is_service_team(user)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot cancel service completion")
    if _is_engineer(user) and service.assigned_engineer_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This request is not assigned to you")
    if _is_vendor(user):
        vendor = _active_vendor_for_user(db, user)
        if vendor is None or service.assigned_vendor_id != vendor.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This request is not assigned to your vendor")
    if service.status != "Service Completed":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cancel payment request before cancelling completion")

    latest_completion = db.scalar(
        select(ServiceCompletion)
        .where(ServiceCompletion.service_request_id == service.id)
        .order_by(desc(ServiceCompletion.completed_at))
    )
    if latest_completion is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No completion found to cancel")

    db.delete(latest_completion)
    old_status = service.status
    service.status = "Approved for Service"
    service.status_date = _now()
    service.completed_at = None
    if service.order_item_id:
        item = db.get(OrderItem, service.order_item_id)
        if item is not None and service.service_type == "Free Service" and (item.service_consume_count or 0) > 0:
            item.service_consume_count = (item.service_consume_count or 0) - 1
    _log_status(db, service, action="Completion Cancelled", user=user, old_status=old_status, new_status=service.status)
    db.commit()
    db.refresh(service)
    return _hydrate_service(db, service)


@router.post("/{service_id}/payment-request", response_model=ServiceOut)
async def raise_payment_request(
    service_id: int,
    customer_charge_amount: float | None = Form(None),
    settlement_service_amount: float | None = Form(None),
    settlement_parts_amount: float | None = Form(None),
    total_requested_amount: float | None = Form(None),
    payment_type: str | None = Form(None),
    remarks: str | None = Form(None),
    qr_code: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = _load_visible_service(db, service_id, user)
    if not (_is_engineer(user) or _is_vendor(user) or _is_service_team(user)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot raise payment request")
    if _is_engineer(user) and service.assigned_engineer_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This request is not assigned to you")
    if _is_vendor(user):
        vendor = _active_vendor_for_user(db, user)
        if vendor is None or service.assigned_vendor_id != vendor.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This request is not assigned to your vendor")
    if service.status != "Service Completed":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Payment request is enabled only after service completion")
    normalized_payment_type = (payment_type or "").strip()
    if normalized_payment_type not in {"Cash", "UPI"}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Payment type must be Cash or UPI")
    if normalized_payment_type == "UPI" and (qr_code is None or not qr_code.filename):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "QR Code is required when payment type is UPI")
    qr_path = None
    if qr_code is not None and qr_code.filename:
        qr_path = await save_upload(qr_code, module="services")
    requested_by_type = "service_team" if _is_service_team(user) else "engineer" if _is_engineer(user) else "vendor"
    payment_request = ServicePaymentRequest(
        service_request_id=service.id,
        requested_by_type=requested_by_type,
        requested_by_user_id=user.id if requested_by_type != "vendor" else None,
        requested_by_vendor_id=service.assigned_vendor_id if requested_by_type == "vendor" else None,
        service_type=service.service_type,
        customer_charge_amount=customer_charge_amount,
        settlement_service_amount=settlement_service_amount,
        settlement_parts_amount=settlement_parts_amount,
        total_requested_amount=total_requested_amount,
        payment_type=normalized_payment_type,
        payment_qr_code_path=qr_path,
        remarks=remarks,
        status="Requested",
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(payment_request)
    old_status = service.status
    service.status = "Payment Requested"
    service.status_date = _now()
    _log_status(
        db,
        service,
        action="Payment Requested",
        user=user,
        old_status=old_status,
        new_status=service.status,
        remarks=remarks,
        metadata={"payment_type": normalized_payment_type, "payment_qr_code_path": qr_path},
    )
    db.commit()
    db.refresh(service)
    return _hydrate_service(db, service)


@router.post("/{service_id}/payment-request/cancel", response_model=ServiceOut)
def cancel_payment_request(service_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = _load_visible_service(db, service_id, user)
    if not (_is_engineer(user) or _is_vendor(user) or _is_service_team(user)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot cancel payment request")
    if _is_engineer(user) and service.assigned_engineer_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This request is not assigned to you")
    if _is_vendor(user):
        vendor = _active_vendor_for_user(db, user)
        if vendor is None or service.assigned_vendor_id != vendor.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This request is not assigned to your vendor")
    if service.status != "Payment Requested":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only active payment requests can be cancelled")

    latest_payment = db.scalar(
        select(ServicePaymentRequest)
        .where(ServicePaymentRequest.service_request_id == service.id)
        .order_by(desc(ServicePaymentRequest.created_at))
    )
    if latest_payment is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No payment request found to cancel")

    db.delete(latest_payment)
    old_status = service.status
    service.status = "Service Completed"
    service.status_date = _now()
    _log_status(db, service, action="Payment Request Cancelled", user=user, old_status=old_status, new_status=service.status)
    db.commit()
    db.refresh(service)
    return _hydrate_service(db, service)


@router.post("/{service_id}/payment-approval", response_model=ServiceOut)
def approve_service_payment(service_id: int, body: ServicePaymentCompleteIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = _load_visible_service(db, service_id, user)
    if not _is_service_team(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only Indcool Service can approve payment")
    if service.status != "Payment Requested":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Payment can be approved only after a payment request is raised")
    if body.approved_amount < 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Approved amount cannot be negative")

    latest_payment = db.scalar(
        select(ServicePaymentRequest)
        .where(ServicePaymentRequest.service_request_id == service.id)
        .order_by(desc(ServicePaymentRequest.created_at))
    )
    if latest_payment is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No payment request found to approve")

    payment_type = body.payment_type or latest_payment.payment_type or "Cash"
    if payment_type == "UPI" and not latest_payment.payment_qr_code_path:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "QR Code is required before approving UPI payment")

    transaction = PaymentTransaction(
        payment_type=payment_type,
        total_amount=body.approved_amount,
        request_count=1,
        recorded_by_user_id=user.id,
        engineer_user_id=service.assigned_engineer_id,
    )
    db.add(transaction)
    db.flush()

    latest_payment.status = "Processed"
    latest_payment.approved_amount = body.approved_amount
    latest_payment.processed_at = _now()
    latest_payment.processed_by_user_id = user.id
    latest_payment.payment_transaction_id = transaction.id
    latest_payment.updated_at = _now()
    if body.remarks:
        latest_payment.remarks = body.remarks

    old_status = service.status
    service.status = "Payment Completed"
    service.status_date = _now()
    _log_status(
        db,
        service,
        action="Payment Approved",
        user=user,
        old_status=old_status,
        new_status=service.status,
        remarks=body.remarks,
        metadata={"payment_request_id": latest_payment.id, "approved_amount": body.approved_amount, "payment_transaction_id": transaction.id},
    )
    _resolve_linked_complaint_from_service(db, service, user, body.remarks)
    db.commit()
    db.refresh(service)
    return _hydrate_service(db, service)


@router.post("/{service_id}/status", response_model=ServiceOut)
def update_service_status(service_id: int, new_status: str = Form(...), remarks: str | None = Form(None), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = _load_visible_service(db, service_id, user)
    _enforce_transition(service.status, new_status)
    old_status = service.status
    service.status = new_status
    service.status_date = _now()
    if new_status == "Closed":
        service.closed_at = _now()
    _log_status(db, service, action="Status Changed", user=user, old_status=old_status, new_status=new_status, remarks=remarks)
    _resolve_linked_complaint_from_service(db, service, user, remarks)
    db.commit()
    db.refresh(service)
    return _hydrate_service(db, service)


@router.get("/{service_id}/history", response_model=list[ServiceHistoryEntry])
def service_history(service_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = _load_visible_service(db, service_id, user)
    rows = db.scalars(select(ServiceStatusLog).where(ServiceStatusLog.service_request_id == service.id).order_by(desc(ServiceStatusLog.created_at))).all()
    return [
        ServiceHistoryEntry(
            id=row.id,
            action=row.action,
            old_status=row.old_status,
            new_status=row.new_status,
            performed_by=row.performed_by,
            performed_by_name=_user_name(db, row.performed_by),
            performed_role=row.performed_role,
            remarks=row.remarks,
            metadata=_json_load(row.metadata_json, None),
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/{service_id}/documents", response_model=list[ServiceDocumentOut])
def list_documents(service_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = _load_visible_service(db, service_id, user)
    rows = db.scalars(select(ServiceDocument).where(ServiceDocument.service_request_id == service.id).order_by(desc(ServiceDocument.uploaded_at))).all()
    return [_doc_out(db, row) for row in rows]


@router.post("/{service_id}/documents/upload", response_model=ServiceOut)
async def upload_document(
    service_id: int,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = _load_visible_service(db, service_id, user)
    if _is_vendor(user) or _is_call_center(user) or _is_engineer(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Use the customer document link flow for customer documents")
    path = await save_upload(file, module="services")
    row = ServiceDocument(
        service_request_id=service.id,
        document_type=document_type,
        file_path=path,
        uploaded_by_type=_role(user),
        uploaded_by_user_id=user.id,
        uploaded_by_customer_name=None,
        status="Uploaded",
        uploaded_at=_now(),
    )
    db.add(row)
    _log_status(db, service, action="Document Uploaded", user=user, old_status=service.status, new_status=service.status, metadata={"document_type": document_type, "file_path": path})
    db.commit()
    db.refresh(service)
    return _hydrate_service(db, service)


@router.post("/{service_id}/documents/{document_id}/review", response_model=ServiceOut)
def review_document(service_id: int, document_id: int, body: ServiceDocumentReviewIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = _load_visible_service(db, service_id, user)
    if not _is_service_team(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only Indcool Service can review documents")
    document = db.get(ServiceDocument, document_id)
    if document is None or document.service_request_id != service.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    document.status = body.status
    document.reviewed_by = user.id
    document.reviewed_at = _now()
    document.review_remarks = body.remarks
    _log_status(db, service, action="Document Reviewed", user=user, old_status=service.status, new_status=service.status, remarks=body.remarks, metadata={"document_id": document_id, "document_status": body.status})
    db.commit()
    db.refresh(service)
    return _hydrate_service(db, service)


@router.post("/{service_id}/documents/request-link", response_model=ServiceDocumentLinkOut)
def request_documents(service_id: int, request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    service = _load_visible_service(db, service_id, user)
    if not _is_service_team(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only Indcool Service can request documents")
    if not service.customer_email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Customer email is required before sending document upload link")
    service.document_access_token = _generate_access_token()
    service.ask_for_documents = True
    service.document_request_sent_at = _now()
    upload_url = build_public_upload_url(service.document_access_token)
    _send_document_link_email(service, upload_url)
    _log_status(
        db,
        service,
        action="Documents Requested",
        user=user,
        old_status=service.status,
        new_status=service.status,
        metadata={
            "upload_url": upload_url,
            "required_documents": _customer_document_types(db, service),
            "requested_by_host": str(request.base_url).rstrip("/"),
        },
    )
    db.commit()
    return ServiceDocumentLinkOut(
        service_request_id=service.id,
        upload_url=upload_url,
        customer_email=service.customer_email,
        document_request_sent_at=service.document_request_sent_at,
        status=service.status,
    )


@router.get("/public/{token}", response_model=ServicePublicDocumentContext)
def public_upload_context(token: str, db: Session = Depends(get_db)):
    service = db.scalar(select(ServiceRequest).where(ServiceRequest.document_access_token == token, ServiceRequest.deleted_at.is_(None)))
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Upload link not found")
    order = db.get(Order, service.order_id) if service.order_id else None
    return ServicePublicDocumentContext(
        service_request_id=service.id,
        request_no=service.request_no,
        customer_name=service.customer_name,
        customer_email=service.customer_email,
        model_details=service.model_details,
        order_no=order.order_no if order else None,
        serial_no=service.serial_no,
        problem_description=service.problem_description,
        required_documents=_customer_document_types(db, service),
        status=service.status,
    )


@router.post("/public/{token}/upload", response_model=dict)
async def public_upload(token: str, document_type: str = Form(...), customer_name: str | None = Form(None), file: UploadFile = File(...), db: Session = Depends(get_db)):
    service = db.scalar(select(ServiceRequest).where(ServiceRequest.document_access_token == token, ServiceRequest.deleted_at.is_(None)))
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Upload link not found")
    _validate_customer_document_upload(document_type, file)
    path = await save_upload(file, module="services")
    db.add(
        ServiceDocument(
            service_request_id=service.id,
            document_type=document_type,
            file_path=path,
            uploaded_by_type="customer",
            uploaded_by_customer_name=customer_name,
            status="Uploaded",
            uploaded_at=_now(),
        )
    )
    _notify_service_team(
        db,
        service,
        title="Customer documents received",
        message=f"Customer uploaded {document_type} for {service.request_no}.",
        notification_type="customer_document_uploaded",
    )
    db.add(
        ServiceStatusLog(
            service_request_id=service.id,
            action="Customer Document Uploaded",
            old_status=service.status,
            new_status=service.status,
            performed_by=None,
            performed_role="customer",
            remarks=document_type,
            metadata_json=_json_dump({"document_type": document_type, "file_path": path}),
            created_at=_now(),
        )
    )
    db.commit()
    return {"ok": True, "service_request_id": service.id, "message": "Documents uploaded successfully"}


@router.get("/serials/lookup", response_model=SerialLookup)
def lookup_serial(serial_no: str = Query(..., min_length=1), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not (_is_service_team(user) or _is_call_center(user) or _is_engineer(user) or _is_vendor(user)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot look up serials")
    item = _find_order_item_by_serial(db, serial_no)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Serial number not found")
    context = _derive_service_context(db, item)
    order = context["order"]
    return SerialLookup(
        order_item_id=item.id,
        serial_no=item.serial_no or serial_no,
        serial_no_2=item.serial_no_2,
        item_name=None,
        item_code=item.item_code,
        order_no=order.order_no if order else None,
        customer_name=order.customer_name if order else None,
        customer_contact=order.customer_contact if order else None,
        pcb_warranty_date=context["pcb_warranty_date"],
        component_warranty_date=context["component_warranty_date"],
        machine_warranty_date=context["machine_warranty_date"],
        installation_status=item.installation_status,
        free_service_count=item.free_service_count,
        service_consume_count=item.service_consume_count,
    )
