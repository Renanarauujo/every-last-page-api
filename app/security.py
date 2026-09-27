"""CORS, headers de seguranca e limite de requisicoes por IP."""

import os
import threading
import time
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

ORIGINS = "http://localhost:8080,http://127.0.0.1:8080"

HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "frame-ancestors 'none'",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}

SEARCH_LIMIT = 20
WINDOW = 60


def origins() -> list[str]:
    """Retorna as origens permitidas definidas em CORS_ORIGINS."""
    value = os.getenv("CORS_ORIGINS", ORIGINS)
    return [o.strip() for o in value.split(",") if o.strip()]


def setup(app: FastAPI) -> None:
    """Registra o CORS e os headers de seguranca."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins(),
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @app.middleware("http")
    async def add_headers(request: Request, call_next):
        res = await call_next(request)
        for name, value in HEADERS.items():
            res.headers.setdefault(name, value)
        return res


class IpLimiter:
    """Limita a `limit` chamadas por IP a cada `window` segundos."""

    def __init__(self, limit: int, window: float) -> None:
        self.limit = limit
        self.window = window
        self._calls: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def __call__(self, request: Request) -> None:
        """Responde 429 quando o IP excede o limite."""
        ip = request.client.host if request.client else "unknown"
        t = time.monotonic()
        with self._lock:
            calls = self._calls[ip]
            while calls and t - calls[0] >= self.window:
                calls.popleft()
            if len(calls) >= self.limit:
                wait = int(self.window - (t - calls[0])) + 1
                raise HTTPException(
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Muitas buscas em pouco tempo. Tente de novo em instantes.",
                    headers={"Retry-After": str(wait)},
                )
            calls.append(t)

    def reset(self) -> None:
        """Limpa o historico de chamadas."""
        with self._lock:
            self._calls.clear()


search_limit = IpLimiter(SEARCH_LIMIT, WINDOW)
