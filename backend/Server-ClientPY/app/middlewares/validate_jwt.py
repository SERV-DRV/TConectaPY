import os

import jwt
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

NODE_CLAIMS_KEY = "uid"
SUB_CLAIMS_KEY = "sub"
DOTNET_NAME_ID_KEY = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier"
DOTNET_ROLE_KEY = "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"


async def validate_jwt(request: Request, credentials: HTTPAuthorizationCredentials | None = None):
    token = None

    if credentials and credentials.credentials:
        token = credentials.credentials
    else:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        else:
            token = request.headers.get("token")

    if not token:
        raise HTTPException(status_code=401, detail="Token no proporcionado")

    try:
        secret = os.getenv("JWT_SECRET", "")
        audience = os.getenv("JWT_AUDIENCE", None)
        kwargs = {"algorithms": ["HS256", "HS384", "HS512"]}
        if audience:
            kwargs["audience"] = audience
        decoded = jwt.decode(token, secret, **kwargs)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

    user_id = (
        decoded.get(NODE_CLAIMS_KEY)
        or decoded.get(SUB_CLAIMS_KEY)
        or decoded.get(DOTNET_NAME_ID_KEY)
    )
    if not user_id:
        raise HTTPException(status_code=401, detail="Token sin identificación de usuario")

    user_role = (
        decoded.get("role")
        or decoded.get(DOTNET_ROLE_KEY)
        or "USER_ROLE"
    )

    request.state.user = {"id": user_id, "role": user_role}
