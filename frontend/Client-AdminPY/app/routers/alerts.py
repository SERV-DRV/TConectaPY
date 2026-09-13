from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.api_client import admin_get, admin_post, admin_put, admin_delete
from app.main import require_admin

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def list_alerts(request: Request):
    user = await require_admin(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        data = await admin_get("/alerts", token=token)
    except Exception:
        data = {"data": []}
    return templates.TemplateResponse(request, "alerts/index.html", {
        "user": user, "alerts": data.get("data", []),
    })


@router.post("")
async def create_alert(request: Request, title: str = Form(...), description: str = Form(...),
                       typeAlert: str = Form("INFO")):
    user = await require_admin(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        await admin_post("/alerts", {"title": title, "description": description, "typeAlert": typeAlert}, token=token)
    except Exception:
        pass
    return RedirectResponse("/alerts", status_code=302)


@router.put("/{alert_id}/status")
async def resolve_alert(alert_id: str, request: Request, status: str = Form("RESOLVED")):
    user = await require_admin(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        await admin_put(f"/alerts/{alert_id}/status", {"status": status}, token=token)
    except Exception:
        pass
    return RedirectResponse("/alerts", status_code=302)


@router.delete("/{alert_id}")
async def delete_alert(alert_id: str, request: Request):
    user = await require_admin(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        await admin_delete(f"/alerts/{alert_id}", token=token)
        return JSONResponse({"message": "Alerta eliminada"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
