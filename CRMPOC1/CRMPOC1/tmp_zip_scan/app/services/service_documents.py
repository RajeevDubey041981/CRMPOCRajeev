from urllib.parse import urljoin

from app.config import settings


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
    origin = settings.cors_origin_list[0] if settings.cors_origin_list else "http://localhost:5173"
    return urljoin(origin.rstrip("/") + "/", f"services/public-upload/{token}")
