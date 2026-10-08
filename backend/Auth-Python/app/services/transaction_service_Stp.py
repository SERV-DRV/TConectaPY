"""
Servicio de Pagos con Stripe (Production)

Implementa el flujo de pago real usando Stripe PaymentIntents y PaymentMethods.
Se usa cuando ENVIRONMENT=production y hay credenciales Stripe válidas.

NOTA: Usar PaymentMethod IDs (pm_...) NUNCA números de tarjeta directos para cumplimiento PCI.
"""

import asyncio
import uuid

import stripe

from app.config import settings
from app.database import async_session_factory
from app.models.user import User
from app.services.invoice_service import create_invoice
from app.services.wallet_integration import add_funds, has_citizen_card, initialize_wallet
from sqlalchemy import select

# Configurar la API key de Stripe
stripe.api_key = settings.stripe_secret_key
stripe.api_version = settings.stripe_api_version

# PaymentMethod IDs de prueba de Stripe que requieren autorización especial
STRIPE_TEST_PAYMENT_METHODS = {
    "pm_card_visa",
    "pm_card_mastercard",
    "pm_card_amex",
    "pm_card_discover",
    "pm_card_diners",
    "pm_card_jcb",
    "pm_card_unionpay",
    "pm_card_chargeDeclined",
    "pm_card_chargeDeclinedInsufficientFunds",
    "pm_card_chargeDeclinedLostCard",
    "pm_card_chargeDeclinedStolenCard",
    "pm_card_chargeDeclinedExpiredCard",
    "pm_card_chargeDeclinedIncorrectCvc",
    "pm_card_chargeDeclinedProcessingError",
}


