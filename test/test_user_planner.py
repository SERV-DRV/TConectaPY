import re
from playwright.sync_api import Page, expect

USER_URL = "http://localhost:5174"

def test_planner_loads(login_user: Page):
    login_user.goto(f"{USER_URL}/planner")

    # Verificar que el mapa está presente
    expect(login_user.locator("#map")).to_be_visible()

    # Verificar inputs de origen y destino
    expect(login_user.locator("#originQuery")).to_be_visible()
    expect(login_user.locator("#destQuery")).to_be_visible()

    # Verificar botón de calcular ruta
    expect(login_user.get_by_role("button", name="Armar mi Ruta")).to_be_visible()

def test_planner_set_origin_destination(login_user: Page):
    login_user.goto(f"{USER_URL}/planner")
    login_user.locator("#originQuery").wait_for(state="visible")

    # Escribir origen
    login_user.locator("#originQuery").fill("Terminal Central")

    # Escribir destino
    login_user.locator("#destQuery").fill("Plaza Italia")

    # Verificar que los campos tienen valor
    expect(login_user.locator("#originQuery")).to_have_value("Terminal Central")
    expect(login_user.locator("#destQuery")).to_have_value("Plaza Italia")

def test_planner_history_visible(login_user: Page):
    login_user.goto(f"{USER_URL}/planner")
    login_user.get_by_role("heading", name="Historial de Viajes").wait_for(state="visible")

    # Verificar que el panel de historial está visible
    expect(login_user.get_by_role("heading", name="Historial de Viajes")).to_be_visible()
