import re
from playwright.sync_api import Page, expect

ADMIN_URL = "http://localhost:5173"

def test_bus_create(login_admin: Page):
    login_admin.goto(f"{ADMIN_URL}/buses")
    login_admin.get_by_role("button", name="+ Nuevo Bus").wait_for(state="visible")

    login_admin.get_by_role("button", name="+ Nuevo Bus").click()
    login_admin.get_by_placeholder("Numero de bus").fill("9999")
    login_admin.get_by_placeholder("Placa (ej: U1234ABC)").fill("U999XYZ")
    login_admin.get_by_role("spinbutton").fill("60")
    login_admin.get_by_role("button", name="Crear Bus").click()

    expect(login_admin.get_by_role("heading", name="Nuevo Bus")).not_to_be_visible(timeout=10000)
    expect(login_admin.locator("td", has_text="9999").first).to_be_visible()
    expect(login_admin.locator("td", has_text="U999XYZ").first).to_be_visible()

def test_bus_change_status(login_admin: Page):
    login_admin.goto(f"{ADMIN_URL}/buses")
    login_admin.locator("select[name='status']").first.wait_for(state="visible")

    # Cambiar estado del primer bus a Inactivo
    login_admin.locator("select[name='status']").first.select_option("INACTIVE")

    # Verificar que la página recargó (el select vuelve a estar visible)
    login_admin.locator("select[name='status']").first.wait_for(state="visible")

def test_bus_edit(login_admin: Page):
    login_admin.goto(f"{ADMIN_URL}/buses")
    login_admin.get_by_role("button", name="Editar").first.wait_for(state="visible")

    # Abrir modal de edición
    login_admin.get_by_role("button", name="Editar").first.click()
    login_admin.locator("#edit-busNumber-input").wait_for(state="visible")

    # Verificar que los campos están prellenados
    expect(login_admin.locator("#edit-busNumber-input")).not_to_have_value("")

    # Cerrar modal sin guardar
    login_admin.keyboard.press("Escape")
