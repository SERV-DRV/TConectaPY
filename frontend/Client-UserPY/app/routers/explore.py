from fastapi import APIRouter, Request, Query
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api_client import admin_request
from app.main import require_auth

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def explore_page(request: Request, tab: str = Query("roads"), page: int = Query(1)):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    roads = []
    stations = []
    total_pages = 1
    total = 0
    if tab == "roads":
        try:
            data = await admin_request("GET", f"/roads?page={page}&limit=6", token=token)
            roads = data.get("data", [])
            total_pages = data.get("totalPages", 1)
            total = data.get("totalRecords", 0)
        except Exception:
            pass
    else:
        try:
            data = await admin_request("GET", f"/stations?page={page}&limit=9", token=token)
            stations = data.get("data", [])
            total_pages = data.get("totalPages", 1)
            total = data.get("totalRecords", 0)
        except Exception:
            pass
    return templates.TemplateResponse(request, "explore/index.html", {
        "user": user, "tab": tab,
        "roads": roads, "stations": stations,
        "page": page, "total_pages": total_pages, "total": total,
    })
