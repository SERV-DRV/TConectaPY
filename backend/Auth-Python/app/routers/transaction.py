from fastapi import APIRouter, Depends

from app.middlewares.validate_jwt import validate_jwt
from app.models.user import User
from app.schemas.auth import TransactionRequest, TransactionResponse
from app.schemas.stripe_schemas import (
    StripeRechargeRequest,
    StripePurchaseCardRequest,
    CreatePaymentIntentRequest,
    StripePaymentIntentResponse,
)
from app.services.payment_gateway_factory import get_payment_service

router = APIRouter()


# ── Endpoints para SIMULACIÓN (development) ───────────────
# Estos reciben número de tarjeta directo (Luhn validation)


@router.post("/recharge", response_model=TransactionResponse)
async def recharge(
    body: TransactionRequest,
    user: User = Depends(validate_jwt),
):
    service = get_payment_service()
    result = await service.process_recharge(
        user.id, user.cui, body.CardNumber, body.Amount
    )
    return result


@router.post("/purchase-card", response_model=TransactionResponse)
async def purchase_card(
    body: TransactionRequest,
    user: User = Depends(validate_jwt),
):
    service = get_payment_service()
    result = await service.purchase_card(
        user.id, user.cui, body.CardNumber, body.Amount
    )
    return result


# ── Endpoints para STRIPE (production) ────────────────────
# Estos reciben PaymentMethod ID (pm_...)


@router.post("/recharge/stripe", response_model=TransactionResponse)
async def recharge_stripe(
    body: StripeRechargeRequest,
    user: User = Depends(validate_jwt),
):
    service = get_payment_service()
    result = await service.process_recharge(
        user.id, user.cui, body.Amount, body.PaymentMethodId, body.IdempotencyKey
    )
    return result


@router.post("/purchase-card/stripe", response_model=TransactionResponse)
async def purchase_card_stripe(
    body: StripePurchaseCardRequest,
    user: User = Depends(validate_jwt),
):
    service = get_payment_service()
    result = await service.purchase_card(
        user.id, user.cui, body.PaymentMethodId, body.IdempotencyKey
    )
    return result


# ── Crear PaymentIntent (para frontend Stripe Elements) ───


@router.post("/create-payment-intent", response_model=StripePaymentIntentResponse)
async def create_payment_intent(
    body: CreatePaymentIntentRequest,
    user: User = Depends(validate_jwt),
):
    service = get_payment_service()
    result = await service.create_payment_intent(
        user.id, user.cui, body.Amount, body.Type
    )
    if "error" in result:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=result["error"])
    return result