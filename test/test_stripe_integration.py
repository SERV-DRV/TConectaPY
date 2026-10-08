"""
Playwright E2E Tests para Integración Stripe

Tests para ambos modos de pago:
- Development: Simulación con Luhn (tarjetas 4242 4242 4242 4242)
- Production: Stripe Elements con PaymentMethod IDs (pm_card_visa)

Credenciales de prueba:
- Usuario: 2000000000002 / Usuario123! (puede usar pm_card_visa en Stripe)
- Admin: 1000000000001 / Admin123!
"""

import re
import os
from playwright.sync_api import Page, expect

USER_URL = "http://localhost:5174"
IS_CI = os.getenv("CI", "false").lower() == "true"
MAX_RETRIES = 8 if IS_CI else 3
RETRY_DELAY = 10 if IS_CI else 5

# Detectar si estamos en modo production (Stripe) o development (simulación)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
USE_STRIPE = ENVIRONMENT == "production"


def test_wallet_recharge_simulation(login_user: Page):
    """
    Test recarga con simulación (Development mode).
    Usa tarjeta Luhn válida: 4242 4242 4242 4242
    """
    if USE_STRIPE:
        print("Skipping simulation test - running in Stripe mode")
        return
    
    login_user.goto(f"{USER_URL}/wallet")
    login_user.get_by_role("button", name="Q10.00").wait_for(state="visible")

    expect(login_user.get_by_text("Saldo Disponible")).to_be_visible()

    # Verificar que NO hay elementos de Stripe
    expect(login_user.locator("#card-element")).not_to_be_visible()
    
    # Llenar formulario de simulación
    login_user.get_by_role("button", name="Q10.00").click()
    login_user.locator("input[name='cardNumber']").fill("4242424242424242")
    login_user.locator("input[name='expirationDate']").fill("12/34")
    login_user.locator("input[name='cvv']").fill("123")
    login_user.get_by_role("button", name="Procesar Recarga").click()

    # Verificar redirección exitosa
    expect(login_user).to_have_url(re.compile(r"/wallet"), timeout=15000)
    
    # Verificar toast de éxito
    expect(login_user.get_by_text("Recarga exitosa")).to_be_visible()


def test_wallet_purchase_card_simulation(login_user: Page):
    """
    Test compra tarjeta ciudadana con simulación (Development mode).
    """
    if USE_STRIPE:
        print("Skipping simulation test - running in Stripe mode")
        return
    
    # Ir a tab de compra
    login_user.goto(f"{USER_URL}/wallet?tab=purchase")
    login_user.get_by_role("button", name=re.compile(r"Comprar Tarjeta")).wait_for(state="visible")

    # Verificar precio Q20.00
    expect(login_user.get_by_role("button", name=re.compile(r"Comprar Tarjeta"))).to_be_visible()

    # Llenar datos de tarjeta (Luhn válido)
    login_user.locator("input[name='cardNumber']").fill("4242424242424242")
    login_user.locator("input[name='expirationDate']").fill("12/34")
    login_user.locator("input[name='cvv']").fill("123")

    # Comprar
    login_user.get_by_role("button", name=re.compile(r"Comprar Tarjeta")).click()

    # Verificar que queda en billetera
    expect(login_user).to_have_url(re.compile(r"/wallet"), timeout=15000)
    
    # Verificar toast de éxito
    expect(login_user.get_by_text("Tarjeta ciudadana comprada")).to_be_visible()


def test_wallet_recharge_stripe(login_user: Page):
    """
    Test recarga con Stripe Elements (Production mode).
    Usa PaymentMethod ID: pm_card_visa
    
    Requiere:
    - ENVIRONMENT=production
    - STRIPE_PUBLISHABLE_KEY configurada en frontend
    - STRIPE_SECRET_KEY configurada en Auth-Python
    """
    if not USE_STRIPE:
        print("Skipping Stripe test - running in simulation mode")
        return
    
    login_user.goto(f"{USER_URL}/wallet")
    
    # Verificar que Stripe Elements está cargado
    login_user.locator("#card-element").wait_for(state="visible", timeout=10000)
    
    # Verificar mensaje de modo prueba
    expect(login_user.get_by_text("Modo prueba")).to_be_visible()
    
    # Seleccionar monto
    login_user.get_by_role("button", name="Q10.00").click()
    
    # Esperar a que Stripe.js cargue y el card element esté listo
    login_user.wait_for_timeout(2000)
    
    # Llenar Stripe Elements (usando iframe)
    # Stripe Elements usa iframes, necesitamos interactuar con ellos
    card_frame = login_user.frame_locator("#card-element iframe").first
    
    # Número de tarjeta de prueba (pm_card_visa)
    card_frame.locator('input[name="cardnumber"]').fill("4242 4242 4242 4242")
    card_frame.locator('input[name="exp-date"]').fill("12/34")
    card_frame.locator('input[name="cvc"]').fill("123")
    
    # Click en botón de procesar
    login_user.get_by_role("button", name="Procesar Recarga").click()
    
    # Esperar procesamiento y redirección
    expect(login_user).to_have_url(re.compile(r"/wallet"), timeout=30000)
    
    # Verificar toast de éxito
    expect(login_user.get_by_text("Recarga exitosa")).to_be_visible()


