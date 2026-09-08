import csv
import io
import secrets
import time
from datetime import date, datetime, timezone
from typing import Literal

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy import case, desc, func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.call import Call
from app.models.complaint import Complaint, ComplaintStatusLog
from app.models.order import OrderItem
from app.models.service import ServiceRequest
from app.models.user import User
from app.schemas.complaint import (
    ACTIONS,
    QUERY_TYPES,
    STATUSES,
    ComplaintActionRecord,
    ComplaintCreate,
    ComplaintHistoryEntry,
    ComplaintListItem,
    ComplaintListResponse,
    ComplaintOut,
    ComplaintStatusUpdate,
    ComplaintUpdate,
)
from app.services.file_service import save_upload
from app.services.permissions import can_act_on, sub_module_scope
from app.services.service_documents import build_public_upload_url
from app.services.serial_history import EVENT_TYPES, create_serial_history_event

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


def _apply_view_scope(stmt, db: Session, user: User):
    """Restrict a complaint query to the user's allowed query types.

    Returns (stmt, has_any_access). When has_any_access is False the caller
    should short-circuit with an empty result.
    """
    scope = sub_module_scope(db, user, "complaints", "can_view")
    if scope is None:
        return stmt, True
    if not scope:
        return stmt, False
    return stmt.where(Complaint.query_type.in_(scope)), True


def _generate_comp_no() -> str:
    return f"IDC_{int(time.time() * 1000)}"


def _generate_access_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _generate_service_access_token() -> str:
    return secrets.token_urlsafe(24)


def _hydrate(db: Session, c: Complaint) -> dict:
    engineer_name = None
    if c.assigned_engineer:
        u = db.get(User, c.assigned_engineer)
        engineer_name = u.name if u else None
    created_by_name = None
    if c.created_by:
        u = db.get(User, c.created_by)
        created_by_name = u.name if u else None
    return {
        **{k: getattr(c, k) for k in (
            "id", "comp_no", "comp_date", "customer_name", "customer_mobile",
            "customer_email", "customer_address", "model_details",
            "problem_description", "query_type", "status", "status_date",
            "assigned_engineer", "remark", "service_proof_path", "access_code",
            "send_sms", "created_by", "order_item_id", "serial_no", "source", "created_at", "updated_at",
        )},
        "assigned_engineer_name": engineer_name,
        "created_by_name": created_by_name,
    }


def _list_row(
    db: Session,
    c: Complaint,
    call_count: int = 0,
    pending_followup_count: int = 0,
    last_action_taken: str | None = None,
) -> ComplaintListItem:
    engineer_name = None
    if c.assigned_engineer:
        u = db.get(User, c.assigned_engineer)
        engineer_name = u.name if u else None
    created_by_name = None
    if c.created_by:
        u = db.get(User, c.created_by)
        created_by_name = u.name if u else None
    return ComplaintListItem(
        id=c.id,
        comp_no=c.comp_no,
        customer_name=c.customer_name,
        customer_mobile=c.customer_mobile,
        customer_email=c.customer_email,
        customer_address=c.customer_address,
        model_details=c.model_details,
        problem_description=c.problem_description,
        query_type=c.query_type,
        status=c.status,
        status_date=c.status_date,
        assigned_engineer_name=engineer_name,
        remark=c.remark,
        created_by_name=created_by_name,
        serial_no=c.serial_no,
        order_item_id=c.order_item_id,
        created_at=c.created_at,
        call_count=call_count,
        pending_followup_count=pending_followup_count,
        last_action_taken=last_action_taken,
    )


def _load_visible_complaint(db: Session, complaint_id: int, user: User) -> Complaint:
    complaint = db.get(Complaint, complaint_id)
    if complaint is None or complaint.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Complaint not found")
    if not can_act_on(db, user, "complaints", "can_view", complaint.query_type):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Complaint not found")
    return complaint


def _find_linked_service_request(db: Session, complaint_id: int) -> ServiceRequest | None:
    return db.scalar(
        select(ServiceRequest).where(
            ServiceRequest.complaint_id == complaint_id,
            ServiceRequest.deleted_at.is_(None),
        )
    )


