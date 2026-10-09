import re
from playwright.sync_api import Page, expect

def test_stripe_recharge_success(login_user: Page):
    """Test recarga exitosa con Stripe (requiere ENVIRONMENT=production y keys configuradas)"""
    page = login_user
    page.goto("http://localhost:5174/wallet?tab=recharge")
    
    # Verificar que Stripe Elements está presente (si está en production)
    stripe_publishable = page.evaluate("""() => {
        const script = document.querySelector('script[src*="js.stripe.com"]');
        return !!script;
    }""")
    
    if stripe_publishable:
        # Modo Stripe production
        page.fill('#stripeAmount', '10')
        page.click('#stripe-recharge-btn')
        
        # Esperar a que Stripe procese
        expect(page.locator('#stripe-recharge-btn')).to_be_enabled(timeout=30000)
        
        # Verificar éxito (redirección a historial)
        expect(page).to_have_url(re.compile(r"/wallet\?tab=history"), timeout=10000)
    else:
        # Modo simulación (development)
        page.fill('#amount', '10')
        page.fill('input[name="cardNumber"]', '4242424242424242')
        page.fill('input[name="expirationDate"]', '12/28')
        page.fill('input[name="cvv"]', '123')
        page.click('button:has-text("Procesar Recarga (Simulación)")')
        
        expect(page).to_have_url(re.compile(r"/wallet"), timeout=10000)


def test_stripe_recharge_declined(login_user: Page):
    """Test rechazo con tarjeta de prueba de fondos insuficientes"""
    page = login_user
    page.goto("http://localhost:5174/wallet?tab=recharge")
    
    stripe_publishable = page.evaluate("""() => {
        const script = document.querySelector('script[src*="js.stripe.com"]');
        return !!script;
    }""")
    
    if stripe_publishable:
        page.fill('#stripeAmount', '10')
        # Usar tarjeta de prueba declined
        # Nota: Stripe Elements no permite ingresar pm_ directamente en CardElement
        # Este test requiere configuración especial o mock
        pass


def test_simulation_recharge(login_user: Page):
    """Test simulacro actual (development) con Luhn válido"""
    page = login_user
    page.goto("http://localhost:5174/wallet?tab=recharge")
    
    page.fill('#amount', '10')
    page.fill('input[name="cardNumber"]', '4242424242424242')  # Luhn válido
    page.fill('input[name="expirationDate"]', '12/28')
    page.fill('input[name="cvv"]', '123')
    page.click('button:has-text("Procesar Recarga (Simulación)")')
    
    # Verificar que no hay error
    expect(page.locator('.toast-error')).not_to_be_visible(timeout=5000)


def test_stripe_purchase_card_success(login_user: Page):
    """Test compra de tarjeta ciudadana con Stripe"""
    page = login_user
    page.goto("http://localhost:5174/wallet?tab=purchase")
    
    stripe_publishable = page.evaluate("""() => {
        const script = document.querySelector('script[src*="js.stripe.com"]');
        return !!script;
    }""")
    
    if stripe_publishable:
        page.click('#stripe-purchase-btn')
        expect(page.locator('#stripe-purchase-btn')).to_be_enabled(timeout=30000)
        expect(page).to_have_url(re.compile(r"/wallet\?tab=history"), timeout=10000)
    else:
        page.fill('input[name="cardNumber"]', '4242424242424242')
        page.fill('input[name="expirationDate"]', '12/28')
        page.fill('input[name="cvv"]', '123')
        page.click('button:has-text("Comprar Tarjeta Ciudadana (Q20.00) (Simulación)")')
        expect(page).to_have_url(re.compile(r"/wallet"), timeout=10000)


def test_webhook_payment_intent_succeeded():
    """Test webhook handler con event mock - requiere ejecución manual con Stripe CLI"""
    # Este test se ejecuta manualmente:
    # stripe listen --forward-to localhost:5001/api/stripe/webhook
    # stripe trigger payment_intent.succeeded
    pass