"""Create isolated test data for the bulk-serial service request E2E flow.

Writes JSON fixture to stdout (logs go to stderr). Run inside the API container:

    Get-Content scripts/setup-e2e-service-flow.py | docker compose exec -T api python -

Or from api/ when PYTHONPATH includes the app:

    python ../scripts/setup-e2e-service-flow.py
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

API_ROOT = Path("/app") if Path("/app/app").exists() else (
    Path("/var/www/indcool/api") if Path("/var/www/indcool/api/app").exists()
    else Path(__file__).resolve().parents[1] / "api"
)
sys.path.insert(0, str(API_ROOT))

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models.item_master import ItemMaster  # noqa: E402
from app.models.order import Order, OrderItem  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.vendor import Vendor  # noqa: E402
from app.security import hash_password  # noqa: E402

CALLCENTER_EMAIL = "callcenter@indcool.com"
CALLCENTER_PASSWORD = "callcenter123"
ENGINEER_EMAIL = "ravi@indcool.com"
ITEM_CODE = "8908012210481"


def _log(message: str) -> None:
    print(message, file=sys.stderr)


def ensure_callcenter_user(db) -> User:
    user = db.scalar(select(User).where(User.email == CALLCENTER_EMAIL))
    if user is None:
        user = User(
            name="Call Center Agent",
            email=CALLCENTER_EMAIL,
            password_hash=hash_password(CALLCENTER_PASSWORD),
            role="callcenter",
            is_active=True,
        )
        db.add(user)
        db.flush()
        _log(f"[setup] created callcenter user: {CALLCENTER_EMAIL}")
    else:
        user.password_hash = hash_password(CALLCENTER_PASSWORD)
        user.role = "callcenter"
        user.is_active = True
        _log(f"[setup] callcenter user already exists: {CALLCENTER_EMAIL}")
    return user


def main() -> int:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    order_no = f"E2E-SRV-{run_id}"
    serial1 = f"E2E-SN-1-{run_id}"
    serial2 = f"E2E-SN-2-{run_id}"
    customer_name = f"E2E Service Customer {run_id}"
    customer_mobile = f"9{run_id[-9:]}"

    db = SessionLocal()
    try:
        callcenter = ensure_callcenter_user(db)
        engineer = db.scalar(select(User).where(User.email == ENGINEER_EMAIL))
        if engineer is None:
            raise RuntimeError(f"Engineer not found: {ENGINEER_EMAIL}. Run seed first.")
        engineer.password_hash = hash_password("engineer123")
        engineer.is_active = True
        engineer.role = "engineer"

        item = db.scalar(
            select(ItemMaster).where(
                ItemMaster.item_code == ITEM_CODE,
                ItemMaster.deleted_at.is_(None),
            )
        )
        if item is None:
            item = db.scalar(
                select(ItemMaster).where(ItemMaster.deleted_at.is_(None)).order_by(ItemMaster.id)
            )
        if item is None:
            raise RuntimeError("No item master found. Run seed first.")

        vendor = db.scalar(select(Vendor).where(Vendor.email == "vendor@indcool.com"))
        admin = db.scalar(select(User).where(User.email == "admin@indcool.com"))

        order = Order(
            order_no=order_no,
            order_date=date.today(),
            customer_name=customer_name,
            customer_contact=customer_mobile,
            customer_email=f"e2e-{run_id}@example.com",
            customer_city="Delhi",
            status="Delivered",
            vendor_id=vendor.id if vendor else None,
            created_by=admin.id if admin else None,
        )
        db.add(order)
        db.flush()

        for serial in (serial1, serial2):
            db.add(
                OrderItem(
                    order_id=order.id,
                    item_id=item.id,
                    item_code=item.item_code,
                    serial_no=serial,
                    pcb_warranty_years=1,
                    component_warranty_years=2,
                    machine_warranty_years=3,
                    free_service_count=2,
                    dry_free_service_count=1,
                    wet_free_service_count=1,
                    service_consume_count=0,
                    installation_status="Completed",
                    item_qty=1,
                )
            )

        db.commit()

        fixture = {
            "run_id": run_id,
            "order_id": order.id,
            "order_no": order_no,
            "customer_name": customer_name,
            "customer_mobile": customer_mobile,
            "serials": [serial1, serial2],
            "item_code": item.item_code,
            "item_name": item.item_name,
            "engineer_email": ENGINEER_EMAIL,
            "engineer_name": engineer.name,
            "engineer_id": engineer.id,
            "callcenter_email": CALLCENTER_EMAIL,
            "callcenter_password": CALLCENTER_PASSWORD,
            "admin_email": "admin@indcool.com",
            "admin_password": "admin123",
            "engineer_password": "engineer123",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        _log(f"[setup] order #{order.id} ({order_no}) with serials {serial1}, {serial2}")
        print(json.dumps(fixture, indent=2))
        return 0
    except Exception as exc:
        db.rollback()
        _log(f"[setup] ERROR: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
