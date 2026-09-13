from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.main import require_admin
from app.api_client import auth_get, auth_post

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def list_users(request: Request):
    user = await require_admin(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        data = await auth_get("/Auth/users", token=token)
    except Exception:
        data = []
    users = data if isinstance(data, list) else data.get("data", [])
    return templates.TemplateResponse(request, "users/index.html", {
        "user": user, "users": users,
    })


def _extract_error(e):
    try:
        return e.response.json().get("detail", str(e))
    except Exception:
        return str(e)


@router.post("")
async def create_admin(request: Request, cui: str = Form(...), email: str = Form(...), password: str = Form(...)):
    user = await require_admin(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        await auth_post("/Auth/register-admin", {"cui": cui, "email": email, "password": password}, token=token)
        return RedirectResponse("/users?success=Admin creado correctamente", status_code=302)
    except Exception as e:
        msg = _extract_error(e)
        return RedirectResponse(f"/users?error={msg}", status_code=302)
