import base64
import json
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api_client import auth_request

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login")
async def login_page(request: Request):
    error = request.query_params.get("error")
    mode = request.query_params.get("mode", "login")
    return templates.TemplateResponse(request, "auth/login.html", {"error": error, "mode": mode})


@router.post("/login")
async def login(request: Request, cui: str = Form(...), password: str = Form(...)):
    try:
        data = await auth_request("POST", "/Auth/login", json={"cui": cui, "password": password})
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
        return RedirectResponse("/planner", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/auth/login?error={str(e)}", status_code=302)


@router.post("/register")
async def register(request: Request, cui: str = Form(...), email: str = Form(...), password: str = Form(...)):
    try:
        data = await auth_request("POST", "/Auth/register", json={"cui": cui, "email": email, "password": password})
        token = data.get("token") or data.get("accessToken")
        if token:
            payload = token.split(".")[1]
            payload += "=" * (4 - len(payload) % 4)
            decoded = json.loads(base64.b64decode(payload))
            request.session["token"] = token
            request.session["user"] = {"id": decoded.get("sub"), "cui": decoded.get("cui"), "role": decoded.get("role", "User")}
            return RedirectResponse("/planner", status_code=302)
        return RedirectResponse("/auth/login?mode=register", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/auth/login?error={str(e)}&mode=register", status_code=302)


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/auth/login", status_code=302)
