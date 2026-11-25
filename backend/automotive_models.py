from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func

from database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    make = Column(String(80), nullable=False)
    model = Column(String(80), nullable=False)
    year = Column(Integer, nullable=False)
    engine = Column(String(40), nullable=False)
    fuel = Column(String(40), nullable=False)
    plate = Column(String(24), nullable=False)
    mileage = Column(Integer, nullable=False)
    image = Column(String(500))


class ServiceCategory(Base):
    __tablename__ = "service_categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)


class ProductCategory(Base):
    __tablename__ = "product_categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)


class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True)
    category_id = Column(ForeignKey("service_categories.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Integer)
    make = Column(String(80))
    duration = Column(Integer, nullable=False, default=60)
    available = Column(Boolean, nullable=False, default=False)
    image = Column(String(500))


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    category_id = Column(ForeignKey("product_categories.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    make = Column(String(80), index=True)
    price = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=False)
    image = Column(String(500))


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    vehicle_id = Column(ForeignKey("vehicles.id"), nullable=False, index=True)
    service_id = Column(ForeignKey("services.id"), nullable=False, index=True)
    starts_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    phone = Column(String(24), nullable=False)
    notes = Column(Text, nullable=False)
    status = Column(String(24), nullable=False, default="new")
    price = Column(Integer, nullable=False)


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(24), nullable=False, default="new")
    total = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(ForeignKey("products.id"), nullable=False)
    name = Column(String(120), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)


class Favorite(Base):
    __tablename__ = "favorites"
    user_id = Column(ForeignKey("users.id"), primary_key=True)
    product_id = Column(ForeignKey("products.id"), primary_key=True)


class Cart(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id"), nullable=False, unique=True)


class CartItem(Base):
    __tablename__ = "cart_items"
    cart_id = Column(ForeignKey("carts.id"), primary_key=True)
    product_id = Column(ForeignKey("products.id"), primary_key=True)
    quantity = Column(Integer, nullable=False)


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(ForeignKey("vehicles.id"), nullable=False, index=True)
    title = Column(String(120), nullable=False)
    performed_on = Column(String(10), nullable=False)
    next_on = Column(String(10))
    cost = Column(Integer, nullable=False)
    oil_change = Column(Boolean, nullable=False, default=False)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id"), nullable=False, index=True)
    message = Column(String(240), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Banner(Base):
    __tablename__ = "banners"
    id = Column(Integer, primary_key=True)
    title = Column(String(120), nullable=False)
    description = Column(Text, nullable=False)
    image = Column(String(500))
    active = Column(Boolean, nullable=False, default=True)


class Profile(Base):
    __tablename__ = "profiles"
    user_id = Column(ForeignKey("users.id"), primary_key=True)
    phone = Column(String(24))
    language = Column(String(8), nullable=False, default="uz")



class BusinessSettings(Base):
    __tablename__ = "business_settings"
    id = Column(Integer, primary_key=True)
    phone = Column(String(24))
    address = Column(String(240))
    hours = Column(String(160))
