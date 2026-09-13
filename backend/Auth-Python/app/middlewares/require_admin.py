from fastapi import Depends, HTTPException

from app.models.user import User
from app.middlewares.validate_jwt import validate_jwt


async def require_admin(user: User = Depends(validate_jwt)) -> User:
    """Dependency que verifica que el usuario tenga rol Admin."""
    if user.role != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Acceso denegado. Se requieren privilegios de Administrador.",
        )
    return user
