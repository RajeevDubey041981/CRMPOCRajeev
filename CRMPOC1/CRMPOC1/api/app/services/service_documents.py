from datetime import datetime, timezone
from urllib.parse import urljoin

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.service import ServiceDocument, ServiceDocumentRule, ServiceRequest

CUSTOMER_DOCUMENT_APPROVED_STATUSES = {"Reviewed", "Approved"}

CUSTOMER_DOCUMENT_TYPES = {
    "Purchase Order",
    "Original Purchase Bill/Invoice",
}
CUSTOMER_DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/jpg",
}
CUSTOMER_DOCUMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


def build_public_upload_url(token: str) -> str:
    base = (settings.app_public_url or "").strip()
    if not base:
        base = settings.cors_origin_list[0] if settings.cors_origin_list else "http://localhost:5173"
    return urljoin(base.rstrip("/") + "/", f"services/public-upload/{token}")


def _required_documents_from_rules(
    db: Session,
    service_type: str | None,
    warranty_status: str | None,
    query_type: str | None,
) -> list[str]:
    stmt = select(ServiceDocumentRule).where(
        ServiceDocumentRule.is_active == True,
        ServiceDocumentRule.is_required == True,
    )
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


def customer_document_types(db: Session, service: ServiceRequest) -> list[str]:
    configured = [
        doc
        for doc in _required_documents_from_rules(
            db, service.service_type, service.warranty_status, service.query_type
        )
        if doc in CUSTOMER_DOCUMENT_TYPES
    ]
    if configured:
        return configured
    return sorted(CUSTOMER_DOCUMENT_TYPES)


def latest_customer_documents_by_type(db: Session, service_id: int) -> dict[str, ServiceDocument]:
    rows = db.scalars(
        select(ServiceDocument)
        .where(
            ServiceDocument.service_request_id == service_id,
            ServiceDocument.uploaded_by_type == "customer",
        )
        .order_by(desc(ServiceDocument.uploaded_at))
    ).all()
    latest: dict[str, ServiceDocument] = {}
    for row in rows:
        if row.document_type not in latest:
            latest[row.document_type] = row
    return latest


def document_workflow_active(service: ServiceRequest) -> bool:
    return bool(
        service.ask_for_documents
        or service.document_request_sent_at
        or service.requires_documents
    )


def customer_documents_approved(db: Session, service: ServiceRequest) -> bool:
    if not document_workflow_active(service):
        return True
    configured = customer_document_types(db, service)
    latest = latest_customer_documents_by_type(db, service.id)
    if not latest:
        return False
    required = [doc_type for doc_type in configured if doc_type in latest]
    if not required:
        required = list(latest.keys())
    for doc_type in required:
        row = latest[doc_type]
        if row.status not in CUSTOMER_DOCUMENT_APPROVED_STATUSES:
            return False
    return True


def order_workflow_unlocked(db: Session, service: ServiceRequest) -> bool:
    return customer_documents_approved(db, service)


def sync_document_workflow_status(db: Session, service: ServiceRequest) -> bool:
    """Align service status with customer document upload/review state."""
    if not document_workflow_active(service):
        return False
    latest = latest_customer_documents_by_type(db, service.id)
    if not latest:
        return False
    changed = False
    if customer_documents_approved(db, service):
        if service.status == "Admin Review Document":
            service.status = "Service Team Review"
            service.status_date = datetime.now(timezone.utc)
            changed = True
    else:
        pending = any(
            row.status not in CUSTOMER_DOCUMENT_APPROVED_STATUSES for row in latest.values()
        )
        if pending and service.status in {"New", "Service Team Review"}:
            service.status = "Admin Review Document"
            service.status_date = datetime.now(timezone.utc)
            changed = True
    return changed