class StripePaymentService:
    """Servicio de pagos real con Stripe para entorno de producción."""

    # Moneda: GTQ (Quetzales Guatemaltecos) - Stripe lo soporta desde 2024
    CURRENCY = "gtq"
    CARD_AMOUNT_FIXED = 20.00  # Q20.00 para tarjeta ciudadana

    async def _check_stripe_test_allowed(self, user_id: str) -> bool:
        """
        Verifica si el usuario tiene permiso para usar tarjetas de prueba de Stripe.
        
        Solo aplica en production con PaymentMethod IDs de prueba (pm_card_visa, etc.).
        """
        async with async_session_factory() as session:
            result = await session.execute(
                select(User.stripe_test_allowed).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            return user is True

    async def _is_test_payment_method(self, payment_method_id: str) -> bool:
        """Verifica si el PaymentMethod ID es uno de prueba de Stripe."""
        return payment_method_id in STRIPE_TEST_PAYMENT_METHODS

    async def process_recharge_stripe(
        self,
        user_id: str,
        cui: str,
        amount: float,
        payment_method_id: str,
        idempotency_key: str | None = None,
    ) -> dict:
        """
        Procesa una recarga usando Stripe PaymentIntent.
        
        Args:
            user_id: ID del usuario
            cui: CUI del usuario
            amount: Monto a recargar en GTQ
            payment_method_id: PaymentMethod ID de Stripe (ej: pm_card_visa)
            idempotency_key: Clave de idempotencia opcional para evitar duplicados
            
        Returns:
            Dict con resultado de la transacción
        """
        # Validar PaymentMethod ID format
        if not payment_method_id.startswith("pm_"):
            return {
                "isSuccess": False,
                "message": "PaymentMethod ID inválido. Use formato pm_...",
                "transactionId": "",
                "invoiceId": None,
            }

        if amount <= 0:
            return {
                "isSuccess": False,
                "message": "El monto debe ser mayor a 0.",
                "transactionId": "",
                "invoiceId": None,
            }

        # Verificar permisos para PaymentMethods de prueba
        if await self._is_test_payment_method(payment_method_id):
            allowed = await self._check_stripe_test_allowed(user_id)
            if not allowed:
                return {
                    "isSuccess": False,
                    "message": "Este usuario no está autorizado para usar tarjetas de prueba de Stripe. Contacte al administrador.",
                    "transactionId": "",
                    "invoiceId": None,
                    "stripe_error_code": "test_card_not_allowed",
                }

        try:
            # Crear y confirmar PaymentIntent en Stripe
            # Usamos asyncio.to_thread porque el SDK de Stripe es síncrono
            intent = await asyncio.to_thread(
                stripe.PaymentIntent.create,
                amount=round(amount * 100),  # Stripe usa centavos (Q10.00 = 1000)
                currency=self.CURRENCY,
                payment_method=payment_method_id,
                confirm=True,
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "never",  # No permitir redirecciones (ej. 3D Secure)
                },
                metadata={
                    "user_id": user_id,
                    "cui": cui,
                    "transaction_type": "RECARGA",
                },
                idempotency_key=idempotency_key,
            )
        except stripe.error.CardError as error:
            # Error de tarjeta (rechazada, fondos insuficientes, etc.)
            return {
                "isSuccess": False,
                "message": error.user_message or "El pago fue rechazado.",
                "transactionId": "",
                "invoiceId": None,
                "stripe_error_code": error.code,
                "stripe_decline_code": error.decline_code,
            }
        except stripe.error.RateLimitError:
            return {
                "isSuccess": False,
                "message": "Demasiadas solicitudes. Intente nuevamente en unos minutos.",
                "transactionId": "",
                "invoiceId": None,
                "stripe_error_code": "rate_limit",
            }
        except stripe.error.InvalidRequestError as error:
            return {
                "isSuccess": False,
                "message": f"Solicitud inválida: {error.user_message}",
                "transactionId": "",
                "invoiceId": None,
                "stripe_error_code": "invalid_request",
            }
        except stripe.error.AuthenticationError:
            return {
                "isSuccess": False,
                "message": "Error de autenticación con Stripe. Contacte soporte.",
                "transactionId": "",
                "invoiceId": None,
                "stripe_error_code": "authentication_error",
            }
        except stripe.error.APIConnectionError:
            return {
                "isSuccess": False,
                "message": "Error de conexión con Stripe. Intente nuevamente.",
                "transactionId": "",
                "invoiceId": None,
                "stripe_error_code": "api_connection",
            }
        except stripe.error.StripeError as error:
            # Otros errores de Stripe
            return {
                "isSuccess": False,
                "message": f"Error en el procesamiento del pago: {error.user_message or str(error)}",
                "transactionId": "",
                "invoiceId": None,
                "stripe_error_code": "stripe_error",
            }

        # Verificar que el pago fue exitoso
        if intent.status != "succeeded":
            return {
                "isSuccess": False,
                "message": f"El pago requiere una acción adicional: {intent.status}.",
                "transactionId": intent.id,
                "invoiceId": None,
                "stripe_status": intent.status,
                "stripe_next_action": getattr(intent, 'next_action', None),
            }

        # Actualizar la billetera en MongoDB
        wallet_updated = await add_funds(user_id, amount)
        if not wallet_updated:
            # IMPORTANTE: El pago en Stripe SÍ se procesó, pero falló la sincronización
            # El webhook payment_intent.succeeded manejará la reconciliación
            return {
                "isSuccess": False,
                "message": "Pago aprobado en Stripe, pero falló la sincronización con la billetera. Se reconciliará automáticamente.",
                "transactionId": intent.id,
                "invoiceId": None,
                "requires_reconciliation": True,
            }

        # Crear factura en MongoDB con el PaymentIntent ID como trazabilidad
        invoice_id = await create_invoice(
            user_id=user_id,
            cui=cui,
            tipo="RECARGA",
            monto=amount,
            tarjeta_ultimos4="",  # No guardamos últimos 4 dígitos con PaymentMethod
            transaction_id=intent.id,
        )

        return {
            "isSuccess": True,
            "message": "Recarga procesada exitosamente.",
            "transactionId": intent.id,
            "invoiceId": invoice_id,
            "stripe_payment_intent_id": intent.id,
            "amount_received": intent.amount_received / 100,
        }

    async def process_purchase_card_stripe(
        self,
        user_id: str,
        cui: str,
        payment_method_id: str,
        idempotency_key: str | None = None,
    ) -> dict:
        """
        Procesa compra de tarjeta ciudadana (Q20.00 fijo) usando Stripe.
        
        Args:
            user_id: ID del usuario
            cui: CUI del usuario
            payment_method_id: PaymentMethod ID de Stripe (ej: pm_card_visa)
            idempotency_key: Clave de idempotencia opcional
            
        Returns:
            Dict con resultado de la transacción
        """
        # Validar PaymentMethod ID format
        if not payment_method_id.startswith("pm_"):
            return {
                "isSuccess": False,
                "message": "PaymentMethod ID inválido. Use formato pm_...",
                "transactionId": "",
                "invoiceId": None,
            }

        # Verificar permisos para PaymentMethods de prueba
        if await self._is_test_payment_method(payment_method_id):
            allowed = await self._check_stripe_test_allowed(user_id)
            if not allowed:
                return {
                    "isSuccess": False,
                    "message": "Este usuario no está autorizado para usar tarjetas de prueba de Stripe. Contacte al administrador.",
                    "transactionId": "",
                    "invoiceId": None,
                    "stripe_error_code": "test_card_not_allowed",
                }

        # Verificar si ya tiene tarjeta ciudadana
        already_has_card = await has_citizen_card(user_id)
        if already_has_card:
            return {
                "isSuccess": False,
                "message": "Transacción denegada. El usuario ya posee una Tarjeta Ciudadana activa.",
                "transactionId": "",
                "invoiceId": None,
            }

        amount = self.CARD_AMOUNT_FIXED

        try:
            # Crear y confirmar PaymentIntent para compra de tarjeta
            intent = await asyncio.to_thread(
                stripe.PaymentIntent.create,
                amount=round(amount * 100),  # 2000 centavos = Q20.00
                currency=self.CURRENCY,
                payment_method=payment_method_id,
                confirm=True,
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "never",
                },
                metadata={
                    "user_id": user_id,
                    "cui": cui,
                    "transaction_type": "COMPRA_TARJETA",
                },
                idempotency_key=idempotency_key,
            )
        except stripe.error.CardError as error:
            return {
                "isSuccess": False,
                "message": error.user_message or "El pago fue rechazado.",
                "transactionId": "",
                "invoiceId": None,
                "stripe_error_code": error.code,
                "stripe_decline_code": error.decline_code,
            }
        except stripe.error.StripeError as error:
            return {
                "isSuccess": False,
                "message": f"Error en el procesamiento del pago: {error.user_message or str(error)}",
                "transactionId": "",
                "invoiceId": None,
                "stripe_error_code": getattr(error, 'code', 'unknown'),
            }

        # Verificar que el pago fue exitoso
        if intent.status != "succeeded":
            return {
                "isSuccess": False,
                "message": f"El pago requiere una acción adicional: {intent.status}.",
                "transactionId": intent.id,
                "invoiceId": None,
                "stripe_status": intent.status,
            }

        # Inicializar billetera con tarjeta ciudadana (saldo Q20 + 5 viajes cortesía)
        wallet_initialized = await initialize_wallet(user_id)
        if not wallet_initialized:
            return {
                "isSuccess": False,
                "message": "Pago aprobado, pero falló la creación de la billetera. Contacte soporte.",
                "transactionId": intent.id,
                "invoiceId": None,
                "requires_reconciliation": True,
            }

        # Crear factura
        invoice_id = await create_invoice(
            user_id=user_id,
            cui=cui,
            tipo="COMPRA_TARJETA",
            monto=amount,
            tarjeta_ultimos4="",
            transaction_id=intent.id,
        )

        return {
            "isSuccess": True,
            "message": "Tarjeta Ciudadana adquirida exitosamente. Se han acreditado Q20.00 de saldo y 5 viajes de cortesía.",
            "transactionId": intent.id,
            "invoiceId": invoice_id,
            "stripe_payment_intent_id": intent.id,
            "amount_received": intent.amount_received / 100,
        }

    async def create_payment_intent(
        self,
        amount: float,
        metadata: dict,
        idempotency_key: str | None = None,
    ) -> dict:
        """
        Crea un PaymentIntent sin confirmar (para uso con Stripe Elements en frontend).
        
        Args:
            amount: Monto en GTQ
            metadata: Metadata para el PaymentIntent
            idempotency_key: Clave de idempotencia opcional
            
        Returns:
            Dict con id y client_secret del PaymentIntent
        """
        try:
            intent = await asyncio.to_thread(
                stripe.PaymentIntent.create,
                amount=round(amount * 100),
                currency=self.CURRENCY,
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "never",
                },
                metadata=metadata,
                idempotency_key=idempotency_key,
            )
            return {
                "id": intent.id,
                "client_secret": intent.client_secret,
                "amount": intent.amount,
                "currency": intent.currency,
                "status": intent.status,
            }
        except stripe.error.StripeError as error:
            raise ValueError(f"Error creando PaymentIntent: {error.user_message or str(error)}")

    async def create_setup_intent(self, user_id: str, cui: str) -> dict:
        """
        Crea un SetupIntent para guardar PaymentMethod para uso futuro.
        
        Args:
            user_id: ID del usuario
            cui: CUI del usuario
            
        Returns:
            Dict con client_secret del SetupIntent
        """
        try:
            setup_intent = await asyncio.to_thread(
                stripe.SetupIntent.create,
                automatic_payment_methods={"enabled": True},
                metadata={"user_id": user_id, "cui": cui},
            )
            return {
                "id": setup_intent.id,
                "client_secret": setup_intent.client_secret,
                "status": setup_intent.status,
            }
        except stripe.error.StripeError as error:
            raise ValueError(f"Error creando SetupIntent: {error.user_message or str(error)}")

    async def handle_webhook_event(self, event: dict) -> dict:
        """
        Maneja eventos de webhook de Stripe.
        
        Args:
            event: Evento de Stripe parseado
            
        Returns:
            Dict con resultado del manejo
        """
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        if event_type == "payment_intent.succeeded":
            return await self._handle_payment_intent_succeeded(data)
        elif event_type == "payment_intent.payment_failed":
            return await self._handle_payment_intent_failed(data)
        elif event_type == "payment_intent.canceled":
            return await self._handle_payment_intent_canceled(data)
        elif event_type == "setup_intent.succeeded":
            return await self._handle_setup_intent_succeeded(data)
        else:
            return {"status": "ignored", "event_type": event_type}

    async def _handle_payment_intent_succeeded(self, payment_intent: dict) -> dict:
        """Maneja payment_intent.succeeded - actualiza wallet si no se hizo en la request original."""
        payment_intent_id = payment_intent["id"]
        metadata = payment_intent.get("metadata", {})
        user_id = metadata.get("user_id")
        cui = metadata.get("cui")
        transaction_type = metadata.get("transaction_type", "RECARGA")
        amount = payment_intent["amount_received"] / 100

        # Verificar si ya existe factura para este PaymentIntent
        from app.services.invoice_service import get_invoice_by_transaction_id
        existing_invoice = await get_invoice_by_transaction_id(payment_intent_id)

        if existing_invoice:
            return {"status": "already_processed", "payment_intent_id": payment_intent_id}

        # Actualizar wallet si no se hizo antes
        wallet_updated = await add_funds(user_id, amount)
        if not wallet_updated:
            return {
                "status": "wallet_sync_failed",
                "payment_intent_id": payment_intent_id,
                "message": "Pago exitoso pero falló sincronización wallet - requiere intervención manual",
            }

        # Crear factura
        invoice_id = await create_invoice(
            user_id=user_id,
            cui=cui,
            tipo=transaction_type,
            monto=amount,
            tarjeta_ultimos4="",
            transaction_id=payment_intent_id,
        )

        return {
            "status": "processed",
            "payment_intent_id": payment_intent_id,
            "invoice_id": invoice_id,
            "amount": amount,
        }

    async def _handle_payment_intent_failed(self, payment_intent: dict) -> dict:
        """Maneja payment_intent.payment_failed - registra el fallo."""
        payment_intent_id = payment_intent["id"]
        last_error = payment_intent.get("last_payment_error", {})
        
        return {
            "status": "payment_failed",
            "payment_intent_id": payment_intent_id,
            "error_code": last_error.get("code"),
            "error_message": last_error.get("message"),
            "decline_code": last_error.get("decline_code"),
        }

    async def _handle_payment_intent_canceled(self, payment_intent: dict) -> dict:
        """Maneja payment_intent.canceled."""
        return {
            "status": "canceled",
            "payment_intent_id": payment_intent["id"],
        }

    async def _handle_setup_intent_succeeded(self, setup_intent: dict) -> dict:
        """Maneja setup_intent.succeeded - PaymentMethod guardado para futuro uso."""
        return {
            "status": "setup_complete",
            "setup_intent_id": setup_intent["id"],
            "payment_method": setup_intent.get("payment_method"),
        }

    # Métodos de compatibilidad para la interfaz común
    async def process_recharge(self, user_id: str, cui: str, card_number: str, amount: float) -> dict:
        """Compatibilidad: redirige a Stripe si se pasa PaymentMethod ID, sino falla."""
        if card_number.startswith("pm_"):
            return await self.process_recharge_stripe(user_id, cui, amount, card_number)
        return {
            "isSuccess": False,
            "message": "En production se requiere PaymentMethod ID de Stripe (pm_...). Use Stripe Elements en frontend.",
            "transactionId": "",
            "invoiceId": None,
        }

    async def process_purchase_card(self, user_id: str, cui: str, card_number: str, amount: float) -> dict:
        """Compatibilidad: redirige a Stripe si se pasa PaymentMethod ID."""
        if card_number.startswith("pm_"):
            return await self.process_purchase_card_stripe(user_id, cui, card_number)
        return {
            "isSuccess": False,
            "message": "En production se requiere PaymentMethod ID de Stripe (pm_...). Use Stripe Elements en frontend.",
            "transactionId": "",
            "invoiceId": None,
        }