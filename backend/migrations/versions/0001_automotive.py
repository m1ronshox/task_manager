from alembic import op
import sqlalchemy as sa
from sqlalchemy import select

revision = "0001_automotive"
down_revision = None

SERVICES = (
    "Motor diagnostikasi", "Kompyuter diagnostikasi", "Moy almashtirish",
    "Yurish qismini ta’mirlash", "Razval va balansirovka", "Shina almashtirish",
    "Avtoelektrik", "Konditsioner xizmati", "Tuning", "Avtomobil yuvish",
    "Detailing", "Audio tizim o‘rnatish",
)
PRODUCTS = (
    "Motor ehtiyot qismlari", "Amortizatorlar", "Shinalar va disklar",
    "Filtrlar", "Motor moylari", "Akkumulyatorlar", "Avtomobil elektronikasi",
    "Magnitola va dinamiklar", "Avtomobil aksessuarlari",
)


def initial_schema():
    metadata = sa.MetaData()
    sa.Table('banners', metadata,
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('image', sa.String(length=500)),
        sa.Column('active', sa.Boolean(), nullable=False),
    )
    sa.Table('product_categories', metadata,
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
    )
    sa.Table('service_categories', metadata,
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False, unique=True),
    )
    sa.Table('users', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('telegram_id', sa.BigInteger(), unique=True, index=True),
        sa.Column('first_name', sa.String(length=100)),
        sa.Column('username', sa.String(length=100)),
    )
    sa.Table('carts', metadata,
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, unique=True),
    )
    sa.Table('notifications', metadata,
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('message', sa.String(length=240), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    sa.Table('orders', metadata,
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('status', sa.String(length=24), nullable=False),
        sa.Column('total', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    sa.Table('products', metadata,
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('product_categories.id'), nullable=False, index=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('make', sa.String(length=80), index=True),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('stock', sa.Integer(), nullable=False),
        sa.Column('image', sa.String(length=500)),
    )
    sa.Table('profiles', metadata,
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('phone', sa.String(length=24)),
        sa.Column('language', sa.String(length=8), nullable=False),
    )
    sa.Table('services', metadata,
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('service_categories.id'), nullable=False, index=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('price', sa.Integer()),
        sa.Column('duration', sa.Integer(), nullable=False),
        sa.Column('available', sa.Boolean(), nullable=False),
        sa.Column('image', sa.String(length=500)),
    )
    sa.Table('tasks', metadata,
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('completed', sa.Boolean()),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
    )
    sa.Table('vehicles', metadata,
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('make', sa.String(length=80), nullable=False),
        sa.Column('model', sa.String(length=80), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('engine', sa.String(length=40), nullable=False),
        sa.Column('fuel', sa.String(length=40), nullable=False),
        sa.Column('plate', sa.String(length=24), nullable=False),
        sa.Column('mileage', sa.Integer(), nullable=False),
        sa.Column('image', sa.String(length=500)),
    )
    sa.Table('bookings', metadata,
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('vehicle_id', sa.Integer(), sa.ForeignKey('vehicles.id'), nullable=False, index=True),
        sa.Column('service_id', sa.Integer(), sa.ForeignKey('services.id'), nullable=False, index=True),
        sa.Column('starts_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('ends_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('phone', sa.String(length=24), nullable=False),
        sa.Column('notes', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=24), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
    )
    sa.Table('cart_items', metadata,
        sa.Column('cart_id', sa.Integer(), sa.ForeignKey('carts.id'), primary_key=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), primary_key=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
    )
    sa.Table('favorites', metadata,
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), primary_key=True),
    )
    sa.Table('maintenance_records', metadata,
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('vehicle_id', sa.Integer(), sa.ForeignKey('vehicles.id'), nullable=False, index=True),
        sa.Column('title', sa.String(length=120), nullable=False),
        sa.Column('performed_on', sa.String(length=10), nullable=False),
        sa.Column('next_on', sa.String(length=10)),
        sa.Column('cost', sa.Integer(), nullable=False),
        sa.Column('oil_change', sa.Boolean(), nullable=False),
    )
    sa.Table('order_items', metadata,
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False, index=True),
        sa.Column('product_id', sa.Integer(), sa.ForeignKey('products.id'), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
    )
    return metadata


def upgrade():
    connection = op.get_bind()
    metadata = initial_schema()
    metadata.create_all(connection)
    categories = metadata.tables["service_categories"]
    services = metadata.tables["services"]
    for name in SERVICES:
        category_id = connection.scalar(select(categories.c.id).where(categories.c.name == name))
        if category_id is None:
            result = connection.execute(categories.insert().values(name=name))
            connection.execute(services.insert().values(
                category_id=result.inserted_primary_key[0], name=name,
                description=f"{name} bo‘yicha avtoservis xizmati.",
                duration=60, available=False,
            ))
    products = metadata.tables["product_categories"]
    for name in PRODUCTS:
        if connection.scalar(select(products.c.id).where(products.c.name == name)) is None:
            connection.execute(products.insert().values(name=name))


def downgrade():
    raise RuntimeError("Avtomobil ma’lumotlarini o‘chiruvchi downgrade qo‘llab-quvvatlanmaydi.")
