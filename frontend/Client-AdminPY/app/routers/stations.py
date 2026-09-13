from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api_client import admin_get, admin_post, admin_put
from app.main import require_admin

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def list_stations(request: Request, page: int = Query(1), status: str = Query(None), typeStation: str = Query(None)):
    user = await require_admin(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    params = {"page": page, "limit": 10}
    if status:
        params["status"] = status
    if typeStation:
        params["typeStation"] = typeStation
    try:
        data = await admin_get("/stations", token=token, params=params)
    except Exception:
        data = {"data": [], "totalRecords": 0, "totalPages": 0, "page": 1}
    return templates.TemplateResponse(request, "stations/index.html", {
        "user": user, "stations": data.get("data", []),
        "total": data.get("totalRecords", 0), "page": data.get("page", 1),
        "total_pages": data.get("totalPages", 0), "status": status or "", "typeStation": typeStation or "",
    })


def _extract_error(e):
    try:
        return e.response.json().get("detail", str(e))
    except Exception:
        return str(e)


@router.post("")
async def create_station(request: Request, name: str = Form(...), stationCode: str = Form(...),
                         typeStation: str = Form("CENTRALES"), coordinates: str = Form(...)):
    user = await require_admin(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    coords = [float(c.strip()) for c in coordinates.split(",")]
    try:
        await admin_post("/stations", {"name": name, "stationCode": stationCode, "typeStation": typeStation, "coordinates": coords}, token=token)
        return RedirectResponse("/stations?success=Estacion creada correctamente", status_code=302)
    except Exception as e:
        msg = _extract_error(e)
        return RedirectResponse(f"/stations?error={msg}", status_code=302)


@router.post("/{station_id}")
async def update_station(station_id: str, request: Request, name: str = Form(...),
                         typeStation: str = Form("CENTRALES"), coordinates: str = Form(None)):
    user = await require_admin(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    data = {"name": name, "typeStation": typeStation}
    if coordinates:
        coords = [float(c.strip()) for c in coordinates.split(",")]
        data["coordinates"] = coords
    try:
        await admin_put(f"/stations/{station_id}", data, token=token)
        return RedirectResponse("/stations?success=Estacion actualizada", status_code=302)
    except Exception as e:
        msg = _extract_error(e)
        return RedirectResponse(f"/stations?error={msg}", status_code=302)


@router.post("/{station_id}/status")
async def change_station_status(station_id: str, request: Request, status: str = Form(...)):
    user = await require_admin(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        await admin_put(f"/stations/{station_id}/status", {"status": status}, token=token)
        return RedirectResponse("/stations?success=Estado actualizado", status_code=302)
    except Exception as e:
        msg = _extract_error(e)
        return RedirectResponse(f"/stations?error={msg}", status_code=302)
