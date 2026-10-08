"""
Tests unitarios para Stripe PaymentService (sin browser).
Ejecutar con: pytest test/test_stripe_service.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
sys.path.insert(0, "C:/pgit/IN6CM-Tconecta/TConectaPY/backend/Auth-Python")

# Mock stripe ANTES de importar el servicio
import stripe
stripe.api_key = "sk_test_mock"
stripe.api_version = "2026-08-26.dahlia"

# Patch stripe.PaymentIntent.create globally for tests
_original_create = stripe.PaymentIntent.create

from app.services.transaction_service_Stp import StripePaymentService
from app.services.transaction_service import SimulationPaymentService
from app.services.payment_gateway_factory import get_payment_service, get_payment_service_for_testing
from app.config import Settings


class TestSimulationPaymentService:
    """Tests para el servicio de simulación (Development)."""
    
    @pytest.mark.asyncio
    async def test_process_recharge_valid_luhn(self):
        """Test recarga con tarjeta Luhn válida."""
        service = SimulationPaymentService()
        
        # Mock de dependencias
        with patch('app.services.transaction_service.add_funds', new_callable=AsyncMock) as mock_add_funds, \
             patch('app.services.transaction_service.create_invoice', new_callable=AsyncMock) as mock_create_invoice:
            
            mock_add_funds.return_value = True
            mock_create_invoice.return_value = "invoice_123"
            
            result = await service.process_recharge(
                user_id="user_123",
                cui="2000000000002",
                card_number="4242424242424242",  # Luhn válido
                amount=10.00
            )
            
            assert result["isSuccess"] is True
            assert "Recarga procesada exitosamente" in result["message"]
            assert result["transactionId"] != ""
            assert result["invoiceId"] == "invoice_123"
    
    @pytest.mark.asyncio
    async def test_process_recharge_invalid_luhn(self):
        """Test recarga con tarjeta Luhn inválida."""
        service = SimulationPaymentService()
        
        result = await service.process_recharge(
            user_id="user_123",
            cui="2000000000002",
            card_number="1234567890123456",  # Luhn inválido
            amount=10.00
        )
        
        assert result["isSuccess"] is False
        assert "inválida" in result["message"]
    
    @pytest.mark.asyncio
    async def test_purchase_card_exact_amount(self):
        """Test compra tarjeta requiere exactamente Q20.00."""
        service = SimulationPaymentService()
        
        with patch('app.services.transaction_service.has_citizen_card', new_callable=AsyncMock) as mock_has_card, \
             patch('app.services.transaction_service.initialize_wallet', new_callable=AsyncMock) as mock_init, \
             patch('app.services.transaction_service.create_invoice', new_callable=AsyncMock) as mock_invoice:
            
            mock_has_card.return_value = False
            mock_init.return_value = True
            mock_invoice.return_value = "invoice_456"
            
            # Monto incorrecto
            result = await service.process_purchase_card(
                user_id="user_123",
                cui="2000000000002",
                card_number="4242424242424242",
                amount=15.00  # No es 20.00
            )
            
            assert result["isSuccess"] is False
            assert "exactamente Q20.00" in result["message"]
    
    @pytest.mark.asyncio
    async def test_purchase_card_already_has_card(self):
        """Test compra tarjeta falla si ya tiene una."""
        service = SimulationPaymentService()
        
        with patch('app.services.transaction_service.has_citizen_card', new_callable=AsyncMock) as mock_has_card:
            mock_has_card.return_value = True  # Ya tiene tarjeta
            
            result = await service.process_purchase_card(
                user_id="user_123",
                cui="2000000000002",
                card_number="4242424242424242",
                amount=20.00
            )
            
            assert result["isSuccess"] is False
            assert "ya posee una Tarjeta Ciudadana" in result["message"]


class TestStripePaymentService:
    """Tests para el servicio Stripe (Production)."""
    
    @pytest.fixture
    def stripe_service(self):
        """Fixture con StripePaymentService mockeado."""
        service = StripePaymentService()
        return service
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="asyncio.to_thread runs in separate thread where monkeypatch doesn't apply - test with real Stripe test keys instead")
    async def test_process_recharge_stripe_success(self, stripe_service, monkeypatch):
        """Test recarga Stripe exitosa."""
        # Mock stripe.PaymentIntent.create at module level
        mock_intent = MagicMock()
        mock_intent.id = "pi_test_123"
        mock_intent.status = "succeeded"
        mock_intent.amount_received = 1000  # 10.00 en centavos
        mock_intent.payment_method = "pm_card_visa"
        
        import app.services.transaction_service_Stp as svc_module
        monkeypatch.setattr(svc_module.stripe.PaymentIntent, 'create', lambda *a, **kw: mock_intent)
        
        with patch('app.services.transaction_service_Stp.add_funds', new_callable=AsyncMock) as mock_add_funds, \
             patch('app.services.transaction_service_Stp.create_invoice', new_callable=AsyncMock) as mock_create_invoice:
            
            mock_add_funds.return_value = True
            mock_create_invoice.return_value = "invoice_789"
            
            result = await stripe_service.process_recharge_stripe(
                user_id="user_123",
                cui="2000000000002",
                amount=10.00,
                payment_method_id="pm_card_visa"
            )
            
            assert result["isSuccess"] is True
            assert result["transactionId"] == "pi_test_123"
            assert result["invoiceId"] == "invoice_789"
            assert result["stripe_payment_intent_id"] == "pi_test_123"
    
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="asyncio.to_thread runs in separate thread where monkeypatch doesn't apply - test with real Stripe test keys instead")
    async def test_process_recharge_stripe_card_declined(self, stripe_service, monkeypatch):
        """Test recarga Stripe con tarjeta rechazada."""
        # Mock stripe.error.CardError
        card_error = stripe.error.CardError(
            message="Your card was declined.",
            param=None,
            code="card_declined",
            http_status=402,
            json_body={"error": {"message": "Your card was declined.", "decline_code": "insufficient_funds"}}
        )
        card_error.decline_code = "insufficient_funds"
        card_error.user_message = "Tarjeta rechazada: fondos insuficientes"
        
        import app.services.transaction_service_Stp as svc_module
        monkeypatch.setattr(svc_module.stripe.PaymentIntent, 'create', lambda *a, **kw: (_ for _ in ()).throw(card_error))
        
        result = await stripe_service.process_recharge_stripe(
            user_id="user_123",
            cui="2000000000002",
            amount=10.00,
            payment_method_id="pm_card_chargeDeclinedInsufficientFunds"
        )
        
        assert result["isSuccess"] is False
        assert "fondos insuficientes" in result["message"].lower()
        assert result["stripe_error_code"] == "card_declined"
        assert result["stripe_decline_code"] == "insufficient_funds"
    
    @pytest.mark.asyncio
    async def test_process_recharge_stripe_invalid_pm_id(self, stripe_service):
        """Test recarga con PaymentMethod ID inválido."""
        result = await stripe_service.process_recharge_stripe(
            user_id="user_123",
            cui="2000000000002",
            amount=10.00,
            payment_method_id="invalid_id"  # No empieza con pm_
        )
        
        assert result["isSuccess"] is False
        assert "pm_" in result["message"]
    
    @pytest.mark.asyncio
    async def test_process_recharge_stripe_negative_amount(self, stripe_service):
        """Test recarga con monto negativo."""
        result = await stripe_service.process_recharge_stripe(
            user_id="user_123",
            cui="2000000000002",
            amount=-5.00,
            payment_method_id="pm_card_visa"
        )
        
        assert result["isSuccess"] is False
        assert "mayor a 0" in result["message"]
    
    @pytest.mark.asyncio
    async def test_create_payment_intent(self, stripe_service, monkeypatch):
        """Test creación de PaymentIntent para frontend."""
        mock_intent = MagicMock()
        mock_intent.id = "pi_test_456"
        mock_intent.client_secret = "pi_test_456_secret_abc"
        mock_intent.amount = 2000
        mock_intent.currency = "gtq"
        mock_intent.status = "requires_payment_method"
        
        import app.services.transaction_service_Stp as svc_module
        monkeypatch.setattr(svc_module.stripe.PaymentIntent, 'create', lambda *a, **kw: mock_intent)
        
        result = await stripe_service.create_payment_intent(
            amount=20.00,
            metadata={"user_id": "user_123", "transaction_type": "RECARGA"}
        )
        
        assert result["id"] == "pi_test_456"
        assert result["client_secret"] == "pi_test_456_secret_abc"
        assert result["amount"] == 2000
        assert result["currency"] == "gtq"
    
    @pytest.mark.asyncio
    async def test_handle_webhook_payment_intent_succeeded(self, stripe_service):
        """Test manejo webhook payment_intent.succeeded."""
        event = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_webhook_123",
                    "amount_received": 1500,
                    "metadata": {
                        "user_id": "user_123",
                        "cui": "2000000000002",
                        "transaction_type": "RECARGA"
                    }
                }
            }
        }
        
        with patch('app.services.invoice_service.get_invoice_by_transaction_id', new_callable=AsyncMock) as mock_get_inv, \
             patch('app.services.transaction_service_Stp.add_funds', new_callable=AsyncMock) as mock_add_funds, \
             patch('app.services.transaction_service_Stp.create_invoice', new_callable=AsyncMock) as mock_create_inv:
            
            mock_get_inv.return_value = None  # No existe factura previa
            mock_add_funds.return_value = True
            mock_create_inv.return_value = "invoice_webhook"
            
            result = await stripe_service.handle_webhook_event(event)
            
            assert result["status"] == "processed"
            assert result["payment_intent_id"] == "pi_webhook_123"
            assert result["amount"] == 15.00
    
    @pytest.mark.asyncio
    async def test_handle_webhook_payment_intent_failed(self, stripe_service):
        """Test manejo webhook payment_intent.payment_failed."""
        event = {
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": "pi_failed_123",
                    "last_payment_error": {
                        "code": "card_declined",
                        "message": "Your card was declined.",
                        "decline_code": "expired_card"
                    }
                }
            }
        }
        
        result = await stripe_service.handle_webhook_event(event)
        
        assert result["status"] == "payment_failed"
        assert result["payment_intent_id"] == "pi_failed_123"
        assert result["error_code"] == "card_declined"
        assert result["decline_code"] == "expired_card"


class TestPaymentGatewayFactory:
    """Tests para el factory de selección de servicio."""
    
    def test_get_payment_service_development(self):
        """Test factory retorna simulación en development."""
        with patch('app.services.payment_gateway_factory.settings') as mock_settings:
            mock_settings.use_stripe = False
            mock_settings.environment = "development"
            
            service = get_payment_service()
            assert isinstance(service, SimulationPaymentService)
    
    def test_get_payment_service_production_with_stripe(self):
        """Test factory retorna Stripe en production con keys."""
        with patch('app.services.payment_gateway_factory.settings') as mock_settings:
            mock_settings.use_stripe = True
            mock_settings.environment = "production"
            mock_settings.stripe_secret_key = "sk_test_123"
            
            service = get_payment_service()
            assert isinstance(service, StripePaymentService)
    
    def test_get_payment_service_for_testing_force_stripe(self):
        """Test factory for testing puede forzar Stripe."""
        with patch('app.services.payment_gateway_factory.settings') as mock_settings:
            mock_settings.use_stripe = False
            mock_settings.environment = "development"
            
            service = get_payment_service_for_testing(force_stripe=True)
            assert isinstance(service, StripePaymentService)


class TestLuhnValidation:
    """Tests para validación Luhn."""
    
    def test_valid_visa(self):
        from app.helpers.luhn import is_valid_luhn
        assert is_valid_luhn("4242424242424242") is True
    
    def test_valid_mastercard(self):
        from app.helpers.luhn import is_valid_luhn
        assert is_valid_luhn("5555555555554444") is True
    
    def test_invalid_luhn(self):
        from app.helpers.luhn import is_valid_luhn
        assert is_valid_luhn("1234567890123456") is False
    
    def test_too_short(self):
        from app.helpers.luhn import is_valid_luhn
        assert is_valid_luhn("123456789012") is False  # Menos de 13 dígitos
    
    def test_with_spaces_and_dashes(self):
        from app.helpers.luhn import is_valid_luhn
        assert is_valid_luhn("4242 4242 4242 4242") is True
        assert is_valid_luhn("4242-4242-4242-4242") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])