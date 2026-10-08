from fastapi import APIRouter, Depends, Request

from app.middlewares.validate_jwt import validate_jwt
from app.models.user import User
from app.schemas.auth import TransactionRequest, TransactionResponse
from app.schemas.stripe_schemas import (
    StripeConfirmPaymentRequest,
    StripeCreatePaymentIntentRequest,
    StripePurchaseCardRequest,
    StripeRechargeRequest,
    StripeTransactionResponse,
)
from app.services.payment_gateway_factory import get_payment_service

router = APIRouter()


def get_payment_service_dep():
    """Dependency para inyectar el servicio de pago según entorno."""
    return get_payment_service()


# ── Endpoints de Simulación (Development) ─────────────────
# Estos funcionan con números de tarjeta + Luhn validation


@router.post("/recharge", response_model=TransactionResponse)
async def recharge(
    body: TransactionRequest,
    user: User = Depends(validate_jwt),
    payment_service=Depends(get_payment_service_dep),
):
    """
    Recargar billetera.
    
    - Development: Usa validación Luhn + simulación (cardNumber, expirationDate, cvv)
    - Production: Requiere PaymentMethodId de Stripe (pm_...)
    """
    result = await payment_service.process_recharge(
        user.id, user.cui, body.CardNumber, body.Amount
    )
    return result


@router.post("/purchase-card", response_model=TransactionResponse)
async def purchase_card(
    body: TransactionRequest,
    user: User = Depends(validate_jwt),
    payment_service=Depends(get_payment_service_dep),
):
    """
    Comprar tarjeta ciudadana (Q20.00 fijo).
    
    - Development: Usa validación Luhn + simulación
    - Production: Requiere PaymentMethodId de Stripe
    """
    result = await payment_service.process_purchase_card(
        user.id, user.cui, body.CardNumber, body.Amount
    )
    return result


# ── Endpoints Stripe (Production) ─────────────────────────
# Estos usan PaymentMethod IDs (pm_...) - PCI Compliant


@router.post("/recharge-stripe", response_model=StripeTransactionResponse)
async def recharge_stripe(
    body: StripeRechargeRequest,
    user: User = Depends(validate_jwt),
    payment_service=Depends(get_payment_service_dep),
):
    """
    Recargar billetera usando Stripe PaymentIntent (Production).
    
    Requiere ENVIRONMENT=production y credenciales Stripe configuradas.
    El frontend debe usar Stripe Elements para crear PaymentMethod.
    """
    if not hasattr(payment_service, 'process_recharge_stripe'):
        return {
            "isSuccess": False,
            "message": "Stripe no está configurado. Use ENVIRONMENT=production con STRIPE_SECRET_KEY.",
            "transactionId": "",
            "invoiceId": None,
        }

    result = await payment_service.process_recharge_stripe(
        user_id=user.id,
        cui=user.cui,
        amount=body.Amount,
        payment_method_id=body.PaymentMethodId,
        idempotency_key=body.IdempotencyKey,
    )
    return result


@router.post("/purchase-card-stripe", response_model=StripeTransactionResponse)
async def purchase_card_stripe(
    body: StripePurchaseCardRequest,
    user: User = Depends(validate_jwt),
    payment_service=Depends(get_payment_service_dep),
):
    """
    Comprar tarjeta ciudadana (Q20.00) usando Stripe (Production).
    """
    if not hasattr(payment_service, 'process_purchase_card_stripe'):
        return {
            "isSuccess": False,
            "message": "Stripe no está configurado. Use ENVIRONMENT=production con STRIPE_SECRET_KEY.",
            "transactionId": "",
            "invoiceId": None,
        }

    result = await payment_service.process_purchase_card_stripe(
        user_id=user.id,
        cui=user.cui,
        payment_method_id=body.PaymentMethodId,
        idempotency_key=body.IdempotencyKey,
    )
    return result


@router.post("/create-payment-intent", response_model=StripeTransactionResponse)
async def create_payment_intent(
    body: StripeCreatePaymentIntentRequest,
    user: User = Depends(validate_jwt),
    payment_service=Depends(get_payment_service_dep),
):
    """
    Crea PaymentIntent para uso con Stripe Elements en frontend.
    
    Retorna client_secret que el frontend usa con stripe.confirmCardPayment().
    """
    if not hasattr(payment_service, 'create_payment_intent'):
        return {
            "isSuccess": False,
            "message": "Stripe no está configurado.",
            "transactionId": "",
            "invoiceId": None,
        }

    amount = body.Amount if body.TransactionType == "RECARGA" else 20.00
    
    intent = await payment_service.create_payment_intent(
        amount=amount,
        metadata={
            "user_id": user.id,
            "cui": user.cui,
            "transaction_type": body.TransactionType,
        },
    )
    
    return {
        "isSuccess": True,
        "message": "PaymentIntent creado",
        "transactionId": intent["id"],
        "invoiceId": None,
        "stripe_payment_intent_id": intent["id"],
        "amount_received": intent["amount"] / 100,
        "client_secret": intent["client_secret"],
    }


@router.post("/confirm-payment", response_model=StripeTransactionResponse)
async def confirm_payment(
    body: StripeConfirmPaymentRequest,
    user: User = Depends(validate_jwt),
    payment_service=Depends(get_payment_service_dep),
):
    """
    Confirma un PaymentIntent ya creado (alternativa a confirm=true en create).
    """
    if not hasattr(payment_service, 'process_recharge_stripe'):
        return {
            "isSuccess": False,
            "message": "Stripe no está configurado.",
            "transactionId": "",
            "invoiceId": None,
        }

    # Determinar tipo por metadata del PaymentIntent
    import stripe
    intent = await stripe.PaymentIntent.retrieve_async(body.PaymentIntentId)
    transaction_type = intent.metadata.get("transaction_type", "RECARGA")
    amount = intent.amount / 100

    if transaction_type == "COMPRA_TARJETA":
        result = await payment_service.process_purchase_card_stripe(
            user_id=user.id,
            cui=user.cui,
            payment_method_id=body.PaymentMethodId,
        )
    else:
        result = await payment_service.process_recharge_stripe(
            user_id=user.id,
            cui=user.cui,
            amount=amount,
            payment_method_id=body.PaymentMethodId,
        )
    return result