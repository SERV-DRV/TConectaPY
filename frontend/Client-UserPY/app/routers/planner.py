from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api_client import admin_request, client_request
from app.main import require_auth

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def planner_page(request: Request):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    
    stations = []
    roads = []
    history = []
    try:
        st_data = await admin_request("GET", "/stations/all?status=ACTIVE", token=token)
        stations = st_data.get("data", []) if isinstance(st_data, dict) else st_data
    except Exception as e:
        print(f"Error stations: {e}")

    try:
        rd_data = await admin_request("GET", "/roads/all?status=ACTIVE", token=token)
        roads = rd_data.get("data", []) if isinstance(rd_data, dict) else rd_data
    except Exception as e:
        print(f"Error roads: {e}")
        
    try:
        hist_data = await client_request("GET", "/tours/history", token=token)
        history = hist_data.get("data", []) if isinstance(hist_data, dict) else hist_data
    except Exception:
        pass

    return templates.TemplateResponse(request, "planner/index.html", {
        "user": user, "stations": stations, "roads": roads, "history": history
    })


@router.post("/pay")
async def pay_tour(request: Request, originLat: float = Form(...), originLon: float = Form(...),
                   destLat: float = Form(...), destLon: float = Form(...), systemType: str = Form("DEFAULT"),
                   itinerary: str = Form(""), originName: str = Form(""), destName: str = Form(""),
                   estimatedTime: int = Form(0), distanceMeters: int = Form(0)):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        await client_request("POST", "/tours/plan", token=token, json={
            "userId": user.get("id") or user.get("userId"),
            "originLat": originLat, "originLon": originLon,
            "destLat": destLat, "destLon": destLon,
            "systemType": systemType, "itinerary": itinerary,
            "originName": originName, "destName": destName,
            "estimatedTimeMinutes": estimatedTime, "distanceMeters": distanceMeters,
        })
        request.session["toast_msg"] = "Viaje registrado con exito"
    except Exception as e:
        print(f"Error pay tour: {e}")
        request.session["toast_error"] = "Error al registrar viaje (Saldo insuficiente)"
    return RedirectResponse("/planner", status_code=302)
