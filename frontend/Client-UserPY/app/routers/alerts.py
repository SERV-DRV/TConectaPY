from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api_client import admin_request
from app.main import require_auth

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def alerts_page(request: Request):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    alerts = []
    try:
        data = await admin_request("GET", "/alerts", token=token)
        alerts = data.get("data", [])
    except Exception:
        pass
    return templates.TemplateResponse(request, "alerts/index.html", {
        "user": user, "alerts": alerts,
    })
