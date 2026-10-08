from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

import stripe

from app.config import settings
from app.services.payment_gateway_factory import get_payment_service

router = APIRouter()

# Configurar webhook secret para verificación
stripe_webhook_secret = settings.stripe_webhook_secret


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Webhook de Stripe para manejar eventos asíncronos.
    
    Verifica la firma del webhook antes de procesar cualquier evento.
    Maneja: payment_intent.succeeded, payment_intent.payment_failed, 
           payment_intent.canceled, setup_intent.succeeded
    
    URL esperada: https://tconecta-auth.onrender.com/api/stripe/webhook
    Versión API: 2026-08-26.dahlia
    """
    # Solo procesar webhooks en production con Stripe configurado
    if not settings.use_stripe:
        return JSONResponse(
            {"status": "ignored", "message": "Stripe webhooks solo activos en production"},
            status_code=200,
        )

    payload = await request.body()
    signature = request.headers.get("Stripe-Signature")

    if not signature:
        return JSONResponse(
            {"status": "error", "message": "Missing Stripe-Signature header"},
            status_code=400,
        )

    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            stripe_webhook_secret,
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return JSONResponse(
            {"status": "error", "message": "Invalid webhook signature"},
            status_code=400,
        )

    # Obtener servicio Stripe para manejar eventos
    payment_service = get_payment_service()
    
    if not hasattr(payment_service, 'handle_webhook_event'):
        return JSONResponse(
            {"status": "error", "message": "Stripe service not available"},
            status_code=500,
        )

    # Delegar manejo al servicio Stripe
    # Stripe Event object necesita .to_dict() para ser serializable
    event_dict = event.to_dict()
    result = await payment_service.handle_webhook_event(event_dict)
    
    print(f"[Stripe Webhook] Event: {event_dict['type']} | Result: {result.get('status')}")
    
    return {"status": "success", "processed": result}