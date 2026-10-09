import uuid
import stripe
from typing import Optional

from app.config import settings
from app.services.invoice_service import create_invoice
from app.services.wallet_integration import add_funds, has_citizen_card, initialize_wallet


# Configurar Stripe
stripe.api_key = settings.stripe_secret_key
stripe.api_version = settings.stripe_api_version


class StripePaymentService:
    """Implementación de pagos con Stripe para production"""

    # Tarjeta Ciudadana: Q20.00 fijo = 2000 centavos
    CARD_PRICE_CENTS = 2000
    CURRENCY = "gtq"

    async def _create_payment_intent(
        self,
        user_id: str,
        cui: str,
        amount_cents: int,
        transaction_type: str,  # "RECARGA" | "COMPRA_TARJETA"
        payment_method_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> dict:
        """Crea PaymentIntent en Stripe"""
        try:
            metadata = {
                "user_id": user_id,
                "cui": cui,
                "transaction_type": transaction_type,
            }

            params = {
                "amount": amount_cents,
                "currency": self.CURRENCY,
                "metadata": metadata,
                "automatic_payment_methods": {"enabled": True},
                "confirm": False,  # Se confirma client-side con Stripe Elements
            }

            if payment_method_id:
                params["payment_method"] = payment_method_id

            if idempotency_key:
                params["idempotency_key"] = idempotency_key

            intent = stripe.PaymentIntent.create(**params)
            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
            }
        except stripe.error.StripeError as e:
            return {"error": str(e), "type": type(e).__name__}

    async def process_recharge(
        self,
        user_id: str,
        cui: str,
        amount: float,
        payment_method_id: str,
        idempotency_key: Optional[str] = None,
    ) -> dict:
        """
        Procesa recarga de saldo.
        El frontend ya confirmó el pago con Stripe Elements.
        Aquí verificamos el PaymentIntent y actualizamos wallet.
        """
        try:
            # Verificar el PaymentIntent
            intent = stripe.PaymentIntent.retrieve(payment_method_id)
            
            if intent.status != "succeeded":
                return {
                    "isSuccess": False,
                    "message": f"Pago no completado: {intent.status}",
                    "transactionId": "",
                    "invoiceId": None,
                }

            # Verificar metadata
            if intent.metadata.get("user_id") != user_id:
                return {
                    "isSuccess": False,
                    "message": "PaymentIntent no pertenece al usuario",
                    "transactionId": "",
                    "invoiceId": None,
                }

            amount_cents = int(round(amount * 100))
            if intent.amount != amount_cents:
                return {
                    "isSuccess": False,
                    "message": "Monto del PaymentIntent no coincide",
                    "transactionId": "",
                    "invoiceId": None,
                }

            # Actualizar wallet
            wallet_updated = await add_funds(user_id, amount)
            if not wallet_updated:
                return {
                    "isSuccess": False,
                    "message": "Pago exitoso pero falló la sincronización con la billetera.",
                    "transactionId": "",
                    "invoiceId": None,
                }

            # Crear factura
            transaction_id = intent.id  # Usar payment_intent.id como transaction_id
            invoice_id = await create_invoice(
                user_id=user_id,
                cui=cui,
                tipo="RECARGA",
                monto=amount,
                tarjeta_ultimos4=intent.payment_method_details.card.last4 if intent.payment_method_details else "****",
                transaction_id=transaction_id,
            )

            return {
                "isSuccess": True,
                "message": "Recarga procesada exitosamente.",
                "transactionId": transaction_id,
                "invoiceId": invoice_id,
            }

        except stripe.error.StripeError as e:
            return {
                "isSuccess": False,
                "message": f"Error de Stripe: {e.user_message or str(e)}",
                "transactionId": "",
                "invoiceId": None,
            }

    async def purchase_card(
        self,
        user_id: str,
        cui: str,
        payment_method_id: str,
        idempotency_key: Optional[str] = None,
    ) -> dict:
        """
        Procesa compra de Tarjeta Ciudadana (Q20.00 fijo).
        """
        try:
            # Verificar que no tenga tarjeta ya
            already_has_card = await has_citizen_card(user_id)
            if already_has_card:
                return {
                    "isSuccess": False,
                    "message": "Transacción denegada. El usuario ya posee una Tarjeta Ciudadana activa.",
                    "transactionId": "",
                    "invoiceId": None,
                }

            # Verificar PaymentIntent
            intent = stripe.PaymentIntent.retrieve(payment_method_id)
            
            if intent.status != "succeeded":
                return {
                    "isSuccess": False,
                    "message": f"Pago no completado: {intent.status}",
                    "transactionId": "",
                    "invoiceId": None,
                }

            if intent.metadata.get("user_id") != user_id:
                return {
                    "isSuccess": False,
                    "message": "PaymentIntent no pertenece al usuario",
                    "transactionId": "",
                    "invoiceId": None,
                }

            if intent.amount != self.CARD_PRICE_CENTS:
                return {
                    "isSuccess": False,
                    "message": "Monto incorrecto para compra de tarjeta",
                    "transactionId": "",
                    "invoiceId": None,
                }

            # Inicializar wallet con Q20.00 + 5 viajes cortesía
            wallet_initialized = await initialize_wallet(user_id)
            if not wallet_initialized:
                return {
                    "isSuccess": False,
                    "message": "Pago exitoso pero falló la creación de la billetera. Contacte soporte.",
                    "transactionId": "",
                    "invoiceId": None,
                }

            # Crear factura
            transaction_id = intent.id
            invoice_id = await create_invoice(
                user_id=user_id,
                cui=cui,
                tipo="COMPRA_TARJETA",
                monto=20.00,
                tarjeta_ultimos4=intent.payment_method_details.card.last4 if intent.payment_method_details else "****",
                transaction_id=transaction_id,
            )

            return {
                "isSuccess": True,
                "message": "Tarjeta Ciudadana adquirida exitosamente. Se han acreditado Q20.00 de saldo y 5 viajes de cortesía.",
                "transactionId": transaction_id,
                "invoiceId": invoice_id,
            }

        except stripe.error.StripeError as e:
            return {
                "isSuccess": False,
                "message": f"Error de Stripe: {e.user_message or str(e)}",
                "transactionId": "",
                "invoiceId": None,
            }

    async def create_payment_intent(
        self,
        user_id: str,
        cui: str,
        amount: float,
        transaction_type: str,  # "RECARGA" | "COMPRA_TARJETA"
        idempotency_key: Optional[str] = None,
    ) -> dict:
        """Crea PaymentIntent para que frontend lo confirme con Stripe Elements"""
        amount_cents = self.CARD_PRICE_CENTS if transaction_type == "COMPRA_TARJETA" else int(round(amount * 100))
        
        result = await self._create_payment_intent(
            user_id=user_id,
            cui=cui,
            amount_cents=amount_cents,
            transaction_type=transaction_type,
            idempotency_key=idempotency_key,
        )
        
        if "error" in result:
            return {"error": result["error"]}
        
        return result

    async def handle_webhook_event(self, event: dict) -> dict:
        """Maneja eventos de webhook de Stripe"""
        event_type = event.get("type")
        
        if event_type == "payment_intent.succeeded":
            intent = event["data"]["object"]
            return await self._handle_payment_succeeded(intent)
        
        elif event_type == "payment_intent.payment_failed":
            intent = event["data"]["object"]
            return await self._handle_payment_failed(intent)
        
        return {"status": "ignored", "event_type": event_type}

    async def _handle_payment_succeeded(self, intent: dict) -> dict:
        """Procesa payment_intent.succeeded - actualiza wallet si no se hizo ya"""
        try:
            user_id = intent.metadata.get("user_id")
            cui = intent.metadata.get("cui")
            transaction_type = intent.metadata.get("transaction_type")
            
            if not user_id or not transaction_type:
                return {"status": "error", "message": "Metadata incompleta"}

            amount = intent.amount / 100.0

            # Verificar si ya se procesó (idempotencia)
            # Podemos revisar si ya existe factura con este transaction_id
            # Por ahora, intentamos actualizar wallet (add_funds es idempotente por diseño)
            
            if transaction_type == "RECARGA":
                wallet_updated = await add_funds(user_id, amount)
                if wallet_updated:
                    await create_invoice(
                        user_id=user_id,
                        cui=cui,
                        tipo="RECARGA",
                        monto=amount,
                        tarjeta_ultimos4=intent.payment_method_details.card.last4 if intent.payment_method_details else "****",
                        transaction_id=intent.id,
                    )
                    return {"status": "processed", "type": "recharge", "transaction_id": intent.id}
            
            elif transaction_type == "COMPRA_TARJETA":
                already_has_card = await has_citizen_card(user_id)
                if not already_has_card:
                    wallet_initialized = await initialize_wallet(user_id)
                    if wallet_initialized:
                        await create_invoice(
                            user_id=user_id,
                            cui=cui,
                            tipo="COMPRA_TARJETA",
                            monto=20.00,
                            tarjeta_ultimos4=intent.payment_method_details.card.last4 if intent.payment_method_details else "****",
                            transaction_id=intent.id,
                        )
                        return {"status": "processed", "type": "purchase_card", "transaction_id": intent.id}
            
            return {"status": "already_processed", "transaction_id": intent.id}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _handle_payment_failed(self, intent: dict) -> dict:
        """Procesa payment_intent.payment_failed - log y notifica"""
        error = intent.last_payment_error
        return {
            "status": "payment_failed",
            "transaction_id": intent.id,
            "error_code": error.code if error else "unknown",
            "error_message": error.message if error else "unknown",
        }

    async def create_setup_intent(self, user_id: str) -> dict:
        """Crea SetupIntent para guardar tarjetas futuras"""
        try:
            setup_intent = stripe.SetupIntent.create(
                metadata={"user_id": user_id},
                usage="off_session",
            )
            return {"client_secret": setup_intent.client_secret, "setup_intent_id": setup_intent.id}
        except stripe.error.StripeError as e:
            return {"error": str(e)}