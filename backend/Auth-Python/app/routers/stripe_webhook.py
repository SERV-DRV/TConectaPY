import stripe
from fastapi import APIRouter, Request, HTTPException, Header

from app.config import settings
from app.services.payment_gateway_factory import get_payment_service

router = APIRouter()


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
):
    """Webhook endpoint para eventos de Stripe"""
    if not settings.use_stripe:
        raise HTTPException(status_code=404, detail="Stripe no configurado")

    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.stripe_webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Payload inválido")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Firma inválida")

    # Procesar evento
    service = get_payment_service()
    if hasattr(service, "handle_webhook_event"):
        result = await service.handle_webhook_event(event)
        print(f"[Stripe Webhook] Event: {event['type']} | Result: {result}")
        return result

    return {"status": "ignored", "event_type": event["type"]}