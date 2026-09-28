"""
Endpoints Stripe para T-Conecta
================================

Endpoints para integración con Stripe PaymentIntents.
Solo para modo TEST (sandbox).

Endpoints:
    POST /api/stripe/create-payment-intent  → Crea PaymentIntent, retorna client_secret
    POST /api/stripe/confirm-payment        → Confirma PaymentIntent (opcional)
    GET  /api/stripe/payment-intent/{id}    → Obtiene estado de pago
    POST /api/stripe/refund                 → Crea reembolso (opcional)
    POST /api/stripe/webhook                → Webhook Stripe (opcional)

Autenticación: JWT requerido (validate_jwt)

Flujo frontend:
    1. Usuario en /wallet → Click "Q10.00"
    2. Frontend llama POST /api/stripe/create-payment-intent {amount: 1000, currency: "gtq"}
    2. Backend retorna {client_secret, payment_intent_id}
    3. Frontend usa Stripe.js + client_secret → confirmCardPayment()
    4. Stripe procesa → Webhook/Redirect → Tu backend crea factura
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from app.middlewares.validate_jwt import validate_jwt
from app.models.user import User
from app.services.stripe_service import (
    create_payment_intent,
    confirm_payment_intent,
    retrieve_payment_intent,
    create_refund,
    StripeError,
    get_test_card,
)

router = APIRouter(prefix="/stripe", tags=["Stripe"])


# ─── Schemas ───

class CreatePaymentIntentRequest(BaseModel):
    amount: int = Field(..., gt=0, description="Monto en centavos (Q10.00 = 1000)")
    currency: str = Field(default="gtq", pattern="^[a-z]{3}$")
    metadata: Optional[Dict[str, str]] = None
    receipt_email: Optional[str] = None


class CreatePaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    amount: int
    currency: str
    status: str


class ConfirmPaymentRequest(BaseModel):
    payment_intent_id: str


class RefundRequest(BaseModel):
    payment_intent_id: str
    amount: Optional[int] = None  # None = reembolso total


class WebhookEvent(BaseModel):
    id: str
    type: str
    data: Dict[str, Any]


# ─── Endpoints ───

@router.post("/create-payment-intent", response_model=CreatePaymentIntentResponse)
async def create_payment_intent_endpoint(
    body: CreatePaymentIntentRequest,
    user: User = Depends(validate_jwt),
):
    """
    Crea PaymentIntent para recarga/compra.
    
    Frontend usa client_secret con Stripe.js:
        const {paymentIntent, error} = await stripe.confirmCardPayment(clientSecret, {
            payment_method: {card: cardElement}
        });
    """
    try:
        metadata = body.metadata or {}
        metadata.update({
            "user_id": user.id,
            "cui": user.cui,
        })
        
        result = await create_payment_intent(
            amount=body.amount,
            currency=body.currency,
            metadata=metadata,
            receipt_email=user.email if body.receipt_email else None,
        )
        
        return result
    
    except StripeError as e:
        raise HTTPException(status_code=400, detail={
            "code": e.code,
            "message": e.message,
            "param": e.param,
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/confirm-payment")
async def confirm_payment_endpoint(
    body: ConfirmPaymentRequest,
    user: User = Depends(validate_jwt),
):
    """Confirma PaymentIntent manualmente (opcional)"""
    try:
        result = await confirm_payment_intent(body.payment_intent_id)
        return result
    except StripeError as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/payment-intent/{payment_intent_id}")
async def get_payment_intent(
    payment_intent_id: str,
    user: User = Depends(validate_jwt),
):
    """Obtiene estado y detalles de un PaymentIntent"""
    try:
        result = await retrieve_payment_intent(payment_intent_id)
        
        # Verificar ownership (metadata.user_id)
        if result.get("metadata", {}).get("user_id") != user.id:
            raise HTTPException(403, "No autorizado para ver este pago")
        
        return result
    except StripeError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post("/refund")
async def create_refund_endpoint(
    body: RefundRequest,
    user: User = Depends(validate_jwt),
):
    """Crea reembolso (parcial o total) - Solo Admin"""
    if user.role != "Admin":
        raise HTTPException(403, "Solo administradores pueden reembolsar")
    
    try:
        result = await create_refund(body.payment_intent_id, body.amount)
        return result
    except StripeError as e:
        raise HTTPException(status_code=400, detail=e.message)


# ─── Webhook (opcional) ───

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
):
    """
    Webhook Stripe para eventos async (payment_intent.succeeded, etc.)
    
    Configurar en Stripe Dashboard → Developers → Webhooks:
    URL: https://tconecta-auth.onrender.com/api/stripe/webhook
    Eventos: payment_intent.succeeded, payment_intent.payment_failed, charge.refunded
    
    Requiere STRIPE_WEBHOOK_SECRET en .env
    """
    import os
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    if not webhook_secret:
        raise HTTPException(500, "Webhook secret no configurado")
    
    import stripe
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=webhook_secret
        )
    except ValueError:
        raise HTTPException(400, "Payload inválido")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Firma inválida")
    
    # Manejar eventos
    event_type = event["type"]
    payment_intent = event["data"]["object"]
    
    if event_type == "payment_intent.succeeded":
        # TODO: Crear factura, actualizar wallet
        # user_id = payment_intent["metadata"]["user_id"]
        # await create_invoice_from_payment(user_id, payment_intent)
        pass
    
    elif event_type == "payment_intent.payment_failed":
        # TODO: Log fallo, notificar usuario
        pass
    
    elif event_type == "charge.refunded":
        # TODO: Procesar reembolso
        pass
    
    return {"received": True}


# ─── Utilidades testing ───

@router.get("/test-cards")
async def get_test_cards(user: User = Depends(validate_jwt)):
    """Retorna tarjetas de prueba oficiales Stripe (solo TEST)"""
    return {
        "test_cards": {
            "visa_success": {"number": "4242424242424242", "exp": "12/30", "cvc": "123"},
            "visa_declined": {"number": "4000000000000002", "exp": "12/30", "cvc": "123"},
            "visa_3d_secure": {"number": "4000002500003155", "exp": "12/30", "cvc": "123"},
            "mastercard_success": {"number": "5555555555554444", "exp": "12/30", "cvc": "123"},
        },
        "note": "Solo funcionan en modo TEST con claves sk_test_/pk_test_"
    }