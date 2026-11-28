import json
import logging
from datetime import datetime, timedelta, timezone

from urllib.error import URLError
from urllib.request import Request, urlopen
from fastapi import HTTPException
from sqlalchemy import or_, select

from automotive_models import Booking, Cart, CartItem, Notification, Order, OrderItem, Product, Service, Vehicle
from models import User
from settings import BOT_TOKEN

logger = logging.getLogger(__name__)


def require_row(db, model, key, *, lock=False):
    row = db.get(model, key, with_for_update=lock)
    if row is None:
        raise HTTPException(404, "Topilmadi")
    return row


def owned_vehicle(db, user, key, *, lock=False):
    query = select(Vehicle).where(Vehicle.id == key, Vehicle.user_id == user.id)
    row = db.scalar(query.with_for_update() if lock else query)
    if row is None:
        raise HTTPException(404, "Avtomobil topilmadi")
    return row


def notify(db, user_id, message):
    db.add(Notification(user_id=user_id, message=message))
    return db.get(User, user_id).telegram_id, message


def send_telegram(notification):
    telegram_id, message = notification
    if BOT_TOKEN and telegram_id > 0:
        try:
            request = Request(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data=json.dumps({"chat_id": telegram_id, "text": message}).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=5):
                pass
        except (URLError, TimeoutError):
            logger.warning("Telegram delivery failed")


def booking_service(db, user, vehicle_id, service_id, *, lock=False):
    vehicle = owned_vehicle(db, user, vehicle_id, lock=lock)
    service = require_row(db, Service, service_id, lock=lock)
    if not service.available or service.price is None:
        raise HTTPException(409, "Xizmatga yozilish hozircha yopiq")
    if service.make and service.make.casefold() != vehicle.make.casefold():
        raise HTTPException(422, "Xizmat tanlangan avtomobil markasiga mos emas")
    return service


def overlapping_bookings(vehicle_id, service_id, start, end):
    return select(Booking).where(
        or_(Booking.service_id == service_id, Booking.vehicle_id == vehicle_id),
        Booking.status != "cancelled", Booking.starts_at < end, Booking.ends_at > start,
    )


def reserve(db, user, data):
    service = booking_service(db, user, data.vehicle_id, data.service_id, lock=True)
    start = data.starts_at.astimezone(timezone.utc)
    if start <= datetime.now(timezone.utc):
        raise HTTPException(422, "Kelajakdagi vaqtni tanlang")
    end = start + timedelta(minutes=service.duration)
    conflict = db.scalar(overlapping_bookings(data.vehicle_id, service.id, start, end).limit(1))
    if conflict:
        raise HTTPException(409, "Tanlangan vaqt band")
    booking = Booking(**data.model_dump(exclude={"starts_at"}), user_id=user.id,
                      starts_at=start, ends_at=end, price=service.price)
    db.add(booking)
    db.flush()
    return booking


def get_cart(db, user, *, lock=False):
    if lock:
        db.scalar(select(User.id).where(User.id == user.id).with_for_update())
    cart = db.scalar(select(Cart).where(Cart.user_id == user.id))
    if cart is None and lock:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.flush()
    return cart


def checkout(db, user):
    cart = get_cart(db, user, lock=True)
    items = db.scalars(select(CartItem).where(CartItem.cart_id == cart.id)
                       .order_by(CartItem.product_id)).all()
    if not items:
        raise HTTPException(409, "Savatcha bo‘sh")
    order = Order(user_id=user.id, total=0)
    db.add(order)
    db.flush()
    for item in items:
        product = require_row(db, Product, item.product_id, lock=True)
        if item.quantity > product.stock:
            raise HTTPException(409, f"Omborda yetarli emas: {product.name}")
        product.stock -= item.quantity
        order.total += product.price * item.quantity
        db.add(OrderItem(order_id=order.id, product_id=product.id, name=product.name,
                         quantity=item.quantity, price=product.price))
        db.delete(item)
    if order.total > 2_000_000_000:
        raise HTTPException(422, "Buyurtma jami juda katta")
    return order


def change_status(db, row, status):
    transitions = {
        "new": {"confirmed", "cancelled"},
        "confirmed": {"in_progress", "cancelled"},
        "in_progress": {"completed", "cancelled"},
    }
    if status == row.status:
        return False
    if status not in transitions.get(row.status, set()):
        raise HTTPException(409, "Ushbu holatga o‘tkazib bo‘lmaydi")
    if status == "cancelled" and isinstance(row, Order):
        items = db.scalars(select(OrderItem).where(OrderItem.order_id == row.id)
                           .order_by(OrderItem.product_id)).all()
        for item in items:
            require_row(db, Product, item.product_id, lock=True).stock += item.quantity
    row.status = status
    return True
