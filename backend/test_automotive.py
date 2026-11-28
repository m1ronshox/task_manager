import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

import auth
import automotive
import test_api
from database import Base, get_db
from main import app
from models import Task, User

ADMIN_TELEGRAM_ID = 20100
CUSTOMER_TELEGRAM_ID = 20200


class AutomotiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temp.cleanup)
        engine = create_engine(os.getenv("TEST_DATABASE_URL") or f"sqlite:///{temp.name}/test.db")
        cls.addClassCleanup(engine.dispose)
        if inspect(engine).get_table_names():
            raise RuntimeError("Dedicated empty test database required.")
        Base.metadata.create_all(engine, tables=[User.__table__, Task.__table__])
        cls.addClassCleanup(cls.clean_database, engine)
        with Session(engine) as db:
            user = User(telegram_id=29999, first_name="Legacy")
            db.add(user)
            db.flush()
            db.add(Task(title="Legacy task", user_id=user.id))
            db.commit()
        config = Config(str(Path(__file__).with_name("alembic.ini")))
        with patch("database.engine", engine):
            command.upgrade(config, "head")
            command.upgrade(config, "head")

        def test_db():
            with Session(engine) as db:
                yield db

        app.dependency_overrides[get_db] = test_db
        cls.addClassCleanup(app.dependency_overrides.clear)
        cls.addClassCleanup(patch.stopall)
        patch.multiple(auth, BOT_TOKEN=test_api.TOKEN, JWT_SECRET=test_api.SECRET, ALLOW_LOCAL_DEV=False).start()
        patch.object(automotive, "ADMIN_IDS", {ADMIN_TELEGRAM_ID}).start()
        cls.notify = patch.object(automotive, "send_telegram").start()
        cls.client = TestClient(app)
        cls.addClassCleanup(cls.client.close)
        cls.admin = cls.login(ADMIN_TELEGRAM_ID)
        cls.customer = cls.login(CUSTOMER_TELEGRAM_ID)
        cls.outsider = cls.login(CUSTOMER_TELEGRAM_ID + 1)

    @staticmethod
    def clean_database(engine):
        Base.metadata.drop_all(engine)
        with engine.begin() as db:
            db.execute(text("DROP TABLE IF EXISTS alembic_version"))

    @classmethod
    def login(cls, user_id):
        response = cls.client.post("/api/auth/telegram", json={"init_data": test_api.telegram_data(user_id)})
        if response.status_code != 200:
            raise AssertionError(response.text)
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def catalog(self, **params):
        response = self.client.get("/api/auto/catalog", params=params)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def vehicle(self, headers, plate):
        response = self.client.post("/api/auto/vehicles", headers=headers, json={
            "make": "Chevrolet", "model": "Cobalt", "year": 2023, "engine": "1.5",
            "fuel": "Benzin", "plate": plate, "mileage": 12500,
        })
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["id"]

    def test_migration_and_permissions(self):
        catalog = self.catalog()
        self.assertEqual(len(catalog["service_categories"]), 12)
        self.assertEqual(len(catalog["product_categories"]), 9)
        self.assertEqual(len(catalog["services"]), 12)
        header = self.login(29999)
        self.assertEqual(self.client.get("/api/tasks", headers=header).json()[0]["title"], "Legacy task")
        self.assertEqual(self.client.get("/api/auto/admin/dashboard", headers=self.customer).status_code, 403)
        self.assertEqual(self.client.get("/api/auto/admin/records/users", headers=self.customer).status_code, 403)
        self.assertEqual(self.client.get("/api/auto/admin/dashboard", headers=self.admin).status_code, 200)
        path = "/api/auto/admin/business"
        self.assertEqual(self.client.put(path, headers=self.customer, json={"hours": "Sinov"}).status_code, 403)
        self.assertEqual(self.client.put(path, headers=self.admin, json={"hours": "Sinov"}).status_code, 200)
        self.assertEqual(self.client.get("/api/auto/business").json()["hours"], "Sinov")

    def test_booking_overlap_and_ownership(self):
        vehicle = self.vehicle(self.customer, "80 A 123 AA")
        another = self.vehicle(self.outsider, "80 B 125 BB")
        service = self.catalog()["services"][0]
        payload = {key: service[key] for key in ("category_id", "name", "description", "duration")}
        response = self.client.put(f"/api/auto/admin/services/{service['id']}", headers=self.admin,
                                   json={**payload, "price": 50000, "available": True})
        self.assertEqual(response.status_code, 200, response.text)
        local_zone = ZoneInfo("Asia/Tashkent")
        start = (datetime.now(local_zone) + timedelta(days=3)).replace(hour=10, minute=0, second=0, microsecond=0)
        slots_path = "/api/auto/bookings/slots"
        params = {"vehicle_id": vehicle, "service_id": service["id"], "day": start.date().isoformat()}
        self.assertEqual(self.client.get(slots_path, headers=self.outsider, params=params).status_code, 404)
        self.assertIn(start.isoformat(), self.client.get(slots_path, headers=self.customer, params=params).json())
        data = {"vehicle_id": vehicle, "service_id": service["id"],
                "starts_at": start.isoformat(), "phone": "+998901234567"}
        self.assertEqual(self.client.post("/api/auto/bookings", headers=self.outsider, json=data).status_code, 404)
        created = self.client.post("/api/auto/bookings", headers=self.customer, json=data)
        self.assertEqual(created.status_code, 201, created.text)
        self.assertNotIn(start.isoformat(), self.client.get(slots_path, headers=self.customer, params=params).json())
        bookings = self.client.get("/api/auto/bookings", headers=self.customer).json()
        self.assertEqual(bookings[0]["service_name"], service["name"])
        conflict = self.client.post("/api/auto/bookings", headers=self.outsider, json={
            **data, "vehicle_id": another, "starts_at": (start + timedelta(minutes=10)).isoformat(),
        })
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(self.client.get("/api/auto/bookings", headers=self.outsider).json(), [])
        self.assertEqual(self.client.get(f"/api/auto/vehicles/{vehicle}/maintenance",
                                         headers=self.outsider).status_code, 404)
        record = self.client.post(f"/api/auto/vehicles/{vehicle}/maintenance", headers=self.customer,
                                  json={"title": "Moy", "performed_on": "2026-10-02", "oil_change": True,
                                        "next_on": (datetime.now(ZoneInfo("Asia/Tashkent")).date()
                                                    + timedelta(days=1)).isoformat()})
        self.assertEqual(record.status_code, 201, record.text)
        matching = self.client.get(f"/api/auto/vehicles/{vehicle}/recommendations", headers=self.customer)
        self.assertIn(service["id"], [row["id"] for row in matching.json()["services"]])
        blocked = self.client.get(f"/api/auto/vehicles/{vehicle}/recommendations", headers=self.outsider)
        self.assertEqual(blocked.status_code, 404)
        actual_notices = self.client.get("/api/auto/notifications", headers=self.customer).json()
        self.assertTrue(any(notice["id"] == f"maintenance-{record.json()['id']}" for notice in actual_notices))

    def test_profile_partial_updates_preserve_other_fields(self):
        path = "/api/auto/me"
        self.assertEqual(self.client.patch(path, headers=self.customer, json={"phone": "+998901234567"}).status_code, 200)
        self.assertEqual(self.client.patch(path, headers=self.customer, json={"language": "ru"}).status_code, 200)
        self.assertEqual(self.client.get(path, headers=self.customer).json()["phone"], "+998901234567")
        self.assertEqual(self.client.patch(path, headers=self.customer, json={"phone": None}).json()["language"], "ru")

    @unittest.skipUnless(os.getenv("TEST_DATABASE_URL"), "PostgreSQL row-lock test")
    def test_concurrent_booking_uses_row_locks(self):
        service = self.catalog()["services"][1]
        payload = {key: service[key] for key in ("category_id", "name", "description", "duration")}
        response = self.client.put(f"/api/auto/admin/services/{service['id']}", headers=self.admin,
                                   json={**payload, "price": 50000, "available": True})
        self.assertEqual(response.status_code, 200, response.text)
        first = self.vehicle(self.customer, "80 A 155 AA")
        second = self.vehicle(self.outsider, "80 B 155 BB")
        data = {"service_id": service["id"], "phone": "+998901234567",
                "starts_at": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()}

        def send(target):
            headers, vehicle = target
            return self.client.post("/api/auto/bookings", headers=headers,
                                    json={**data, "vehicle_id": vehicle}).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = sorted(pool.map(send, ((self.customer, first), (self.outsider, second))))
        self.assertEqual(results, [201, 409])

    def test_catalog_cart_order_and_stock(self):
        category = self.catalog()["product_categories"][0]["id"]
        values = {"category_id": category, "name": "Sinov filtri", "description": "Sinov",
                  "make": "Chevrolet", "price": 24000, "stock": 3}
        response = self.client.post("/api/auto/admin/products", headers=self.admin, json=values)
        self.assertEqual(response.status_code, 200, response.text)
        product_id = response.json()["id"]
        self.assertEqual(self.catalog(q="filtri", make="chevrolet", category=category)["products"][0]["id"], product_id)
        self.assertEqual(self.catalog(q="%")["products"], [])
        favorite = self.client.put(f"/api/auto/favorites/{product_id}", params={"enabled": True},
                                   headers=self.customer)
        self.assertEqual(favorite.status_code, 200)
        favorite_products = self.client.get("/api/auto/favorites/products", headers=self.customer)
        self.assertEqual(favorite_products.json()[0]["id"], product_id)
        self.assertEqual(self.client.get("/api/auto/favorites", headers=self.outsider).json(), [])
        added = self.client.put(f"/api/auto/cart/{product_id}", headers=self.customer, json={"quantity": 2})
        self.assertEqual(added.status_code, 200, added.text)
        checkout = self.client.post("/api/auto/orders", headers=self.customer)
        self.assertEqual(checkout.status_code, 201, checkout.text)
        self.assertEqual(checkout.json()["total"], 48000)
        self.assertEqual(self.catalog(q="filtri")["products"][0]["stock"], 1)
        self.assertEqual(self.client.get("/api/auto/cart", headers=self.customer).json(), [])
        order_id = checkout.json()["id"]
        cancelled = self.client.patch(f"/api/auto/admin/status/orders/{order_id}", headers=self.admin,
                                      json={"status": "cancelled"})
        self.assertEqual(cancelled.status_code, 200, cancelled.text)
        self.assertEqual(self.catalog(q="filtri")["products"][0]["stock"], 3)
        self.assertEqual(self.client.get("/api/auto/orders", headers=self.outsider).json(), [])
        self.assertGreaterEqual(self.notify.call_count, 2)
