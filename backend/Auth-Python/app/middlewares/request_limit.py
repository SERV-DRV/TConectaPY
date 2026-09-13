from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse

from app.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[
        f"{settings.rate_limit_max}/minute",
    ],
    storage_uri="memory://",
)


def rate_limit_exceeded_handler(request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "StatusCode": 429,
            "Message": "Demasiadas peticiones desde esta IP. Intenta de nuevo más tarde.",
            "Detailed": None,
        },
    )


def get_auth_limiter() -> Limiter:
    """Rate limiter dedicado para endpoints de auth (10 req/min)."""
    return Limiter(
        key_func=get_remote_address,
        default_limits=[f"{settings.auth_rate_limit_max}/minute"],
        storage_uri="memory://",
    )
