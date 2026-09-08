"""One-off repair: split incorrectly paired serials on order #67 (IDC-CM-ACL)."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.database import SessionLocal
from app.models.installation import InstallationRequest
from app.models.order import Order, OrderItem

ORDER_ID = 67
MERGED_ITEM_ID = 172


def main() -> None:
    db = SessionLocal()
    try:
        item = db.get(OrderItem, MERGED_ITEM_ID)
        order = db.get(Order, ORDER_ID)
        if item is None or order is None:
            raise SystemExit("Order or order item not found")
        if item.serial_no_2 != "PKC-112":
            raise SystemExit(f"Unexpected serial_no_2 on item {MERGED_ITEM_ID}: {item.serial_no_2!r}")

        inst = db.scalar(
            select(InstallationRequest).where(InstallationRequest.order_item_id == MERGED_ITEM_ID)
        )
        item.serial_no_2 = None
        if inst is not None:
            inst.serial_no_2 = None

        new_item = OrderItem(
            order_id=order.id,
            item_id=item.item_id,
            item_code=item.item_code,
            serial_no="PKC-112",
            serial_no_2=None,
            item_qty=1,
            pcb_warranty_years=item.pcb_warranty_years,
            component_warranty_years=item.component_warranty_years,
            machine_warranty_years=item.machine_warranty_years,
            free_service_count=item.free_service_count,
            dry_free_service_count=item.dry_free_service_count,
            wet_free_service_count=item.wet_free_service_count,
            service_consume_count=item.service_consume_count,
            installation_status="Submitted",
        )
        db.add(new_item)
        db.flush()

        db.add(
            InstallationRequest(
                source="vendor",
                customer_name=order.customer_name or "Unknown",
                contact_number=order.customer_contact or "",
                address=order.customer_city or "",
                order_id=order.id,
                order_item_id=new_item.id,
                product_name="Air Cooler",
                serial_no="PKC-112",
                serial_no_2=None,
                request_date=datetime.now(timezone.utc),
                status="Submitted",
            )
        )
        db.commit()
        print(f"Repaired order {ORDER_ID}: split PKC-112 into order item #{new_item.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
