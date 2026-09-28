import re
from playwright.sync_api import Page, expect

ADMIN_URL = "http://localhost:5173"

def test_station_change_status(login_admin: Page):
    login_admin.goto(f"{ADMIN_URL}/stations")
    login_admin.locator("select[name='status']").first.wait_for(state="visible")

    # Cambiar estado del primer station a INACTIVE
    login_admin.locator("select[name='status']").first.select_option("INACTIVE")

    # Verificar que la página recargó
    login_admin.locator("select[name='status']").first.wait_for(state="visible")

def test_station_edit_modal(login_admin: Page):
    login_admin.goto(f"{ADMIN_URL}/stations")
    login_admin.get_by_role("button", name="Editar").first.wait_for(state="visible")

    # Abrir modal de edición
    login_admin.get_by_role("button", name="Editar").first.click()

    # Verificar que el modal de edición está visible
    expect(login_admin.get_by_role("button", name="Guardar Cambios")).to_be_visible(timeout=5000)

    # Cerrar modal
    login_admin.keyboard.press("Escape")

def test_station_create_modal_opens(login_admin: Page):
    login_admin.goto(f"{ADMIN_URL}/stations")
    login_admin.get_by_role("button", name="+ Nueva Estacion").wait_for(state="visible")

    # Abrir modal de creación
    login_admin.get_by_role("button", name="+ Nueva Estacion").click()

    # Verificar que los campos del formulario están visibles
    expect(login_admin.get_by_placeholder("Nombre")).to_be_visible()
    expect(login_admin.get_by_placeholder("Buscar lugar (ej: Irtra Petapa)")).to_be_visible()

    # Verificar que el mapa está presente
    expect(login_admin.locator("#map")).to_be_visible()

    # Cerrar modal
    login_admin.keyboard.press("Escape")
