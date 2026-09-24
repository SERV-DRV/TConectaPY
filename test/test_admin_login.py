import re
from playwright.sync_api import Page, expect

def test_admin_login(page: Page):
    page.goto("http://localhost:5173/auth/login")

    page.get_by_placeholder("Ej: 0000000000000").fill("1000000000001")
    page.locator("input[name='password']").fill("Admin123!")
    page.get_by_role("button", name="Iniciar sesion").click()

    expect(page).to_have_url(re.compile(r"/dashboard$"))
    expect(page.get_by_role("heading", name="Dashboard")).to_be_visible()
