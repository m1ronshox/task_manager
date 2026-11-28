import os
import re
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import get_current_user
from automotive_models import (
    Banner, Booking, BusinessSettings, CartItem, Favorite, MaintenanceRecord, Notification, Order, OrderItem,
    Product, ProductCategory, Profile, Service, ServiceCategory, Vehicle,
)
from automotive_schemas import (
    BannerInput, BookingInput, BusinessInput, CategoryInput, MaintenanceInput, ProductInput, ProfileInput,
    QuantityInput, ServiceInput, StatusInput, VehicleInput,
)
from automotive_service import (
    booking_service, change_status, checkout, get_cart, notify, overlapping_bookings,
    owned_vehicle, require_row, reserve, send_telegram,
)
from database import get_db
from models import User

router = APIRouter(prefix="/api/auto", tags=["Avto Magnat"])
Db = Annotated[Session, Depends(get_db)]
Customer = Annotated[User, Depends(get_current_user)]
ADMIN_IDS = frozenset(int(value) for value in os.getenv("ADMIN_TELEGRAM_IDS", "").split(",") if value.strip())
STATUS_LABELS = dict(new="Yangi", confirmed="Tasdiqlangan", in_progress="Jarayonda",
                     completed="Bajarilgan", cancelled="Bekor qilingan")


def require_admin(user: Customer):
    if user.telegram_id not in ADMIN_IDS:
        raise HTTPException(403, "Administrator ruxsati talab qilinadi")
    return user


admin = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])


def present(row):
    result = {}
    for column in row.__table__.columns:
        value = getattr(row, column.key)
        if isinstance(value, datetime) and value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        result[column.key] = value
    return result


def list_rows(db, statement):
    return [present(row) for row in db.scalars(statement)]


def save(db, row, data=None):
    if data is not None:
        for key, value in data.items():
            setattr(row, key, value)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Yozuv mavjud yoki bog‘langan ma’lumot topilmadi") from None
    db.refresh(row)
    return present(row)


@router.get("/catalog")
def catalog(
    db: Db, q: str = Query("", max_length=120), category: int | None = None,
    make: str = Query("", max_length=80), sort: Literal["name", "asc", "desc"] = "name",
    offset: int = Query(0, ge=0),
):
    products = select(Product)
    services = select(Service)
    if q.strip():
        pattern = q.strip().replace("!", "!!").replace("%", "!%").replace("_", "!_")
        products = products.where(Product.name.ilike(f"%{pattern}%", escape="!"))
        services = services.where(Service.name.ilike(f"%{pattern}%", escape="!"))
    if category is not None:
        products = products.where(Product.category_id == category)
    if make.strip():
        products = products.where(func.lower(Product.make) == make.strip().lower())
    order = {"name": Product.name, "asc": Product.price.asc(), "desc": Product.price.desc()}[sort]
    return {
        "services": list_rows(db, services.order_by(Service.id).limit(200)),
        "products": list_rows(db, products.order_by(order, Product.id).offset(offset).limit(48)),
        "service_categories": list_rows(db, select(ServiceCategory).order_by(ServiceCategory.id)),
        "product_categories": list_rows(db, select(ProductCategory).order_by(ProductCategory.id)),
        "banners": list_rows(db, select(Banner).where(Banner.active).order_by(Banner.id).limit(12)),
    }


@router.get("/business")
def business(db: Db):
    row = db.get(BusinessSettings, 1)
    return present(row) if row else {"phone": None, "address": None, "hours": None}


@admin.put("/business")
def update_business(data: BusinessInput, db: Db):
    return save(db, db.get(BusinessSettings, 1) or BusinessSettings(id=1), data.model_dump())


@router.get("/me")
def me(db: Db, user: Customer):
    profile = db.get(Profile, user.id)
    return {"first_name": user.first_name, "username": user.username,
            "is_admin": user.telegram_id in ADMIN_IDS, "phone": profile.phone if profile else None,
            "language": profile.language if profile else "uz"}


@router.put("/me")
def update_profile(data: ProfileInput, db: Db, user: Customer):
    return save_profile(db, user, data.model_dump())


@router.patch("/me")
def patch_profile(data: ProfileInput, db: Db, user: Customer):
    return save_profile(db, user, data.model_dump(exclude_unset=True))


def save_profile(db, user, values):
    db.scalar(select(User.id).where(User.id == user.id).with_for_update())
    return save(db, db.get(Profile, user.id) or Profile(user_id=user.id), values)


@router.get("/vehicles")
def vehicles(db: Db, user: Customer):
    return list_rows(db, select(Vehicle).where(Vehicle.user_id == user.id).order_by(Vehicle.id))


@router.post("/vehicles", status_code=201)
def create_vehicle(data: VehicleInput, db: Db, user: Customer):
    return save(db, Vehicle(user_id=user.id), data.model_dump(mode="json"))


@router.put("/vehicles/{key}")
def update_vehicle(key: int, data: VehicleInput, db: Db, user: Customer):
    return save(db, owned_vehicle(db, user, key), data.model_dump(mode="json"))


