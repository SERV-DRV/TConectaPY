from typing import Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class BaseStripeSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


# ── Stripe Requests ──────────────────────────────────────


class StripeRechargeRequest(BaseStripeSchema):
    """Request para recarga con Stripe (PaymentMethod ID)"""
    Amount: float = Field(
        gt=0,
        validation_alias=AliasChoices("Amount", "amount"),
        description="Monto en quetzales",
    )
    PaymentMethodId: str = Field(
        pattern=r"^pm_",
        validation_alias=AliasChoices("PaymentMethodId", "paymentMethodId"),
        description="Stripe PaymentMethod ID (ej: pm_card_visa)",
    )
    SavePaymentMethod: bool = Field(
        default=False,
        validation_alias=AliasChoices("SavePaymentMethod", "savePaymentMethod"),
    )
    IdempotencyKey: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("IdempotencyKey", "idempotencyKey"),
    )


class StripePurchaseCardRequest(BaseStripeSchema):
    """Request para compra de tarjeta ciudadana con Stripe"""
    PaymentMethodId: str = Field(
        pattern=r"^pm_",
        validation_alias=AliasChoices("PaymentMethodId", "paymentMethodId"),
    )
    SavePaymentMethod: bool = Field(
        default=False,
        validation_alias=AliasChoices("SavePaymentMethod", "savePaymentMethod"),
    )
    IdempotencyKey: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("IdempotencyKey", "idempotencyKey"),
    )


class CreatePaymentIntentRequest(BaseStripeSchema):
    """Request para crear PaymentIntent (frontend)"""
    Amount: float = Field(
        gt=0,
        validation_alias=AliasChoices("Amount", "amount"),
    )
    Type: str = Field(
        validation_alias=AliasChoices("Type", "type"),
        pattern=r"^(RECARGA|COMPRA_TARJETA)$",
    )


# ── Stripe Responses ─────────────────────────────────────


class StripePaymentIntentResponse(BaseStripeSchema):
    """Response con client_secret para Stripe Elements"""
    client_secret: str
    payment_intent_id: str


class StripeWebhookEvent(BaseStripeSchema):
    """Evento de webhook de Stripe"""
    id: str
    type: str
    data: dict
    created: int


class StripeWebhookResponse(BaseStripeSchema):
    status: str
    message: Optional[str] = None
    transaction_id: Optional[str] = None
    error: Optional[str] = None