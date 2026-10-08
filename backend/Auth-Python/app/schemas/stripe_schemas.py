"""
Schemas específicos para Stripe - Validación de requests/responses de la API Stripe.
"""

from typing import Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class BaseStripeSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


# ── Requests ──────────────────────────────────────────────


class StripeRechargeRequest(BaseStripeSchema):
    """Request para recarga con Stripe PaymentMethod."""
    Amount: float = Field(
        gt=0,
        validation_alias=AliasChoices("Amount", "amount"),
        description="Monto a recargar en GTQ",
    )
    PaymentMethodId: str = Field(
        pattern=r"^pm_",
        validation_alias=AliasChoices("PaymentMethodId", "paymentMethodId"),
        description="PaymentMethod ID de Stripe (ej: pm_card_visa)",
    )
    SavePaymentMethod: bool = Field(
        default=False,
        validation_alias=AliasChoices("SavePaymentMethod", "savePaymentMethod"),
        description="Guardar PaymentMethod para uso futuro",
    )
    IdempotencyKey: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("IdempotencyKey", "idempotencyKey"),
        description="Clave de idempotencia para evitar duplicados",
    )


class StripePurchaseCardRequest(BaseStripeSchema):
    """Request para compra de tarjeta ciudadana con Stripe."""
    PaymentMethodId: str = Field(
        pattern=r"^pm_",
        validation_alias=AliasChoices("PaymentMethodId", "paymentMethodId"),
        description="PaymentMethod ID de Stripe",
    )
    SavePaymentMethod: bool = Field(
        default=False,
        validation_alias=AliasChoices("SavePaymentMethod", "savePaymentMethod"),
    )
    IdempotencyKey: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("IdempotencyKey", "idempotencyKey"),
    )


class StripeCreatePaymentIntentRequest(BaseStripeSchema):
    """Request para crear PaymentIntent (client-side Stripe Elements)."""
    Amount: float = Field(
        gt=0,
        validation_alias=AliasChoices("Amount", "amount"),
    )
    TransactionType: str = Field(
        default="RECARGA",
        validation_alias=AliasChoices("TransactionType", "transactionType"),
        pattern=r"^(RECARGA|COMPRA_TARJETA)$",
    )
    SavePaymentMethod: bool = Field(
        default=False,
        validation_alias=AliasChoices("SavePaymentMethod", "savePaymentMethod"),
    )


class StripeConfirmPaymentRequest(BaseStripeSchema):
    """Request para confirmar pago desde frontend con client_secret."""
    PaymentIntentId: str = Field(
        validation_alias=AliasChoices("PaymentIntentId", "paymentIntentId"),
    )
    PaymentMethodId: str = Field(
        pattern=r"^pm_",
        validation_alias=AliasChoices("PaymentMethodId", "paymentMethodId"),
    )


# ── Responses ─────────────────────────────────────────────


class StripePaymentIntentResponse(BaseStripeSchema):
    """Response con client_secret para Stripe Elements."""
    id: str
    client_secret: str
    amount: int
    currency: str
    status: str


class StripeSetupIntentResponse(BaseStripeSchema):
    """Response para SetupIntent (guardar tarjeta)."""
    id: str
    client_secret: str
    status: str


class StripeTransactionResponse(BaseStripeSchema):
    """Response unificado para transacciones Stripe."""
    isSuccess: bool
    message: str
    transactionId: str
    invoiceId: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    amount_received: Optional[float] = None
    stripe_status: Optional[str] = None
    stripe_error_code: Optional[str] = None
    stripe_decline_code: Optional[str] = None
    requires_reconciliation: bool = False


# ── Webhook ───────────────────────────────────────────────


class StripeWebhookEvent(BaseStripeSchema):
    """Evento de webhook de Stripe parseado."""
    id: str
    type: str
    data: dict
    created: Optional[int] = None


class StripeWebhookResponse(BaseStripeSchema):
    """Response estándar para webhook."""
    status: str  # success | error
    message: Optional[str] = None


# ── Error ─────────────────────────────────────────────────


class StripeErrorResponse(BaseStripeSchema):
    """Error response de Stripe."""
    StatusCode: int
    Message: str
    Detailed: Optional[str] = None
    StripeErrorCode: Optional[str] = None
    StripeDeclineCode: Optional[str] = None