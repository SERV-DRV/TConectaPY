from playwright.sync_api import Page, expect

USER_URL = "http://localhost:5174"

def test_user_see_alerts(login_user: Page):
    # 1. Ir a alertas
    login_user.goto(f"{USER_URL}/alerts")

    # 2. Verificar que la página carga (con o sin alertas)
    expect(login_user.get_by_role("heading", name="Alertas")).to_be_visible()
