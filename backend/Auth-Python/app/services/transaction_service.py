"""
Servicio de Simulación de Pagos (Development)

Implementa el flujo de pago actual basado en validación Luhn + delay simulado.
Se usa cuando ENVIRONMENT=development o no hay credenciales Stripe configuradas.
"""

import asyncio
import uuid

from app.config import settings
from app.helpers.luhn import is_valid_luhn
from app.services.invoice_service import create_invoice
from app.services.wallet_integration import add_funds, has_citizen_card, initialize_wallet


class SimulationPaymentService:
    """Servicio de simulación de pagos para entorno de desarrollo."""

    async def process_recharge(self, user_id: str, cui: str, card_number: str, amount: float) -> dict:
        """
        Procesa una recarga simulada.
        
        Args:
            user_id: ID del usuario
            cui: CUI del usuario
            card_number: Número de tarjeta (se valida con Luhn)
            amount: Monto a recargar
            
        Returns:
            Dict con resultado de la transacción
        """
        if not is_valid_luhn(card_number):
            return {
                "isSuccess": False,
                "message": "Número de tarjeta inválida.",
                "transactionId": "",
                "invoiceId": None,
            }

        # Simular latencia de pasarela de pago
        await asyncio.sleep(1.5)

        wallet_updated = await add_funds(user_id, amount)

        if not wallet_updated:
            return {
                "isSuccess": False,
                "message": "Transacción aprobada, pero falló la sincronización con la billetera.",
                "transactionId": "",
                "invoiceId": None,
            }

        transaction_id = str(uuid.uuid4())
        invoice_id = await create_invoice(
            user_id=user_id,
            cui=cui,
            tipo="RECARGA",
            monto=amount,
            tarjeta_ultimos4=card_number[-4:],
            transaction_id=transaction_id,
        )

        return {
            "isSuccess": True,
            "message": "Recarga procesada exitosamente.",
            "transactionId": transaction_id,
            "invoiceId": invoice_id,
        }

    async def process_purchase_card(self, user_id: str, cui: str, card_number: str, amount: float) -> dict:
        """
        Procesa compra de tarjeta ciudadana simulada.
        
        Args:
            user_id: ID del usuario
            cui: CUI del usuario
            card_number: Número de tarjeta (se valida con Luhn)
            amount: Debe ser exactamente 20.00
            
        Returns:
            Dict con resultado de la transacción
        """
        if amount != 20.00:
            return {
                "isSuccess": False,
                "message": "El costo de emisión de la Tarjeta Ciudadana es exactamente Q20.00.",
                "transactionId": "",
                "invoiceId": None,
            }

        if not is_valid_luhn(card_number):
            return {
                "isSuccess": False,
                "message": "Número de tarjeta inválida.",
                "transactionId": "",
                "invoiceId": None,
            }

        already_has_card = await has_citizen_card(user_id)
        if already_has_card:
            return {
                "isSuccess": False,
                "message": "Transacción denegada. El usuario ya posee una Tarjeta Ciudadana activa.",
                "transactionId": "",
                "invoiceId": None,
            }

        # Simular latencia de pasarela de pago
        await asyncio.sleep(1.5)

        wallet_initialized = await initialize_wallet(user_id)

        if not wallet_initialized:
            return {
                "isSuccess": False,
                "message": "Transacción aprobada, pero falló la creación de la billetera. Contacte soporte.",
                "transactionId": "",
                "invoiceId": None,
            }

        transaction_id = str(uuid.uuid4())
        invoice_id = await create_invoice(
            user_id=user_id,
            cui=cui,
            tipo="COMPRA_TARJETA",
            monto=20.00,
            tarjeta_ultimos4=card_number[-4:],
            transaction_id=transaction_id,
        )

        return {
            "isSuccess": True,
            "message": "Tarjeta Ciudadana adquirida exitosamente. Se han acreditado Q20.00 de saldo y 5 viajes de cortesía.",
            "transactionId": transaction_id,
            "invoiceId": invoice_id,
        }

    async def create_payment_intent(self, amount: float, metadata: dict) -> dict:
        """
        Simula creación de PaymentIntent para compatibilidad con frontend.
        En simulación retorna un client_secret falso.
        """
        import uuid
        fake_intent_id = f"pi_sim_{uuid.uuid4().hex[:24]}"
        return {
            "id": fake_intent_id,
            "client_secret": f"{fake_intent_id}_secret_{uuid.uuid4().hex[:16]}",
            "amount": round(amount * 100),
            "currency": "gtq",
            "status": "requires_payment_method",
        }


# Mantener compatibilidad hacia atrás con funciones existentes
async def process_payment(user_id: str, cui: str, card_number: str, amount: float) -> dict:
    """Función legacy - usar SimulationPaymentService().process_recharge()"""
    service = SimulationPaymentService()
    return await service.process_recharge(user_id, cui, card_number, amount)


async def purchase_card(user_id: str, cui: str, card_number: str, amount: float) -> dict:
    """Función legacy - usar SimulationPaymentService().process_purchase_card()"""
    service = SimulationPaymentService()
    return await service.process_purchase_card(user_id, cui, card_number, amount)


async def process_stripe_payment(
    user_id: str,
    cui: str,
    amount: float,
    payment_method_id: str,
) -> dict:
    """Función legacy - redirige a StripePaymentService si está disponible"""
    from app.services.payment_gateway_factory import get_payment_service
    service = get_payment_service()
    if hasattr(service, 'process_recharge_stripe'):
        return await service.process_recharge_stripe(user_id, cui, amount, payment_method_id)
    # Fallback a simulación si no hay Stripe
    return await service.process_recharge(user_id, cui, "4242424242424242", amount)