def _ensure_service_request_for_complaint(db: Session, complaint: Complaint, user: User) -> ServiceRequest:
    existing = _find_linked_service_request(db, complaint.id)
    if existing is not None:
        return existing
    now = datetime.now(timezone.utc)
    service = ServiceRequest(
        request_no=f"SRV_{int(time.time() * 1000)}",
        request_date=complaint.comp_date or date.today(),
        query_type=complaint.query_type or "Service",
        customer_name=complaint.customer_name,
        customer_mobile=complaint.customer_mobile,
        customer_email=complaint.customer_email,
        customer_address=complaint.customer_address,
        model_details=complaint.model_details,
        problem_description=complaint.problem_description,
        additional_remarks=complaint.remark,
        status="Service Team Review",
        status_date=datetime.now(timezone.utc),
        source=complaint.source or "callcenter",
        created_by=complaint.created_by or user.id,
        complaint_id=complaint.id,
        order_item_id=complaint.order_item_id,
        serial_no=complaint.serial_no,
        document_access_token=_generate_service_access_token(),
        created_at=now,
        updated_at=now,
    )
    db.add(service)
    db.flush()
    return service


@router.get("", response_model=ComplaintListResponse)
def list_complaints(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
    status_filter: Literal[STATUSES] | None = Query(None, alias="status"),  # type: ignore[valid-type]
    query_type: Literal[QUERY_TYPES] | None = None,  # type: ignore[valid-type]
    search: str | None = None,
    id: int | None = None,
    comp_no: str | None = None,
    source: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort: str = "-created_at",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Complaint).where(Complaint.deleted_at.is_(None))
    stmt, has_access = _apply_view_scope(stmt, db, user)
    if not has_access:
        return ComplaintListResponse(items=[], total=0, page=page, per_page=per_page)
    if id is not None:
        stmt = stmt.where(Complaint.id == id)
    if comp_no:
        stmt = stmt.where(Complaint.comp_no.ilike(f"%{comp_no.strip()}%"))
    if status_filter:
        stmt = stmt.where(Complaint.status == status_filter)
    if query_type:
        stmt = stmt.where(Complaint.query_type == query_type)
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Complaint.customer_name.ilike(like),
                Complaint.customer_mobile.ilike(like),
                Complaint.customer_email.ilike(like),
            )
        )
    if source:
        stmt = stmt.where(Complaint.source == source)
    if date_from:
        stmt = stmt.where(Complaint.comp_date >= date_from)
    if date_to:
        stmt = stmt.where(Complaint.comp_date <= date_to)

    sort_col = sort.lstrip("-")
    col = getattr(Complaint, sort_col, Complaint.created_at)
    stmt = stmt.order_by(desc(col) if sort.startswith("-") else col)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(stmt.offset((page - 1) * per_page).limit(per_page)).all()

    complaint_ids = [c.id for c in rows]
    call_counts: dict[int, int] = {}
    pending_counts: dict[int, int] = {}
    last_actions: dict[int, str] = {}

    if complaint_ids:
        # Batch call counts
        for row in db.execute(
            select(
                Call.complaint_id,
                func.count(Call.id).label("total"),
                func.sum(case((Call.follow_up_status == "Pending", 1), else_=0)).label("pending"),
            )
            .where(Call.complaint_id.in_(complaint_ids))
            .group_by(Call.complaint_id)
        ).all():
            call_counts[row.complaint_id] = row.total
            pending_counts[row.complaint_id] = row.pending or 0

        # Batch last action taken per complaint
        subq = (
            select(
                ComplaintStatusLog.complaint_id,
                ComplaintStatusLog.action_taken,
                func.row_number().over(
                    partition_by=ComplaintStatusLog.complaint_id,
                    order_by=desc(ComplaintStatusLog.changed_at),
                ).label("rn"),
            )
            .where(
                ComplaintStatusLog.complaint_id.in_(complaint_ids),
                ComplaintStatusLog.action_taken.is_not(None),
            )
            .subquery()
        )
        for row in db.execute(
            select(subq.c.complaint_id, subq.c.action_taken).where(subq.c.rn == 1)
        ).all():
            last_actions[row.complaint_id] = row.action_taken

    return ComplaintListResponse(
        items=[
            _list_row(
                db, c,
                call_counts.get(c.id, 0),
                pending_counts.get(c.id, 0),
                last_actions.get(c.id),
            )
            for c in rows
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=ComplaintOut, status_code=status.HTTP_201_CREATED)
def create_complaint(
    body: ComplaintCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not can_act_on(db, user, "complaints", "can_create", body.query_type):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Your role cannot create complaints of type '{body.query_type or 'unspecified'}'",
        )
    complaint = Complaint(
        comp_no=_generate_comp_no(),
        comp_date=body.comp_date or date.today(),
        customer_name=body.customer_name,
        customer_mobile=body.customer_mobile,
        customer_email=body.customer_email,
        customer_address=body.customer_address,
        model_details=body.model_details,
        problem_description=body.problem_description,
        query_type=body.query_type,
        remark=body.remark,
        send_sms=body.send_sms,
        access_code=_generate_access_code(),
        status="Pending",
        created_by=user.id,
        source="callcenter",
    )
    db.add(complaint)
    db.flush()
    db.add(ComplaintStatusLog(
        complaint_id=complaint.id,
        old_status=None,
        new_status="Pending",
        changed_by=user.id,
        remark="Complaint created",
    ))
    if (complaint.query_type or "").lower() == "service":
        _ensure_service_request_for_complaint(db, complaint, user)
    db.commit()
    db.refresh(complaint)
    # NOTE: spec mentions firing an SMS here when send_sms is true.
    # SMS provider integration is Sprint 6 — wire-up point lives in this code path.
    return ComplaintOut(**_hydrate(db, complaint))


@router.get("/export")
def export_csv(
    status_filter: Literal[STATUSES] | None = Query(None, alias="status"),  # type: ignore[valid-type]
    query_type: Literal[QUERY_TYPES] | None = None,  # type: ignore[valid-type]
    search: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    export_scope = sub_module_scope(db, user, "complaints", "can_export")
    if export_scope is not None and not export_scope:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot export complaints")
    stmt = select(Complaint).where(Complaint.deleted_at.is_(None))
    if export_scope is not None:
        stmt = stmt.where(Complaint.query_type.in_(export_scope))
    if status_filter:
        stmt = stmt.where(Complaint.status == status_filter)
    if query_type:
        stmt = stmt.where(Complaint.query_type == query_type)
    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Complaint.customer_name.ilike(like),
                Complaint.customer_mobile.ilike(like),
                Complaint.comp_no.ilike(like),
            )
        )
    if date_from:
        stmt = stmt.where(Complaint.comp_date >= date_from)
    if date_to:
        stmt = stmt.where(Complaint.comp_date <= date_to)
    stmt = stmt.order_by(desc(Complaint.created_at))

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "ID", "Ref No", "Comp Date", "Customer Name", "Mobile", "Email",
        "Address", "Query Type", "Model", "Problem", "Status", "Status Date",
        "Assigned Engineer", "Remark", "Created By", "Created At",
    ])
    for c in db.scalars(stmt).all():
        engineer = db.get(User, c.assigned_engineer).name if c.assigned_engineer else ""
        creator = db.get(User, c.created_by).name if c.created_by else ""
        writer.writerow([
            c.id, c.comp_no, c.comp_date, c.customer_name, c.customer_mobile,
            c.customer_email or "", c.customer_address or "", c.query_type or "",
            c.model_details or "", c.problem_description or "", c.status,
            c.status_date.isoformat() if c.status_date else "",
            engineer, c.remark or "", creator,
            c.created_at.isoformat(),
        ])
    buf.seek(0)
    filename = f"complaints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([buf.read()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _load_visible(db: Session, user: User, complaint_id: int) -> Complaint:
    c = db.get(Complaint, complaint_id)
    if c is None or c.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Complaint not found")
    if not can_act_on(db, user, "complaints", "can_view", c.query_type):
        # Hide existence: 404, not 403.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Complaint not found")
    return c


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = _load_visible(db, user, complaint_id)
    return ComplaintOut(**_hydrate(db, c))


