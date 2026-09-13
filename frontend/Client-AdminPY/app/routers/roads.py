from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api_client import admin_get, admin_post, admin_put
from app.main import require_admin

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def list_roads(request: Request, page: int = Query(1), status: str = Query(None), typeRoad: str = Query(None)):
    user = await require_admin(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    params = {"page": page, "limit": 10}
    if status:
        params["status"] = status
    if typeRoad:
        params["typeRoad"] = typeRoad
    try:
        data = await admin_get("/roads", token=token, params=params)
    except Exception:
        data = {"data": [], "totalRecords": 0, "totalPages": 0, "page": 1}
    try:
        stations_data = await admin_get("/stations", token=token, params={"limit": 100})
    except Exception:
        stations_data = {"data": []}
    return templates.TemplateResponse(request, "roads/index.html", {
        "user": user, "roads": data.get("data", []),
        "total": data.get("totalRecords", 0), "page": data.get("page", 1),
        "total_pages": data.get("totalPages", 0), "status": status or "", "typeRoad": typeRoad or "",
        "available_stations": stations_data.get("data", []),
    })


def _extract_error(e):
    try:
        return e.response.json().get("detail", str(e))
    except Exception:
        return str(e)


@router.post("")
async def create_road(request: Request, name: str = Form(...), routeCode: str = Form(...),
                      typeRoad: str = Form("CENTRALES"), coordinates: str = Form(...),
                      stationStart: str = Form(None), stationEnd: str = Form(None)):
    user = await require_admin(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    coords = [[float(c.strip()) for c in pair.split(",")] for pair in coordinates.split(";") if pair.strip()]
    stations = []
    if stationStart:
        stations.append(stationStart)
    if stationEnd:
        stations.append(stationEnd)
    body = {"name": name, "routeCode": routeCode, "typeRoad": typeRoad, "coordinates": coords}
    if stations:
        body["stations"] = stations
    try:
        await admin_post("/roads", body, token=token)
        return RedirectResponse("/roads?success=Ruta creada correctamente", status_code=302)
    except Exception as e:
        msg = _extract_error(e)
        return RedirectResponse(f"/roads?error={msg}", status_code=302)


@router.post("/{road_id}")
async def update_road(road_id: str, request: Request, name: str = Form(...), routeCode: str = Form(...),
                      typeRoad: str = Form("CENTRALES"), coordinates: str = Form(None)):
    user = await require_admin(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    data = {"name": name, "routeCode": routeCode, "typeRoad": typeRoad}
    if coordinates:
        coords = [[float(c.strip()) for c in pair.split(",")] for pair in coordinates.split(";") if pair.strip()]
        data["coordinates"] = coords
    try:
        await admin_put(f"/roads/{road_id}", data, token=token)
        return RedirectResponse("/roads?success=Ruta actualizada", status_code=302)
    except Exception as e:
        msg = _extract_error(e)
        return RedirectResponse(f"/roads?error={msg}", status_code=302)


@router.post("/{road_id}/status")
async def change_road_status(road_id: str, request: Request, status: str = Form(...)):
    user = await require_admin(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        await admin_put(f"/roads/{road_id}/status", {"status": status}, token=token)
        return RedirectResponse("/roads?success=Estado actualizado", status_code=302)
    except Exception as e:
        msg = _extract_error(e)
        return RedirectResponse(f"/roads?error={msg}", status_code=302)
