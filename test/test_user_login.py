import re
from playwright.sync_api import Page, expect

def test_user_login(page: Page):
    page.goto("http://localhost:5174/auth/login")

    page.get_by_placeholder("CUI (13 digitos)").fill("2000000000002")
    page.get_by_placeholder("Contrasena").fill("Usuario123!")
    page.get_by_role("button", name="Iniciar sesion").click()

    expect(page).to_have_url(re.compile(r"/planner$"))
    expect(page.get_by_role("heading", name="Buscador de Rutas Interactivo")).to_be_visible()
