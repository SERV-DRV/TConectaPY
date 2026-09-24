import re
from playwright.sync_api import Page, expect

USER_URL = "http://localhost:5174"

def test_user_profile_view(login_user: Page):
    login_user.goto(f"{USER_URL}/profile")
    expect(login_user.get_by_role("heading", name="Mi Perfil Ciudadano")).to_be_visible()
    expect(login_user.get_by_role("button", name="Resumen de Actividad")).to_be_visible()
    expect(login_user.get_by_role("button", name="Datos del Usuario")).to_be_visible()

def test_user_profile_edit_email(login_user: Page):
    login_user.goto(f"{USER_URL}/profile")

    # Click en tab datos del usuario
    login_user.get_by_role("button", name="Datos del Usuario").click()

    # Verificar email visible
    expect(login_user.get_by_text("usuario@correo.com")).to_be_visible()

def test_user_profile_switch_tabs(login_user: Page):
    login_user.goto(f"{USER_URL}/profile")

    # Verificar tab resumen por defecto
    expect(login_user.get_by_text("Total Gastado")).to_be_visible()

    # Cambiar a tab datos
    login_user.get_by_role("button", name="Datos del Usuario").click()
    expect(login_user.get_by_text("CUI / DPI")).to_be_visible()

    # Volver a tab resumen
    login_user.get_by_role("button", name="Resumen de Actividad").click()
    expect(login_user.get_by_text("Total Gastado")).to_be_visible()
