import base64
import json
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api_client import auth_post

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login")
async def login_page(request: Request):
    error = request.query_params.get("error")
    return templates.TemplateResponse(request, "auth/login.html", {"error": error})


@router.post("/login")
async def login(request: Request, cui: str = Form(...), password: str = Form(...)):
    try:
        data = await auth_post("/Auth/login", {"cui": cui, "password": password})
        token = data.get("token") or data.get("accessToken")
        if not token:
            return RedirectResponse("/auth/login?error=Credenciales invalidas", status_code=302)
        payload = token.split(".")[1]
        payload += "=" * (4 - len(payload) % 4)
        decoded = json.loads(base64.b64decode(payload))
        role = decoded.get("role") or decoded.get(
            "http://schemas.microsoft.com/ws/2008/06/identity/claims/role", "User"
        )
        request.session["token"] = token
        request.session["user"] = {"id": decoded.get("sub"), "cui": decoded.get("cui"), "role": role}
        return RedirectResponse("/dashboard", status_code=302)
    except Exception as e:
        msg = "Credenciales invalidas"
        try:
            msg = e.response.json().get("Message", msg)
        except Exception:
            pass
        return RedirectResponse(f"/auth/login?error={msg}", status_code=302)


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/auth/login", status_code=302)
