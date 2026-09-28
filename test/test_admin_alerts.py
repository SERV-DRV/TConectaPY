import pytest
from playwright.sync_api import Page, expect
import re

@pytest.mark.integration
def test_alert_create_and_resolve(login_admin):
    ADMIN_URL = "http://localhost:5173"
    login_admin.goto(f"{ADMIN_URL}/alerts")
    login_admin.get_by_role("button", name="+ Nueva Alerta").wait_for(state="visible")
    login_admin.get_by_role("button", name="+ Nueva Alerta").click()
    login_admin.get_by_placeholder("Titulo").fill("Test Alert Playwright")
    login_admin.locator("select[name='typeAlert']").select_option("INCIDENT")
    login_admin.get_by_placeholder("Descripcion").fill("Alerta de prueba automatizada")
    login_admin.get_by_role("button", name="Crear Alerta").click()
    expect(login_admin.get_by_text("Test Alert Playwright")).to_be_visible(timeout=10000)
    login_admin.get_by_text("Test Alert Playwright").locator("..").get_by_role("button", name="Marcar Resuelta").click()
    login_admin.get_by_role("button", name="Confirmar").click()
    expect(login_admin.get_by_text("Test Alert Playwright")).not_to_be_visible(timeout=10000)
