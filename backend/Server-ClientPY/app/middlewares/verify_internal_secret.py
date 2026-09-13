import os

from fastapi import Request, HTTPException


async def verify_internal_secret(request: Request):
    secret = request.headers.get("x-internal-secret")
    expected = os.getenv("INTERNAL_SECRET", "")

    if not secret or secret != expected:
        raise HTTPException(status_code=403, detail="Acceso no autorizado")
