from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.middlewares.require_admin import require_admin
from app.middlewares.validate_jwt import validate_jwt
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    EmailResponse,
    LoginRequest,
    MessageResponse,
    RecoverPasswordRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UpdateEmailRequest,
    UpdateEmailResponse,
    UserOut,
)
from app.services import auth_service

router = APIRouter()

limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=AuthResponse)
@limiter.limit("10/minute")
async def register(
    request: Request,
    body: RegisterRequest,
):
    result = await auth_service.register(body.CUI, body.Email, body.Password)
    return result


@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
):
    result = await auth_service.login(body.CUI, body.Password)
    return result


@router.post("/recover-password", response_model=TokenResponse)
@limiter.limit("10/minute")
async def recover_password(
    request: Request,
    body: RecoverPasswordRequest,
):
    result = await auth_service.request_password_reset(body.Email)
    return result


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("10/minute")
async def reset_password(
    request: Request,
    body: ResetPasswordRequest,
):
    await auth_service.reset_password(body.Email, body.Token, body.NewPassword)
    return {"message": "Contraseña actualizada exitosamente."}


@router.get("/users", response_model=list[UserOut])
async def get_all_users(
    user: User = Depends(require_admin),
):
    return await auth_service.get_all_users()


@router.post("/register-admin", response_model=AuthResponse)
async def register_admin(
    body: RegisterRequest,
    user: User = Depends(require_admin),
):
    result = await auth_service.register_admin(body.CUI, body.Email, body.Password)
    return result


@router.get("/me/email", response_model=EmailResponse)
async def get_user_email(
    user: User = Depends(validate_jwt),
):
    return await auth_service.get_user_email(user.id)


@router.put("/update-email", response_model=UpdateEmailResponse)
async def update_email(
    body: UpdateEmailRequest,
    user: User = Depends(validate_jwt),
):
    return await auth_service.update_email(user.id, body.NewEmail)