@router.get("/vehicles/{key}/recommendations")
def recommendations(key: int, db: Db, user: Customer):
    vehicle = owned_vehicle(db, user, key)
    services = list_rows(db, select(Service).where(
        Service.available, or_(Service.make.is_(None), func.lower(Service.make) == vehicle.make.lower()),
    ).order_by(Service.name).limit(12))
    products = list_rows(db, select(Product).where(
        Product.stock > 0, or_(Product.make.is_(None), func.lower(Product.make) == vehicle.make.lower()),
    ).order_by(Product.name).limit(12))
    return {"services": services, "products": products}


@router.get("/vehicles/{key}/maintenance")
def maintenance(key: int, db: Db, user: Customer):
    owned_vehicle(db, user, key)
    return list_rows(db, select(MaintenanceRecord).where(MaintenanceRecord.vehicle_id == key)
                     .order_by(MaintenanceRecord.performed_on.desc()))


@router.post("/vehicles/{key}/maintenance", status_code=201)
def add_maintenance(key: int, data: MaintenanceInput, db: Db, user: Customer):
    owned_vehicle(db, user, key)
    if data.next_on and data.next_on < data.performed_on:
        raise HTTPException(422, "Keyingi xizmat sanasi bajarilgan sanadan oldin bo‘la olmaydi")
    return save(db, MaintenanceRecord(vehicle_id=key), data.model_dump(mode="json"))


@router.get("/bookings")
def bookings(db: Db, user: Customer):
    rows = db.execute(
        select(Booking, Service.name).join(Service, Booking.service_id == Service.id, isouter=True)
        .where(Booking.user_id == user.id).order_by(Booking.id.desc())
    )
    return [dict(present(row), service_name=name) for row, name in rows]


