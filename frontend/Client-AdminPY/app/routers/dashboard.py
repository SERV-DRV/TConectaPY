from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api_client import admin_get
from app.main import require_auth

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def dashboard(request: Request):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        roads = await admin_get("/roads?limit=100", token=token)
        stations = await admin_get("/stations?limit=100", token=token)
        buses = await admin_get("/buses", token=token)
        alerts = await admin_get("/alerts", token=token)
    except Exception:
        roads = {"totalRecords": 0}
        stations = {"totalRecords": 0}
        buses = {"data": []}
        alerts = {"data": []}
    return templates.TemplateResponse(request, "dashboard/index.html", {
        "user": user,
        "roads_count": roads.get("totalRecords", 0),
        "stations_count": stations.get("totalRecords", 0),
        "buses_count": len(buses.get("data", [])),
        "alerts_count": alerts.get("total", 0),
    })
