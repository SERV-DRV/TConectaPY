from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.helpers.jwt import verify_access_token
from app.database import async_session_factory
from app.models.user import User

from sqlalchemy import select

security = HTTPBearer(auto_error=False)


async def validate_jwt(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    """Dependency que valida el JWT Bearer token y retorna el usuario."""
    token = credentials.credentials if credentials else None

    # Soporte para header x-token
    if not token:
        token = request.headers.get("x-token")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o usuario no identificado.",
        )

    try:
        payload = verify_access_token(token)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o expirado.",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o usuario no identificado.",
        )

    async with async_session_factory() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Token inválido o usuario no identificado.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Cuenta desactivada. Contacta al administrador.",
        )

    return user
