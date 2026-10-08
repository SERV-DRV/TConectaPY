from fastapi import APIRouter, Request, Form, Query, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.api_client import auth_request, client_request, get_invoice, get_invoices
from app.main import require_auth
from app.config import STRIPE_PUBLISHABLE_KEY
from datetime import datetime
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


@router.get("/{invoice_id}")
async def invoice_detail(request: Request, invoice_id: str):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        invoice = await get_invoice(invoice_id, token)
        if not invoice:
            raise HTTPException(404, "Factura no encontrada")
    except Exception:
        raise HTTPException(404, "Factura no encontrada")

    # Parsear fecha para template
    fecha = datetime.fromisoformat(invoice["fecha"].replace("Z", "+00:00"))

    return templates.TemplateResponse(request, "wallet/invoice_detail.html", {
        "user": user,
        "invoice": invoice,
        "fecha_formateada": fecha.strftime("%d/%m/%Y %H:%M"),
    })


@router.get("/api/invoices")
async def get_invoices_api(request: Request, page: int = Query(1)):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        raise HTTPException(401, "Unauthorized")
    token = request.session.get("token")
    try:
        data = await get_invoices(page=page, limit=10, token=token)
        return data
    except Exception:
        return {"invoices": [], "total": 0, "page": 1, "limit": 10, "totalPages": 1}


@router.get("")
async def wallet_page(request: Request, tab: str = Query("recharge"), page: int = Query(1)):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    balance = 0.0
    history = []
    invoices = []
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
    elif tab == "invoices":
        try:
            inv_data = await get_invoices(page=page, limit=10, token=token)
            if isinstance(inv_data, dict) and "invoices" in inv_data:
                invoices = inv_data["invoices"]
                total_pages = inv_data.get("totalPages", 1)
        except Exception as e:
            print("Error fetching invoices:", e)
    cui_last4 = str(user.get('cui', '000000000000'))[-4:] if user.get('cui') else '0000'
    expiry_date = '12/28'
    return templates.TemplateResponse(request, "wallet/index.html", {
        "user": user, "balance": balance,
        "tab": tab, "history": history, "invoices": invoices, "page": page, "total_pages": total_pages,
        "balance_last4": cui_last4, "expiry_date": expiry_date,
        "stripe_publishable_key": STRIPE_PUBLISHABLE_KEY,
    })


@router.post("/recharge")
async def recharge(request: Request, amount: float = Form(...), cardNumber: str = Form(...),
                   expirationDate: str = Form(...), cvv: str = Form(...)):
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    token = request.session.get("token")
    try:
        result = await auth_request("POST", "/transaction/recharge", token=token, json={
            "cardNumber": cardNumber, "expirationDate": expirationDate, "cvv": cvv, "amount": amount,
        })
        # Redirect to invoice detail if successful
        if result.get("isSuccess") and result.get("invoiceId"):
            request.session["toast_msg"] = f"Recarga exitosa de Q{amount}"
            return RedirectResponse(f"/wallet/{result['invoiceId']}", status_code=302)
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
        result = await auth_request("POST", "/transaction/purchase-card", token=token, json={
            "cardNumber": cardNumber, "expirationDate": expirationDate, "cvv": cvv, "amount": 20.00,
        })
        # Redirect to invoice detail if successful
        if result.get("isSuccess") and result.get("invoiceId"):
            request.session["toast_msg"] = "Tarjeta ciudadana comprada con exito"
            return RedirectResponse(f"/wallet/{result['invoiceId']}", status_code=302)
        # If user already has card, show error but stay on page
        if not result.get("isSuccess"):
            request.session["toast_error"] = result.get("message", "Error al comprar tarjeta")
        request.session["toast_msg"] = "Tarjeta ciudadana comprada con exito"
    except Exception as e:
        print(f"Error purchase: {e}")
        request.session["toast_error"] = "Error al comprar tarjeta"
    return RedirectResponse("/wallet?tab=purchase", status_code=302)


# ── Stripe Endpoints (Production) ─────────────────────────


@router.post("/create-payment-intent")
async def create_payment_intent(request: Request, amount: float = Form(...), type: str = Form("recharge")):
    """
    Crea PaymentIntent en Auth-Python para Stripe Elements.
    
    Retorna client_secret que el frontend usa con stripe.confirmCardPayment().
    """
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = request.session.get("token")
    try:
        result = await auth_request("POST", "/transaction/create-payment-intent", token=token, json={
            "Amount": amount,
            "TransactionType": type,
        })
        # Retornar client_secret para Stripe.js
        return {
            "client_secret": result.get("client_secret"),
            "payment_intent_id": result.get("transactionId"),
        }
    except Exception as e:
        print(f"Error creating payment intent: {e}")
        raise HTTPException(status_code=500, detail="Error creando PaymentIntent")


@router.post("/recharge-stripe")
async def recharge_stripe(request: Request, payment_method_id: str = Form(...), amount: float = Form(...)):
    """
    Procesa recarga con Stripe PaymentMethod (Production).
    
    El frontend debe haber creado el PaymentMethod con Stripe Elements
    y enviado el payment_method_id (ej: pm_card_visa).
    """
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    
    token = request.session.get("token")
    try:
        result = await auth_request("POST", "/transaction/recharge-stripe", token=token, json={
            "PaymentMethodId": payment_method_id,
            "Amount": amount,
        })
        if result.get("isSuccess") and result.get("invoiceId"):
            request.session["toast_msg"] = f"Recarga exitosa de Q{amount}"
            return RedirectResponse(f"/wallet/{result['invoiceId']}", status_code=302)
        if not result.get("isSuccess"):
            request.session["toast_error"] = result.get("message", "Error en la recarga")
    except Exception as e:
        print(f"Error stripe recharge: {e}")
        request.session["toast_error"] = "Error al procesar recarga con Stripe"
    return RedirectResponse("/wallet?tab=recharge", status_code=302)


@router.post("/purchase-card-stripe")
async def purchase_card_stripe(request: Request, payment_method_id: str = Form(...)):
    """
    Procesa compra de tarjeta ciudadana con Stripe (Production).
    """
    user = await require_auth(request)
    if isinstance(user, RedirectResponse):
        return user
    
    token = request.session.get("token")
    try:
        result = await auth_request("POST", "/transaction/purchase-card-stripe", token=token, json={
            "PaymentMethodId": payment_method_id,
        })
        if result.get("isSuccess") and result.get("invoiceId"):
            request.session["toast_msg"] = "Tarjeta ciudadana comprada con exito"
            return RedirectResponse(f"/wallet/{result['invoiceId']}", status_code=302)
        if not result.get("isSuccess"):
            request.session["toast_error"] = result.get("message", "Error al comprar tarjeta")
    except Exception as e:
        print(f"Error stripe purchase: {e}")
        request.session["toast_error"] = "Error al comprar tarjeta con Stripe"
    return RedirectResponse("/wallet?tab=purchase", status_code=302)

