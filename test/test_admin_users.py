import re
from playwright.sync_api import Page, expect

ADMIN_URL = "http://localhost:5173"

def test_admin_create_user(login_admin: Page):
    # 1. Ir a usuarios
    login_admin.goto(f"{ADMIN_URL}/users")
    login_admin.get_by_role("button", name="+ Nuevo Admin").wait_for(state="visible")

    # 2. Abrir modal
    login_admin.get_by_role("button", name="+ Nuevo Admin").click()

    # 3. Llenar formulario con CUI único
    test_cui = "3000000000003"
    login_admin.locator("input[name='cui']").fill(test_cui)
    login_admin.locator("input[name='email']").fill("testadmin@playwright.com")

    # 4. El password viene hardcodeado, solo verificar que está visible
    expect(login_admin.locator("input[name='password']")).to_have_value("Transmetro2024!")

    # 5. Crear admin
    login_admin.get_by_role("button", name="Crear Admin").click()

    # 6. Verificar que el CUI aparece en la tabla
    expect(login_admin.locator("td", has_text=test_cui).first).to_be_visible(timeout=10000)
