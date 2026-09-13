from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api_client import admin_get, admin_post, admin_put, admin_patch
from app.main import require_auth

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def list_buses(request: Request):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        data = await admin_get("/buses", token=token)
    except Exception:
        data = {"data": []}
    try:
        roads_data = await admin_get("/roads", token=token, params={"limit": 100})
    except Exception:
        roads_data = {"data": []}
    buses = data.get("data", [])
    roads = roads_data.get("data", [])
    road_map = {str(r.get("_id")): r.get("name") for r in roads}
    for b in buses:
        b["assignedRoadName"] = road_map.get(str(b.get("assignedRoad")), "-") if b.get("assignedRoad") else "-"
    
    return templates.TemplateResponse(request, "buses/index.html", {
        "user": user, 
        "buses": buses,
        "roads": roads,
    })


def _extract_error(e):
    try:
        return e.response.json().get("detail", str(e))
    except Exception:
        return str(e)


@router.post("")
async def create_bus(request: Request, busNumber: str = Form(...), licensePlate: str = Form(...),
                     capacity: int = Form(80), assignedRoad: str = Form(None)):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    body = {"busNumber": busNumber, "licensePlate": licensePlate, "capacity": capacity}
    if assignedRoad:
        body["assignedRoad"] = assignedRoad
    try:
        await admin_post("/buses", body, token=token)
        return RedirectResponse("/buses?success=Bus creado correctamente", status_code=302)
    except Exception as e:
        msg = _extract_error(e)
        return RedirectResponse(f"/buses?error={msg}", status_code=302)


@router.post("/{bus_id}")
async def update_bus(bus_id: str, request: Request, busNumber: str = Form(...),
                     licensePlate: str = Form(...), capacity: int = Form(80),
                     assignedRoad: str = Form(None)):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        payload = {"busNumber": busNumber, "licensePlate": licensePlate, "capacity": capacity}
        if assignedRoad is not None:
            payload["assignedRoad"] = assignedRoad
        await admin_put(f"/buses/{bus_id}", payload, token=token)
        return RedirectResponse("/buses?success=Bus actualizado", status_code=302)
    except Exception as e:
        msg = _extract_error(e)
        return RedirectResponse(f"/buses?error={msg}", status_code=302)


@router.post("/{bus_id}/status")
async def change_bus_status(bus_id: str, request: Request, status: str = Form(...)):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        await admin_patch(f"/buses/{bus_id}/status", {"status": status}, token=token)
        return RedirectResponse("/buses?success=Estado actualizado", status_code=302)
    except Exception as e:
        msg = _extract_error(e)
        return RedirectResponse(f"/buses?error={msg}", status_code=302)