@router.get("/{complaint_id}/service-request")
def get_linked_service_request(
    complaint_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    complaint = _load_visible(db, user, complaint_id)
    service = _find_linked_service_request(db, complaint.id)
    if service is None:
        return {"service_request_id": None, "request_no": None, "upload_url": None, "document_request_sent_at": None, "status": None}
    return {
        "service_request_id": service.id,
        "request_no": service.request_no,
        "upload_url": build_public_upload_url(service.document_access_token) if service.document_access_token else None,
        "document_request_sent_at": service.document_request_sent_at,
        "status": service.status,
    }


@router.post("/{complaint_id}/service-request")
def ensure_linked_service_request(
    complaint_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    complaint = _load_visible(db, user, complaint_id)
    if (complaint.query_type or "").lower() != "service":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only Service complaints can create linked service requests")
    service = _ensure_service_request_for_complaint(db, complaint, user)
    db.commit()
    db.refresh(service)
    return {
        "service_request_id": service.id,
        "request_no": service.request_no,
        "upload_url": build_public_upload_url(service.document_access_token) if service.document_access_token else None,
        "document_request_sent_at": service.document_request_sent_at,
        "status": service.status,
    }


@router.post("/{complaint_id}/documents/request-link")
def request_customer_documents(
    complaint_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    complaint = _load_visible(db, user, complaint_id)
    if (complaint.query_type or "").lower() != "service":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Customer upload links are only available for Service complaints")
    if not complaint.customer_email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Customer email is required before generating upload link")
    service = _ensure_service_request_for_complaint(db, complaint, user)
    service.document_access_token = _generate_service_access_token()
    service.ask_for_documents = True
    service.document_request_sent_at = datetime.now(timezone.utc)
    db.add(
        ComplaintStatusLog(
            complaint_id=complaint.id,
            old_status=complaint.status,
            new_status=complaint.status,
            changed_by=user.id,
            remark="Customer document upload link generated",
            action_taken="Request Sent",
        )
    )
    db.commit()
    db.refresh(service)
    return {
        "service_request_id": service.id,
        "request_no": service.request_no,
        "upload_url": build_public_upload_url(service.document_access_token),
        "document_request_sent_at": service.document_request_sent_at,
        "status": service.status,
    }


@router.put("/{complaint_id}", response_model=ComplaintOut)
def update_complaint(
    complaint_id: int,
    body: ComplaintUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = _load_visible(db, user, complaint_id)
    if not can_act_on(db, user, "complaints", "can_edit", c.query_type):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot edit this complaint")

    data = body.model_dump(exclude_unset=True)
    # Block changing query_type to a type the user has no create/edit perm on.
    if "query_type" in data and data["query_type"] != c.query_type:
        if not can_act_on(db, user, "complaints", "can_edit", data["query_type"]):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Your role cannot move this complaint into '{data['query_type']}'",
            )
    for field, value in data.items():
        setattr(c, field, value)
    db.commit()
    db.refresh(c)
    return ComplaintOut(**_hydrate(db, c))


@router.delete("/{complaint_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_complaint(
    complaint_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = _load_visible(db, user, complaint_id)
    if not can_act_on(db, user, "complaints", "can_delete", c.query_type):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot delete this complaint")
    c.deleted_at = datetime.now(timezone.utc)
    db.commit()


@router.put("/{complaint_id}/status", response_model=ComplaintOut)
async def update_status(
    complaint_id: int,
    new_status: str = Form(...),
    access_code: str | None = Form(None),
    serial_no: str | None = Form(None),
    assigned_engineer: int | None = Form(None),
    remark: str | None = Form(None),
    document: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if new_status not in STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid status")

    c = _load_visible(db, user, complaint_id)
    if not can_act_on(db, user, "complaints", "can_edit", c.query_type):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot edit this complaint")

    linked_item = None
    if serial_no:
        linked_item = db.scalar(
            select(OrderItem).where(
                or_(
                    func.lower(OrderItem.serial_no) == func.lower(serial_no),
                    func.lower(OrderItem.serial_no_2) == func.lower(serial_no),
                )
            )
        )
        if linked_item is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Serial number not found")
        c.order_item_id = linked_item.id
        c.serial_no = serial_no.strip()

    if new_status == "Resolved":
        if not access_code:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Access code required to resolve")
        if c.access_code and access_code != c.access_code:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Access code is incorrect")

    doc_path = None
    if document is not None and document.filename:
        doc_path = await save_upload(document, module="complaints")

    old_status = c.status
    c.status = new_status
    c.status_date = datetime.now(timezone.utc)
    if assigned_engineer is not None:
        c.assigned_engineer = assigned_engineer
    if remark is not None:
        c.remark = remark
    if doc_path:
        c.service_proof_path = doc_path

    log = ComplaintStatusLog(
        complaint_id=c.id,
        old_status=old_status,
        new_status=new_status,
        changed_by=user.id,
        remark=remark,
        document_path=doc_path,
    )
    db.add(log)
    db.flush()
    if c.serial_no:
        create_serial_history_event(
            db,
            serial_no=c.serial_no,
            serial_no_2=linked_item.serial_no_2 if linked_item else None,
            order_item_id=c.order_item_id,
            event_type=EVENT_TYPES["COMPLAINT"],
            event_subtype="STATUS_CHANGED",
            event_at=c.status_date or datetime.now(timezone.utc),
            performed_by_user_id=user.id,
            performed_by_name=user.name,
            source_table="complaint_status_logs",
            source_id=log.id,
            title="Complaint status updated",
            description=f"Complaint {c.comp_no} status changed from {old_status} to {new_status}.",
            remarks=remark,
            metadata={"comp_no": c.comp_no, "old_status": old_status, "new_status": new_status, "document_path": doc_path},
        )
    db.commit()
    db.refresh(c)
    return ComplaintOut(**_hydrate(db, c))


@router.post("/{complaint_id}/action", status_code=status.HTTP_201_CREATED)
def record_action(
    complaint_id: int,
    body: ComplaintActionRecord,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    c = _load_visible(db, user, complaint_id)
    if not can_act_on(db, user, "complaints", "can_edit", c.query_type):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot act on this complaint")
    if body.action_taken not in ACTIONS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid action")
    log = ComplaintStatusLog(
        complaint_id=c.id,
        old_status=c.status,
        new_status=c.status,
        changed_by=user.id,
        remark=body.remark,
        action_taken=body.action_taken,
    )
    db.add(log)
    db.flush()
    if c.serial_no:
        create_serial_history_event(
            db,
            serial_no=c.serial_no,
            order_item_id=c.order_item_id,
            event_type=EVENT_TYPES["SERVICE"],
            event_subtype="ACTION_RECORDED",
            event_at=datetime.now(timezone.utc),
            performed_by_user_id=user.id,
            performed_by_name=user.name,
            source_table="complaint_status_logs",
            source_id=log.id,
            title="Complaint action recorded",
            description=f"Complaint action recorded: {body.action_taken}.",
            remarks=body.remark,
            metadata={"comp_no": c.comp_no, "action_taken": body.action_taken},
        )
    db.commit()
    return {"ok": True, "action_taken": body.action_taken}


@router.get("/{complaint_id}/history", response_model=list[ComplaintHistoryEntry])
def history(
    complaint_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _load_visible(db, user, complaint_id)
    logs = db.scalars(
        select(ComplaintStatusLog)
        .where(ComplaintStatusLog.complaint_id == complaint_id)
        .order_by(ComplaintStatusLog.changed_at.desc())
    ).all()
    out: list[ComplaintHistoryEntry] = []
    for log in logs:
        changed_by_name = None
        if log.changed_by:
            u = db.get(User, log.changed_by)
            changed_by_name = u.name if u else None
        out.append(ComplaintHistoryEntry(
            id=log.id,
            old_status=log.old_status,
            new_status=log.new_status,
            changed_by=log.changed_by,
            changed_by_name=changed_by_name,
            remark=log.remark,
            document_path=log.document_path,
            action_taken=log.action_taken,
            changed_at=log.changed_at,
        ))
    return out
