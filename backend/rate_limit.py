from collections import OrderedDict, deque
from time import monotonic

from starlette.responses import JSONResponse


class RateLimit:
    def __init__(self, app):
        self.app = app
        self.clients = OrderedDict()

    async def __call__(self, scope, receive, send):
        path = scope.get("path", "")
        method = scope.get("method")
        if scope["type"] == "http" and (
            path == "/api/auth/telegram" or
            (path.startswith("/api/auto/") and method in {"POST", "PUT", "PATCH"})
        ) and method != "OPTIONS":
            client = scope.get("client") or ("unknown",)
            auth = path == "/api/auth/telegram"
            key = client[0], auth
            now = monotonic()
            while self.clients and next(iter(self.clients.values()))[-1] <= now - 60:
                self.clients.popitem(last=False)
            if key not in self.clients and len(self.clients) >= 4096:
                self.clients.popitem(last=False)
            history = self.clients.setdefault(key, deque())
            while history and history[0] <= now - 60:
                history.popleft()
            if len(history) >= (30 if auth else 90):
                response = JSONResponse({"detail": "Juda ko‘p so‘rov. Birozdan keyin urinib ko‘ring."},
                                        status_code=429, headers={"Retry-After": "60"})
                await response(scope, receive, send)
                return
            history.append(now)
            self.clients.move_to_end(key)
        await self.app(scope, receive, send)
