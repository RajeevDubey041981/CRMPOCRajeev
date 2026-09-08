"""Shared visibility and sync rules for engineer service assignments."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.service import ServiceRequest, ServiceRequestUnit


def engineer_visible_service_filter(engineer_id: int):
    return or_(
        ServiceRequest.assigned_engineer_id == engineer_id,
        ServiceRequest.id.in_(
            select(ServiceRequestUnit.service_request_id).where(
                ServiceRequestUnit.assigned_engineer_id == engineer_id
            )
        ),
        ServiceRequest.complaint_id.in_(
            select(Complaint.id).where(Complaint.assigned_engineer == engineer_id)
        ),
    )


def engineer_visible_complaint_filter(engineer_id: int):
    return or_(
        Complaint.assigned_engineer == engineer_id,
        Complaint.id.in_(
            select(ServiceRequest.complaint_id).where(
                ServiceRequest.deleted_at.is_(None),
                ServiceRequest.complaint_id.isnot(None),
                engineer_visible_service_filter(engineer_id),
            )
        ),
    )


def sync_service_engineer_assignment(
    db: Session,
    service: ServiceRequest,
    engineer_id: int,
    *,
    update_complaint: bool = True,
) -> None:
    service.assigned_engineer_id = engineer_id
    service.assigned_vendor_id = None
    if not update_complaint or not service.complaint_id:
        return
    complaint = db.get(Complaint, service.complaint_id)
    if complaint is not None and complaint.assigned_engineer != engineer_id:
        complaint.assigned_engineer = engineer_id
