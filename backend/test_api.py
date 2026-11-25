import hmac
import json
import os
import tempfile
import time
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import auth
from database import Base, get_db
from main import app

TOKEN = "test-bot-token"
SECRET = "test-signing-secret-for-local-use-only"
ORIGIN = "https://testing.example"


def telegram_data(user_id, age=0):
    fields = {
        "auth_date": str(int(time.time()) - age),
        "user": json.dumps({"id": user_id, "first_name": "Test"}),
    }
    data = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
    secret = hmac.digest(b"WebAppData", TOKEN.encode(), "sha256")
    fields["hash"] = hmac.digest(secret, data.encode(), "sha256").hex()
    return urlencode(fields)


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temp.cleanup)
        test_postgres = os.getenv("TEST_DATABASE_URL")
        cls.engine = create_engine(test_postgres or f"sqlite:///{temp.name}/test.db")
        cls.addClassCleanup(cls.engine.dispose)
        if test_postgres:
            from sqlalchemy import inspect
            if inspect(cls.engine).get_table_names():
                raise RuntimeError("Use a dedicated, empty PostgreSQL test database.")
        Base.metadata.create_all(cls.engine)
        cls.addClassCleanup(Base.metadata.drop_all, cls.engine)

        def test_db():
            with Session(cls.engine) as session:
                yield session

        cls.addClassCleanup(app.dependency_overrides.clear)
        app.dependency_overrides[get_db] = test_db
        cls.addClassCleanup(patch.stopall)
        patch.multiple(auth, BOT_TOKEN=TOKEN, JWT_SECRET=SECRET, ALLOW_LOCAL_DEV=False).start()
        patch.dict(app.user_middleware[0].kwargs, allow_origins=[ORIGIN]).start()
        cls.client = TestClient(app)
        cls.addClassCleanup(cls.client.close)

    def login(self, user_id):
        response = self.client.post("/api/auth/telegram", json={"init_data": telegram_data(user_id)})
        self.assertEqual(response.status_code, 200)
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    def test_login_register_and_legacy_endpoint(self):
        headers = self.login(11001)
        users = self.client.get("/api/users/", headers=headers).json()
        self.assertEqual(users[0]["telegram_id"], 11001)
        again = self.client.get("/api/users/", headers=self.login(11001)).json()
        self.assertEqual(again, users)
        legacy = {"X-Telegram-Init-Data": telegram_data(11001)}
        registration = self.client.post("/api/users/", headers=legacy, json=users[0])
        self.assertEqual(registration.json(), users[0])
        mismatch = {**users[0], "telegram_id": 11111}
        self.assertEqual(self.client.post("/api/users/", headers=headers, json=mismatch).status_code, 403)

    def test_invalid_authentication(self):
        self.assertEqual(self.client.get("/api/tasks").status_code, 401)
        for data in (telegram_data(11001) + "0", telegram_data(11001, age=3601)):
            self.assertEqual(self.client.post("/api/auth/telegram", json={"init_data": data}).status_code, 401)

        valid = self.login(11004)["Authorization"].split()[1]
        claims = jwt.decode(valid, SECRET, algorithms=["HS256"])
        invalid_tokens = (
            jwt.encode(claims, "another-signing-secret-for-testing", algorithm="HS256"),
            jwt.encode({**claims, "exp": 1}, SECRET, algorithm="HS256"),
        )
        for invalid in invalid_tokens:
            response = self.client.get("/api/tasks", headers={"Authorization": f"Bearer {invalid}"})
            self.assertEqual(response.status_code, 401)

    def test_task_crud_and_owner_isolation(self):
        owner, outsider = self.login(11002), self.login(11003)
        user_id = self.client.get("/api/users/", headers=owner).json()[0]["id"]
        user_tasks = f"/api/users/{user_id}/tasks"
        task = self.client.post(user_tasks, headers=owner, json={"title": "First"})
        self.assertEqual(task.status_code, 200)
        path = f"/api/tasks/{task.json()['id']}"
        self.assertEqual(self.client.get(user_tasks, headers=owner).json(), [task.json()])
        self.assertEqual(self.client.get(user_tasks, headers=outsider).status_code, 404)
        self.assertEqual(self.client.get("/api/tasks", headers=outsider).json(), [])
        self.assertEqual(self.client.patch(path, headers=outsider, json={"completed": True}).status_code, 404)
        self.assertEqual(self.client.delete(path, headers=outsider).status_code, 404)
        self.assertEqual(self.client.patch(path, headers=owner, json={"title": None}).status_code, 422)
        self.assertEqual(self.client.post("/api/tasks", headers=owner, json={"title": "x" * 256}).status_code, 422)
        update = self.client.patch(path, headers=owner, json={"completed": True})
        self.assertIs(update.json()["completed"], True)
        self.assertEqual(self.client.delete(path, headers=owner).status_code, 200)
        self.assertEqual(self.client.get("/api/tasks", headers=owner).json(), [])

    def test_health_and_cors(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/health").json(), {"status": "ok"})
        preflight = {
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "authorization,content-type",
        }
        allowed = self.client.options("/api/tasks/1", headers={**preflight, "Origin": ORIGIN})
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.headers["Access-Control-Allow-Origin"], ORIGIN)
        self.assertNotIn("access-control-allow-credentials", allowed.headers)
        for origin in ("https://unknown.example", "http://localhost:5173"):
            blocked = self.client.options("/api/tasks/1", headers={**preflight, "Origin": origin})
            self.assertEqual(blocked.status_code, 400)
            self.assertNotIn("access-control-allow-origin", blocked.headers)
