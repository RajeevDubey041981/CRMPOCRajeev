from __future__ import annotations

import html
import re
from typing import Any

_TAG_RE = re.compile(r"<[^>]*>")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_UNSAFE_PROTOCOL_RE = re.compile(r"(?i)\b(?:javascript|vbscript|data):")
_SECRET_KEYS = {"password", "new_password", "current_password", "password_hash", "token", "access_token"}


def sanitize_text(value: str) -> str:
    """Keep text content safe for storage and later HTML email rendering."""
    value = _CONTROL_RE.sub("", value)
    value = html.unescape(value)
    value = _UNSAFE_PROTOCOL_RE.sub("", value)
    value = _TAG_RE.sub("", value)
    return html.escape(value, quote=True).strip()


def sanitize_json(value: Any, key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {name: sanitize_json(item, name) for name, item in value.items()}
    if isinstance(value, list):
        return [sanitize_json(item, key) for item in value]
    if isinstance(value, str) and (key or "").lower() not in _SECRET_KEYS:
        return sanitize_text(value)
    return value
