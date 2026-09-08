"""Generate and manage service completion (happy) codes."""

from __future__ import annotations

import secrets

from app.models.service import ServiceRequest


def generate_completion_code() -> str:
    return f"{secrets.randbelow(900000) + 100000:06d}"


def issue_completion_code(service: ServiceRequest, *, regenerate: bool = False) -> tuple[str, bool]:
    """Return (code, is_new). Generates a fresh code when missing or regenerate=True."""
    if not regenerate and service.completion_code:
        return service.completion_code, False
    service.completion_code = generate_completion_code()
    return service.completion_code, True


def clear_completion_code(service: ServiceRequest) -> None:
    service.completion_code = None


def validate_engineer_completion_code(service: ServiceRequest, submitted: str | None) -> str:
    code = (submitted or "").strip()
    if not code:
        raise ValueError("Completion code (happy code) is required")
    expected = (service.completion_code or "").strip()
    if not expected:
        raise ValueError("No completion code has been issued for this service request. Contact admin.")
    if code != expected:
        raise ValueError("Completion code is incorrect")
    return code