@router.get("/bookings/slots")
def booking_slots(db: Db, user: Customer, vehicle_id: int, service_id: int, day: date):
    local_zone = ZoneInfo("Asia/Tashkent")
    now = datetime.now(local_zone)
    if day < now.date():
        return []
    if day > now.date() + timedelta(days=60):
        raise HTTPException(422, "Keyingi 60 kun ichidan sana tanlang")
    service = booking_service(db, user, vehicle_id, service_id)
    settings = db.get(BusinessSettings, 1)
    hours = settings.hours if settings else None
    opening, closing = time(9), time(18)
    if match := re.fullmatch(r"\s*((?:[01]\d|2[0-3]):[0-5]\d)\s*[–—-]\s*((?:[01]\d|2[0-3]):[0-5]\d)\s*", hours or ""):
        configured_open, configured_close = map(time.fromisoformat, match.groups())
        if configured_open < configured_close:
            opening, closing = configured_open, configured_close
    opens = datetime.combine(day, opening, local_zone).astimezone(timezone.utc)
    closes = datetime.combine(day, closing, local_zone).astimezone(timezone.utc)
    duration = timedelta(minutes=service.duration)
    busy = list_rows(db, overlapping_bookings(vehicle_id, service_id, opens, closes))
    slots = []
    for minutes in range(0, int((closes - opens).total_seconds() // 60), 30):
        start = opens + timedelta(minutes=minutes)
        end = start + duration
        if start > now and end <= closes and not any(
            row["starts_at"] < end and row["ends_at"] > start for row in busy
        ):
            slots.append(start.astimezone(local_zone))
    return slots


@router.post("/bookings", status_code=201)
def booking(data: BookingInput, db: Db, user: Customer, background: BackgroundTasks):
    row = reserve(db, user, data)
    notice = notify(db, user.id, f"Avtoservisga yozilish №{row.id} qabul qilindi.")
    result = save(db, row)
    background.add_task(send_telegram, notice)
    return result


@router.get("/favorites")
def favorites(db: Db, user: Customer):
    return list(db.scalars(select(Favorite.product_id).where(Favorite.user_id == user.id)))


@router.get("/favorites/products")
def favorite_products(db: Db, user: Customer):
    return list_rows(db, select(Product).join(Favorite, Favorite.product_id == Product.id)
                     .where(Favorite.user_id == user.id).order_by(Product.name))


@router.put("/favorites/{key}")
def set_favorite(key: int, enabled: bool, db: Db, user: Customer):
    require_row(db, Product, key)
    db.scalar(select(User.id).where(User.id == user.id).with_for_update())
    row = db.get(Favorite, (user.id, key))
    if enabled and row is None:
        db.add(Favorite(user_id=user.id, product_id=key))
    elif not enabled and row is not None:
        db.delete(row)
    db.commit()
    return {"enabled": enabled}


@router.get("/cart")
def cart(db: Db, user: Customer):
    row = get_cart(db, user)
    if row is None:
        return []
    return [{"quantity": item.quantity, "product": present(product)}
            for item, product in db.execute(select(CartItem, Product)
            .join(Product, Product.id == CartItem.product_id).where(CartItem.cart_id == row.id))]


@router.put("/cart/{key}")
def change_cart(key: int, data: QuantityInput, db: Db, user: Customer):
    row = get_cart(db, user, lock=True)
    product = require_row(db, Product, key)
    item = db.get(CartItem, (row.id, key))
    if data.quantity > product.stock:
        raise HTTPException(409, "Omborda yetarli mahsulot yo‘q")
    if data.quantity:
        save(db, item or CartItem(cart_id=row.id, product_id=key), data.model_dump())
    elif item is not None:
        db.delete(item)
        db.commit()
    return {"quantity": data.quantity}


@router.get("/orders")
def orders(db: Db, user: Customer):
    rows = list_rows(db, select(Order).where(Order.user_id == user.id).order_by(Order.id.desc()))
    for row in rows:
        row["items"] = list_rows(db, select(OrderItem).where(OrderItem.order_id == row["id"]))
    return rows


@router.post("/orders", status_code=201)
def order(db: Db, user: Customer, background: BackgroundTasks):
    row = checkout(db, user)
    notice = notify(db, user.id, f"Ehtiyot qismlar buyurtmasi №{row.id} qabul qilindi.")
    result = save(db, row)
    background.add_task(send_telegram, notice)
    return result


@router.get("/notifications")
def notifications(db: Db, user: Customer):
    today = datetime.now(ZoneInfo("Asia/Tashkent")).date()
    next_week = (today + timedelta(days=7)).isoformat()
    upcoming = db.execute(select(MaintenanceRecord, Vehicle)
        .join(Vehicle, Vehicle.id == MaintenanceRecord.vehicle_id)
        .where(Vehicle.user_id == user.id, MaintenanceRecord.next_on.between(today.isoformat(), next_week))
        .order_by(MaintenanceRecord.next_on).limit(15))
    reminders = [
        {"id": f"maintenance-{record.id}",
         "message": f"{vehicle.make} {vehicle.model}: {record.title} · {record.next_on}"}
        for record, vehicle in upcoming
    ]
    return reminders + list_rows(db, select(Notification).where(Notification.user_id == user.id)
                                 .order_by(Notification.id.desc()).limit(50))


ADMIN_TABLES = {
    "users": User, "vehicles": Vehicle, "bookings": Booking, "orders": Order,
    "service-categories": ServiceCategory, "product-categories": ProductCategory,
    "services": Service, "products": Product, "banners": Banner,
}


@admin.get("/dashboard")
def dashboard(db: Db):
    counts = {name: db.scalar(select(func.count()).select_from(model)) for name, model in ADMIN_TABLES.items()}
    counts["revenue"] = sum(db.scalar(select(func.coalesce(func.sum(model.__table__.c[column]), 0))
                              .where(model.status == "completed"))
                            for model, column in ((Order, "total"), (Booking, "price")))
    counts["low_stock"] = db.scalar(select(func.count()).select_from(Product).where(Product.stock < 5))
    return counts


@admin.get("/records/{resource}")
def admin_records(resource: str, db: Db, offset: int = Query(0, ge=0)):
    model = ADMIN_TABLES.get(resource)
    if model is None:
        raise HTTPException(404, "Bo‘lim topilmadi")
    return list_rows(db, select(model).order_by(model.id.desc()).offset(offset).limit(100))


def admin_save(db, model, key, data):
    row = require_row(db, model, key, lock=True) if key is not None else model()
    return save(db, row, data.model_dump(mode="json"))


@admin.post("/services")
@admin.put("/services/{key}")
def manage_services(data: ServiceInput, db: Db, key: int | None = None):
    if data.available and data.price is None:
        raise HTTPException(422, "Xizmatni ochish uchun narx kiriting")
    return admin_save(db, Service, key, data)


@admin.post("/products")
@admin.put("/products/{key}")
def manage_products(data: ProductInput, db: Db, key: int | None = None):
    return admin_save(db, Product, key, data)


@admin.post("/banners")
@admin.put("/banners/{key}")
def manage_banners(data: BannerInput, db: Db, key: int | None = None):
    return admin_save(db, Banner, key, data)


@admin.post("/categories/{kind}")
@admin.put("/categories/{kind}/{key}")
def manage_categories(kind: Literal["service", "product"], data: CategoryInput, db: Db, key: int | None = None):
    return admin_save(db, ServiceCategory if kind == "service" else ProductCategory, key, data)


@admin.patch("/status/{kind}/{key}")
def set_status(kind: Literal["orders", "bookings"], key: int, data: StatusInput,
               db: Db, background: BackgroundTasks):
    row = require_row(db, Order if kind == "orders" else Booking, key, lock=True)
    if not change_status(db, row, data.status):
        return present(row)
    label = "Buyurtma" if kind == "orders" else "Avtoservisga yozilish"
    notice = notify(db, row.user_id, f"{label} №{row.id}: {STATUS_LABELS[data.status]}.")
    result = save(db, row)
    background.add_task(send_telegram, notice)
    return result


router.include_router(admin)
