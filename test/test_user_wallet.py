import re
from playwright.sync_api import Page, expect

USER_URL = "http://localhost:5174"

def test_wallet_recharge(login_user: Page):
    login_user.goto(f"{USER_URL}/wallet")
    login_user.get_by_role("button", name="Q10.00").wait_for(state="visible")

    expect(login_user.get_by_text("Saldo Disponible")).to_be_visible()

    login_user.get_by_role("button", name="Q10.00").click()
    login_user.locator("input[name='cardNumber']").fill("4532015112830366")
    login_user.locator("input[name='expirationDate']").fill("12/28")
    login_user.locator("input[name='cvv']").fill("123")
    login_user.get_by_role("button", name="Procesar Recarga").click()

    expect(login_user).to_have_url(re.compile(r"/wallet"), timeout=10000)

def test_wallet_purchase_card(login_user: Page):
    # 1. Ir a tab de compra de tarjeta
    login_user.goto(f"{USER_URL}/wallet?tab=purchase")
    login_user.get_by_role("button", name=re.compile(r"Comprar Tarjeta")).wait_for(state="visible")

    # 2. Verificar precio Q20.00
    expect(login_user.get_by_role("button", name=re.compile(r"Comprar Tarjeta"))).to_be_visible()

    # 3. Llenar datos de tarjeta
    login_user.locator("input[name='cardNumber']").fill("4532015112830366")
    login_user.locator("input[name='expirationDate']").fill("12/28")
    login_user.locator("input[name='cvv']").fill("123")

    # 4. Comprar
    login_user.get_by_role("button", name=re.compile(r"Comprar Tarjeta")).click()

    # 5. Verificar que queda en billetera
    expect(login_user).to_have_url(re.compile(r"/wallet"), timeout=10000)

def test_wallet_history(login_user: Page):
    # 1. Ir a tab de historial
    login_user.goto(f"{USER_URL}/wallet?tab=history")
    login_user.get_by_role("link", name="Historial").wait_for(state="visible")

    # 2. Verificar que el tab historial está activo
    expect(login_user.get_by_role("heading", name="Historial de Recargas")).to_be_visible()
