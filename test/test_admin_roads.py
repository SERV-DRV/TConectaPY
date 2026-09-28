import re
from playwright.sync_api import Page, expect

ADMIN_URL = "http://localhost:5173"

def test_road_change_status(login_admin: Page):
    login_admin.goto(f"{ADMIN_URL}/roads")
    login_admin.locator("select[name='status']").first.wait_for(state="visible")

    # Cambiar estado del primer road a INACTIVE
    login_admin.locator("select[name='status']").first.select_option("INACTIVE")

    # Verificar que la página recargó
    login_admin.locator("select[name='status']").first.wait_for(state="visible")

def test_road_edit_modal(login_admin: Page):
    login_admin.goto(f"{ADMIN_URL}/roads")
    login_admin.get_by_role("button", name="Editar").first.wait_for(state="visible")

    # Abrir modal de edición
    login_admin.get_by_role("button", name="Editar").first.click()

    # Verificar que el modal de edición está visible
    expect(login_admin.get_by_role("button", name="Guardar Cambios")).to_be_visible(timeout=5000)

    # Cerrar modal
    login_admin.keyboard.press("Escape")

def test_road_create_modal_opens(login_admin: Page):
    login_admin.goto(f"{ADMIN_URL}/roads")
    login_admin.get_by_role("button", name="+ Nueva Ruta").wait_for(state="visible")

    # Abrir modal de creación
    login_admin.get_by_role("button", name="+ Nueva Ruta").click()

    # Verificar que los campos del formulario están visibles
    expect(login_admin.get_by_placeholder("Nombre de la ruta")).to_be_visible()
    expect(login_admin.get_by_placeholder("Codigo (ej: L1)")).to_be_visible()

    # Verificar que el mapa está presente
    expect(login_admin.locator("#map")).to_be_visible()

    # Cerrar modal
    login_admin.keyboard.press("Escape")
