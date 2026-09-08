from datetime import date
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.config import settings
from app.models.order import Order, OrderItem
from app.models.item_master import ItemMaster
from app.models.vendor import Vendor
from app.models.user import User

engine = create_engine(settings.get_database_url())
with Session(engine) as session:
    user = session.scalar(select(User).where(User.email == 'vendor1@indcool.com'))
    vendor = session.scalar(select(Vendor).where(Vendor.email == 'vendor1@indcool.com'))
    if user is None or vendor is None:
        raise SystemExit('vendor1 account not found')

    items = {}
    for code in ['8908012210481', '8908012210542']:
        item = session.scalar(select(ItemMaster).where(ItemMaster.item_code == code))
        if item is None:
            raise SystemExit(f'item code not found: {code}')
        items[code] = item

    order_no = 'V1-ORDER-10ROWS-' + date.today().strftime('%Y%m%d')
    if session.scalar(select(Order).where(Order.order_no == order_no)):
        raise SystemExit(f'order already exists: {order_no}')

    order = Order(
        order_no=order_no,
        order_date=date.today(),
        customer_name='Vendor1 Customer',
        customer_contact='9876543299',
        customer_city='Delhi',
        customer_state='Delhi',
        customer_address='Test address',
        status='Pending',
        vendor_id=vendor.id,
        created_by=user.id,
    )
    session.add(order)
    session.flush()

    for _ in range(5):
        for code in ['8908012210481', '8908012210542']:
            item = items[code]
            session.add(OrderItem(
                order_id=order.id,
                item_id=item.id,
                item_code=item.item_code,
                item_qty=1,
                free_service_count=0,
                service_consume_count=0,
                installation_status='Not Requested',
            ))

    session.commit()
    print(order_no)
