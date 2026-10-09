import base64
import json
from fastapi import Request
from fastapi.responses import RedirectResponse


def decode_jwt(token: str) -> dict:
    try:
        payload = token.split(".")[1]
        payload += "=" * (4 - len(payload) % 4)
        data = json.loads(base64.b64decode(payload))
        role = data.get("role") or data.get(
            "http://schemas.microsoft.com/ws/2008/06/identity/claims/role", "User"
        )
        return {"id": data.get("sub"), "cui": data.get("cui"), "role": role}
    except Exception:
        return {}


async def require_auth(request: Request):
    token = request.session.get("token")
    if not token:
        return RedirectResponse("/auth/login", status_code=302)
    user = decode_jwt(token)
    if not user:
        request.session.clear()
        return RedirectResponse("/auth/login", status_code=302)
    request.state.user = user
    request.state.token = token
    request.state.toast_msg = request.session.pop("toast_msg", None)
    request.state.toast_error = request.session.pop("toast_error", None)
    return user