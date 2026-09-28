"""
Servicio Stripe para T-Conecta
==============================

Maneja la creación de PaymentIntents y confirmación de pagos
usando Stripe en modo TEST (sandbox).

Uso:
    from app.services.stripe_service import create_payment_intent, confirm_payment
    
    # Crear intent
    intent = await create_payment_intent(amount=1000, currency="gtq")  # Q10.00 = 1000 centavos
    
    # Confirmar (opcional, si usas webhooks)
    result = await confirm_payment(payment_intent_id)

Variables de entorno requeridas:
    STRIPE_SECRET_KEY=sk_test_xxx
    STRIPE_API_VERSION=2024-06-20 (opcional)
    STRIPE_WEBHOOK_SECRET=whsec_xxx (opcional, para webhooks)
"""

import os
import stripe
from typing import Optional, Dict, Any

# Configurar Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
stripe.api_version = os.getenv("STRIPE_API_VERSION", "2024-06-20")


class StripeError(Exception):
    """Excepción personalizada para errores de Stripe"""
    def __init__(self, message: str, code: str = None, param: str = None):
        self.message = message
        self.code = code
        self.param = param
        super().__init__(message)


async def create_payment_intent(
    amount: int,           # En centavos: Q10.00 = 1000
    currency: str = "gtq", # GTQ = Quetzales Guatemaltecos
    metadata: Dict[str, str] = None,
    receipt_email: str = None,
) -> Dict[str, Any]:
    """
    Crea un PaymentIntent en Stripe.
    
    Args:
        amount: Monto en centavos (Q10.00 = 1000)
        currency: Moneda ISO 4217 (gtq = Quetzales)
        metadata: Datos extra para vincular con tu sistema
        receipt_email: Email para enviar recibo automático
    
    Returns:
        dict con client_secret, payment_intent_id, amount, currency
    
    Raises:
        StripeError: Si hay error en la API de Stripe
    
    Ejemplo uso en transaction_service.py:
        intent = await create_payment_intent(
            amount=1000,  # Q10.00
            currency="gtq",
            metadata={"user_id": user_id, "tipo": "RECARGA"}
        )
        # Retornar intent.client_secret al frontend
    """
    try:
        params = {
            "amount": amount,
            "currency": currency.lower(),
            "automatic_payment_methods": {"enabled": True},
            # Permite tarjetas, Apple Pay, Google Pay, etc.
        }
        
        if metadata:
            params["metadata"] = metadata
        
        if receipt_email:
            params["receipt_email"] = receipt_email
        
        intent = stripe.PaymentIntent.create(**params)
        
        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "amount": intent.amount,
            "currency": intent.currency,
            "status": intent.status,
        }
    
    except stripe.error.CardError as e:
        raise StripeError(
            message=e.user_message or "Tarjeta rechazada",
            code=e.code,
            param=e.param
        )
    except stripe.error.RateLimitError:
        raise StripeError("Demasiadas peticiones a Stripe", "rate_limit")
    except stripe.error.InvalidRequestError as e:
        raise StripeError(f"Parámetros inválidos: {e.user_message}", "invalid_request")
    except stripe.error.AuthenticationError:
        raise StripeError("Error de autenticación con Stripe (revisa STRIPE_SECRET_KEY)", "auth_error")
    except stripe.error.APIConnectionError:
        raise StripeError("Error de conexión con Stripe", "connection_error")
    except stripe.error.StripeError as e:
        raise StripeError(f"Error de Stripe: {str(e)}", "stripe_error")
    except Exception as e:
        raise StripeError(f"Error inesperado: {str(e)}", "unknown_error")


async def confirm_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
    """
    Confirma manualmente un PaymentIntent (si no usas confirmación automática).
    Normalmente no necesario si usas automatic_payment_methods.enabled=true.
    """
    try:
        intent = stripe.PaymentIntent.confirm(payment_intent_id)
        return {
            "payment_intent_id": intent.id,
            "status": intent.status,
            "amount": intent.amount,
        }
    except stripe.error.StripeError as e:
        raise StripeError(f"Error confirmando pago: {str(e)}", "confirm_error")


async def retrieve_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
    """Obtiene detalles de un PaymentIntent existente"""
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return {
            "payment_intent_id": intent.id,
            "status": intent.status,
            "amount": intent.amount,
            "currency": intent.currency,
            "metadata": intent.metadata,
            "charges": intent.charges.data if intent.charges else [],
        }
    except stripe.error.StripeError as e:
        raise StripeError(f"Error obteniendo pago: {str(e)}", "retrieve_error")


async def create_refund(payment_intent_id: str, amount: int = None) -> Dict[str, Any]:
    """Crea un reembolso (parcial o total)"""
    try:
        params = {"payment_intent": payment_intent_id}
        if amount:
            params["amount"] = amount
        
        refund = stripe.Refund.create(**params)
        return {
            "refund_id": refund.id,
            "status": refund.status,
            "amount": refund.amount,
        }
    except stripe.error.StripeError as e:
        raise StripeError(f"Error creando reembolso: {str(e)}", "refund_error")


# Tarjetas de prueba oficiales Stripe (NO cobran)
TEST_CARDS = {
    "visa_success": "4242424242424242",
    "visa_declined": "4000000000000002",
    "visa_3d_secure": "4000002500003155",
    "mastercard_success": "5555555555554444",
    "amex_success": "378282246310005",
    "discover_success": "6011111111111117",
    # Todas con exp futuro (12/30) y CVV cualquiera (123)
}

# Códigos de error comunes Stripe
ERROR_CODES = {
    "card_declined": "Tarjeta rechazada por el banco",
    "expired_card": "Tarjeta expirada",
    "incorrect_cvc": "CVC incorrecto",
    "processing_error": "Error de procesamiento",
    "rate_limit": "Demasiadas peticiones",
}


def get_test_card(scenario: str = "success") -> Dict[str, str]:
    """Retorna tarjeta de prueba según escenario"""
    cards = {
        "success": {"number": "4242424242424242", "exp": "12/30", "cvc": "123"},
        "declined": {"number": "4000000000000002", "exp": "12/30", "cvc": "123"},
        "3d_secure": {"number": "4000002500003155", "exp": "12/30", "cvc": "123"},
    }
    return cards.get(scenario, cards["success"])