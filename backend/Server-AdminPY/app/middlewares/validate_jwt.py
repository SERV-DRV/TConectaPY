import os
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET", "")


async def validate_jwt(request: Request) -> dict:
    credentials: HTTPAuthorizationCredentials = await security(request)
    if not credentials:
        raise HTTPException(status_code=401, detail="Token no proporcionado")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], options={"verify_aud": False})
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalido o expirado")

    role = payload.get("role") or payload.get(
        "http://schemas.microsoft.com/ws/2008/06/identity/claims/role", "User"
    )
    request.state.user_role = role
    request.state.user_id = payload.get("sub")
    request.state.user_email = payload.get("email")
    return payload


async def require_admin_role(request: Request):
    await validate_jwt(request)
    if request.state.user_role != "Admin":
        raise HTTPException(status_code=403, detail="Se requiere rol de Admin")
