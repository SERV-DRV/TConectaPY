from fastapi import APIRouter, Request, Form, Query, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.api_client import auth_request, client_request
from app.main import require_auth
import math

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/api/balance")
async def get_balance_api(request: Request):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = request.session.get("token")
    try:
        bal_data = await client_request("GET", "/wallets/balance", token=token)
        balance = bal_data.get("balance", bal_data.get("data", {}).get("balance", 0))
        return {"balance": balance}
    except Exception:
        return {"balance": 0.0}

@router.get("")
async def wallet_page(request: Request, tab: str = Query("recharge"), page: int = Query(1)):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    balance = 0.0
    history = []
    total_pages = 1
    try:
        bal_data = await client_request("GET", "/wallets/balance", token=token)
        balance = bal_data.get("balance", bal_data.get("data", {}).get("balance", 0))
    except Exception:
        pass
    if tab == "history":
        try:
            hist_data = await client_request("GET", f"/wallets/history?page={page}&limit=10", token=token)
            if isinstance(hist_data, dict):
                if "history" in hist_data:
                    history = hist_data["history"]
                    total_pages = math.ceil(hist_data.get("total", 0) / hist_data.get("limit", 10)) or 1
                elif "data" in hist_data:
                    history = hist_data["data"]
                    total_pages = hist_data.get("totalPages", 1)
                else:
                    history = hist_data
            else:
                history = hist_data
        except Exception as e:
            print("Error fetching history:", e)
    cui_last4 = str(user.get('cui', '000000000000'))[-4:] if user.get('cui') else '0000'
    expiry_date = '12/28'
    return templates.TemplateResponse(request, "wallet/index.html", {
        "user": user, "balance": balance,
        "tab": tab, "history": history, "page": page, "total_pages": total_pages,
        "balance_last4": cui_last4, "expiry_date": expiry_date,
    })


@router.post("/recharge")
async def recharge(request: Request, amount: float = Form(...), cardNumber: str = Form(...),
                   expirationDate: str = Form(...), cvv: str = Form(...)):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        await auth_request("POST", "/transaction/recharge", token=token, json={
            "cardNumber": cardNumber, "expirationDate": expirationDate, "cvv": cvv, "amount": amount,
        })
        request.session["toast_msg"] = f"Recarga exitosa de Q{amount}"
    except Exception as e:
        print(f"Error recharge: {e}")
        request.session["toast_error"] = "Error al recargar"
    return RedirectResponse("/wallet?tab=recharge", status_code=302)


@router.post("/purchase-card")
async def purchase_card(request: Request, cardNumber: str = Form(...),
                        expirationDate: str = Form(...), cvv: str = Form(...)):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        await auth_request("POST", "/transaction/purchase-card", token=token, json={
            "cardNumber": cardNumber, "expirationDate": expirationDate, "cvv": cvv, "amount": 20.00,
        })
        request.session["toast_msg"] = "Tarjeta ciudadana comprada con exito"
    except Exception as e:
        print(f"Error purchase: {e}")
        request.session["toast_error"] = "Error al comprar tarjeta"
    return RedirectResponse("/wallet?tab=purchase", status_code=302)

