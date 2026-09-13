from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings

# Claim name del rol que ASP.NET Core emite por defecto
DOTNET_ROLE_CLAIM = "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"


def generate_access_token(user_id: str, cui: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_expires_in)

    payload = {
        "sub": user_id,
        "cui": cui,
        "role": role,
        DOTNET_ROLE_CLAIM: role,
        "iat": now,
        "exp": expire,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def generate_password_reset_token(user_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_reset_expires_in)

    payload = {
        "sub": user_id,
        "email": email,
        "purpose": "PasswordReset",
        "iat": now,
        "exp": expire,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def verify_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
        return payload
    except JWTError as e:
        raise ValueError(str(e)) from e


def validate_password_reset_token(token: str, email: str) -> bool:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
        return payload.get("email") == email and payload.get("purpose") == "PasswordReset"
    except JWTError:
        return False
