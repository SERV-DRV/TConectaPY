from playwright.sync_api import Page, expect

ADMIN_URL = "http://localhost:5173"

def test_alert_create_and_resolve(login_admin: Page):
    # 1. Ir a alertas
    login_admin.goto(f"{ADMIN_URL}/alerts")
    login_admin.get_by_role("button", name="+ Nueva Alerta").wait_for(state="visible")

    # 2. Abrir modal y crear alerta
    login_admin.get_by_role("button", name="+ Nueva Alerta").click()
    login_admin.get_by_placeholder("Titulo").fill("Test Alert Playwright")
    login_admin.locator("select[name='typeAlert']").select_option("INCIDENT")
    login_admin.get_by_placeholder("Descripcion").fill("Alerta de prueba automatizada")
    login_admin.get_by_role("button", name="Crear Alerta").click()

    # 3. Verificar que la alerta aparece
    expect(login_admin.get_by_text("Test Alert Playwright")).to_be_visible(timeout=10000)

    # 4. Marcar como resuelta
    login_admin.get_by_text("Test Alert Playwright").locator("..").get_by_role("button", name="Marcar Resuelta").click()
    login_admin.get_by_role("button", name="Confirmar").click()

    # 5. Verificar que desaparece de activas
    expect(login_admin.get_by_text("Test Alert Playwright")).not_to_be_visible(timeout=10000)
