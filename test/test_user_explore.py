from playwright.sync_api import Page, expect

USER_URL = "http://localhost:5174"

def test_user_explore_roads(login_user: Page):
    # 1. Ir a explorar
    login_user.goto(f"{USER_URL}/explore")

    # 2. Verificar tab de rutas y heading
    expect(login_user.get_by_role("heading", name="Explorar Red")).to_be_visible()
    expect(login_user.get_by_role("link", name="Rutas")).to_be_visible()

    # 3. Verificar que hay tarjetas de rutas ( hay headings h3 con nombres de ruta)
    expect(login_user.locator("h3").first).to_be_visible()

def test_user_explore_stations(login_user: Page):
    # 1. Ir a explorar estaciones
    login_user.goto(f"{USER_URL}/explore?tab=stations")

    # 2. Verificar tab de estaciones
    expect(login_user.get_by_role("heading", name="Explorar Red")).to_be_visible()
    expect(login_user.get_by_role("link", name="Estaciones")).to_be_visible()

    # 3. Verificar que hay tarjetas de estaciones
    expect(login_user.locator("h3").first).to_be_visible()
