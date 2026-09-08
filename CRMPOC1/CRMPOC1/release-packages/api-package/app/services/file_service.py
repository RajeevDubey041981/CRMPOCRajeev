import os
import uuid
from datetime import datetime

from fastapi import HTTPException, UploadFile, status

from app.config import settings

ALLOWED_MIME = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/png",
    "image/jpg",
}
ALLOWED_EXT = {".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png"}
MAX_BYTES = 2 * 1024 * 1024  # 2 MB


def to_public_upload_path(path: str | None) -> str | None:
    if not path:
        return path
    normalized = path.replace("\\", "/")
    marker = "/uploads/"
    idx = normalized.find(marker)
    if idx >= 0:
        return normalized[idx:]
    if normalized.startswith("uploads/"):
        return f"/{normalized}"
    return normalized


def _safe_ext(filename: str) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    return ext if ext in ALLOWED_EXT else ""


async def save_upload(file: UploadFile, module: str) -> str:
    """Validate and persist an uploaded file under /uploads/{module}/{YYYY}/{MM}/.

    Returns the public URL path under /uploads/.
    """
    if file.content_type not in ALLOWED_MIME and _safe_ext(file.filename) == "":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported file type")

    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File exceeds 2MB limit")
    if not contents:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file")

    now = datetime.utcnow()
    sub = os.path.join(settings.upload_dir, module, f"{now.year:04d}", f"{now.month:02d}")
    os.makedirs(sub, exist_ok=True)

    ext = _safe_ext(file.filename) or ""
    name = f"{uuid.uuid4().hex}{ext}"
    full_path = os.path.join(sub, name)
    with open(full_path, "wb") as f:
        f.write(contents)
    return to_public_upload_path(full_path)


async def read_upload_bytes(file: UploadFile) -> tuple[bytes, str, str, int]:
    if file.content_type not in ALLOWED_MIME and _safe_ext(file.filename) == "":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported file type")

    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File exceeds 2MB limit")
    if not contents:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file")

    safe_name = file.filename or f"upload{_safe_ext(file.filename or '')}"
    content_type = file.content_type or "application/octet-stream"
    return contents, safe_name, content_type, len(contents)