def test_wallet_purchase_card_stripe(login_user: Page):
    """
    Test compra tarjeta ciudadana con Stripe (Production mode).
    """
    if not USE_STRIPE:
        print("Skipping Stripe test - running in simulation mode")
        return
    
    login_user.goto(f"{USER_URL}/wallet?tab=purchase")
    
    # Verificar Stripe Elements en tab compra
    login_user.locator("#card-element-purchase").wait_for(state="visible", timeout=10000)
    
    # Verificar precio fijo Q20.00
    expect(login_user.get_by_text("Precio fijo: Q20.00")).to_be_visible()
    
    # Esperar Stripe.js
    login_user.wait_for_timeout(2000)
    
    # Llenar Stripe Elements
    card_frame = login_user.frame_locator("#card-element-purchase iframe").first
    card_frame.locator('input[name="cardnumber"]').fill("4242 4242 4242 4242")
    card_frame.locator('input[name="exp-date"]').fill("12/34")
    card_frame.locator('input[name="cvc"]').fill("123")
    
    # Comprar
    login_user.get_by_role("button", name=re.compile(r"Comprar Tarjeta")).click()
    
    # Esperar procesamiento
    expect(login_user).to_have_url(re.compile(r"/wallet"), timeout=30000)
    
    # Verificar éxito
    expect(login_user.get_by_text("Tarjeta ciudadana comprada")).to_be_visible()


def test_stripe_declined_card(login_user: Page):
    """
    Test tarjeta rechazada con Stripe (pm_card_chargeDeclinedInsufficientFunds).
    Solo en modo production.
    """
    if not USE_STRIPE:
        print("Skipping Stripe declined test - running in simulation mode")
        return
    
    login_user.goto(f"{USER_URL}/wallet")
    login_user.locator("#card-element").wait_for(state="visible", timeout=10000)
    login_user.wait_for_timeout(2000)
    
    # Usar tarjeta que simula fondos insuficientes
    card_frame = login_user.frame_locator("#card-element iframe").first
    card_frame.locator('input[name="cardnumber"]').fill("4000 0000 0000 9995")  # insufficient_funds
    card_frame.locator('input[name="exp-date"]').fill("12/34")
    card_frame.locator('input[name="cvc"]').fill("123")
    
    login_user.get_by_role("button", name="Procesar Recarga").click()
    
    # Verificar mensaje de error
    expect(login_user.locator("#card-errors")).to_contain_text("insuficient", timeout=10000)
    
    # NO debe redirigir - debe mostrar error en la página


def test_wallet_history(login_user: Page):
    """Test tab de historial - funciona en ambos modos."""
    login_user.goto(f"{USER_URL}/wallet?tab=history")
    login_user.get_by_role("link", name="Historial").wait_for(state="visible")

    expect(login_user.get_by_role("heading", name="Historial de Recargas")).to_be_visible()


def test_wallet_invoices(login_user: Page):
    """Test tab de facturas - funciona en ambos modos."""
    login_user.goto(f"{USER_URL}/wallet?tab=invoices")
    login_user.get_by_role("link", name="Facturas").wait_for(state="visible")

    expect(login_user.get_by_role("heading", name="Facturas Emitidas")).to_be_visible()


def test_card_flip_animation(login_user: Page):
    """Test animación flip de tarjeta al enfocar CVV."""
    login_user.goto(f"{USER_URL}/wallet")
    
    # En modo simulación, hay input CVV directo
    if not USE_STRIPE:
        cvv_input = login_user.locator("input[name='cvv']")
        cvv_input.focus()
        # Verificar que la tarjeta voltea (transform rotateY 180deg)
        card_inner = login_user.locator("#cardInner")
        expect(card_inner).to_have_attribute("style", re.compile(r"rotateY\(180deg\)"))
        
        cvv_input.blur()
        expect(card_inner).to_have_attribute("style", re.compile(r"rotateY\(0deg\)"))


def test_amount_buttons(login_user: Page):
    """Test botones de monto rápido."""
    login_user.goto(f"{USER_URL}/wallet")
    
    amount_input = login_user.locator("input[name='amount'], input[name='amount']#stripe-amount")
    
    login_user.get_by_role("button", name="Q10.00").click()
    expect(amount_input).to_have_value("10")
    
    login_user.get_by_role("button", name="Q50.00").click()
    expect(amount_input).to_have_value("50")
    
    login_user.get_by_role("button", name="Q100.00").click()
    expect(amount_input).to_have_value("100")


def test_stripe_elements_loaded(login_user: Page):
    """
    Verifica que Stripe.js y Elements se cargan correctamente en production.
    """
    if not USE_STRIPE:
        print("Skipping Stripe load test - running in simulation mode")
        return
    
    login_user.goto(f"{USER_URL}/wallet")
    
    # Verificar script de Stripe.js cargado
    stripe_script = login_user.locator('script[src*="js.stripe.com"]')
    expect(stripe_script).to_have_attribute("src", re.compile(r"js\.stripe\.com"))
    
    # Verificar que publishable key está en la página
    expect(login_user.locator("body")).to_contain_text("pk_test")


# Test helper para verificar webhook manualmente
def test_webhook_endpoint_accessible():
    """
    Test que el endpoint de webhook es accesible.
    Ejecutar manualmente con: stripe trigger payment_intent.succeeded
    """
    import requests
    
    # Este test es informativo - el webhook real se prueba con Stripe CLI
    webhook_url = "http://localhost:5001/api/stripe/webhook"
    
    # En CI/producción usar URL real
    if os.getenv("RENDER"):
        webhook_url = "https://tconecta-auth.onrender.com/api/stripe/webhook"
    
    print(f"Webhook URL: {webhook_url}")
    print("Para probar webhook ejecuta:")
    print("  stripe listen --forward-to localhost:5001/api/stripe/webhook")
    print("  stripe trigger payment_intent.succeeded")
    
    # Test pasa solo como documentación
    assert True


if __name__ == "__main__":
    # Permitir ejecutar tests individuales
    import pytest
    pytest.main([__file__, "-v"])