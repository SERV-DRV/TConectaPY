from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api_client import auth_request, client_request
from app.main import require_auth

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("")
async def profile_page(request: Request):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    email = ""
    tours = []
    try:
        email_data = await auth_request("GET", "/Auth/me/email", token=token)
        email = email_data.get("email", "")
    except Exception:
        pass
    try:
        tours_data = await client_request("GET", "/tours/history", token=token)
        tours = tours_data.get("data", []) if isinstance(tours_data, dict) else tours_data
    except Exception:
        pass
    return templates.TemplateResponse(request, "profile/index.html", {
        "user": user, "email": email, "tours": tours,
        "totalSpent": sum(t.get("chargedFare", 0) for t in tours),
        "totalDistance": sum(t.get("distanceMeters", 0) / 1000 for t in tours),
    })


@router.post("/update-email")
async def update_email(request: Request, newEmail: str = Form(...)):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        await auth_request("PUT", "/Auth/update-email", token=token, json={"newEmail": newEmail})
        request.session["toast_msg"] = "Correo actualizado correctamente"
    except Exception:
        request.session["toast_error"] = "Error al actualizar correo"
    return RedirectResponse("/profile", status_code=302)
