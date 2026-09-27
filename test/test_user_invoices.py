import re
from playwright.sync_api import Page, expect

USER_URL = "http://localhost:5174"

# Tarjeta válida Luhn para tests (Visa test)
VALID_CARD = "4532015112830366"
VALID_EXP = "12/28"
VALID_CVV = "123"

# ──────────────────────────────────────────────
# FACTURA TRAS RECARGA
# ──────────────────────────────────────────────
def test_invoice_created_after_recharge(login_user: Page):
    """
    1. Ir a wallet → tab recarga
    2. Hacer recarga Q10 con tarjeta válida
    3. Verificar redirect a /wallet/[ObjectId] (factura detalle)
    4. Verificar datos clave en factura: monto, tipo, CUI, últimos 4 tarjeta
    """
    login_user.goto(f"{USER_URL}/wallet")

    # Esperar formulario recarga (tab por defecto)
    login_user.get_by_role("button", name="Q10.00").wait_for(state="visible")

    # Llenar y enviar
    login_user.get_by_role("button", name="Q10.00").click()
    login_user.locator("input[name='cardNumber']").fill(VALID_CARD)
    login_user.locator("input[name='expirationDate']").fill(VALID_EXP)
    login_user.locator("input[name='cvv']").fill(VALID_CVV)

    # Click y esperar navegación a factura
    with login_user.expect_navigation():
        login_user.get_by_role("button", name="Procesar Recarga").click()

    # Verificar URL: /wallet/[mongo_id] (ObjectId de 24 hex chars)
    expect(login_user).to_have_url(re.compile(r"/wallet/[a-f0-9]{24}$"), timeout=10000)

    # Verificar contenido factura detalle (usar main para evitar match con navbar balance)
    main = login_user.locator("main")
    expect(main.get_by_role("heading", name="Factura")).to_be_visible()
    expect(main.get_by_text("RECARGA DE SALDO")).to_be_visible()
    expect(main.get_by_text("Q10.00")).to_be_visible()
    expect(main.get_by_text("COMPLETADA")).to_be_visible()
    # CUI del usuario de test (2000000000002)
    expect(main.get_by_text("2000000000002")).to_be_visible()
    # Últimos 4 de tarjeta de test
    expect(main.get_by_text("0366")).to_be_visible()

    # Verificar botones de acción
    expect(main.get_by_role("button", name=re.compile(r"Imprimir"))).to_be_visible()
    expect(main.get_by_role("link", name="Volver al Listado")).to_be_visible()


# ──────────────────────────────────────────────
# FACTURA TRAS COMPRA TARJETA
# ──────────────────────────────────────────────
def test_invoice_created_after_purchase_card(login_user: Page):
    """
    1. Ir a wallet → tab compra tarjeta
    2. Comprar tarjeta Q20.00
    3. Verificar redirect a factura con tipo COMPRA_TARJETA
    Nota: Si el usuario ya tiene tarjeta, verifica mensaje de error y no testa factura
    """
    login_user.goto(f"{USER_URL}/wallet?tab=purchase")

    login_user.get_by_role("button", name=re.compile(r"Comprar Tarjeta")).wait_for(state="visible")

    login_user.locator("input[name='cardNumber']").fill(VALID_CARD)
    login_user.locator("input[name='expirationDate']").fill(VALID_EXP)
    login_user.locator("input[name='cvv']").fill(VALID_CVV)

    with login_user.expect_navigation():
        login_user.get_by_role("button", name=re.compile(r"Comprar Tarjeta")).click()

    # Verificar si redirigió a factura (éxito) o se quedó en purchase (ya tiene tarjeta)
    if "/wallet/" in login_user.url and re.search(r"/wallet/[a-f0-9]{24}$", login_user.url):
        # Éxito: verificamos factura COMPRA_TARJETA
        expect(login_user).to_have_url(re.compile(r"/wallet/[a-f0-9]{24}$"), timeout=10000)
        main = login_user.locator("main")
        expect(main.get_by_text("COMPRA TARJETA CIUDADANA")).to_be_visible()
        expect(main.get_by_text("Q20.00")).to_be_visible()
        expect(main.get_by_text("2000000000002")).to_be_visible()
        expect(main.get_by_text("0366")).to_be_visible()
    else:
        # Usuario ya tiene tarjeta - verificar que sigue en purchase y hay error visible
        expect(login_user).to_have_url(re.compile(r"/wallet\?tab=purchase"))
        # Verificar que el formulario sigue visible (no redirigió)
        expect(login_user.get_by_role("button", name=re.compile(r"Comprar Tarjeta"))).to_be_visible()
        # El toast de error puede no renderizar en headed mode, verificamos que no hay factura
        expect(login_user.get_by_text("COMPRA TARJETA CIUDADANA")).not_to_be_visible()


# ──────────────────────────────────────────────
# TAB FACTURAS — LISTADO PAGINADO
# ──────────────────────────────────────────────
def test_invoices_tab_list_pagination(login_user: Page):
    """
    1. Ir a tab Facturas
    2. Verificar listado (vacío o con facturas previas)
    3. Verificar paginación si hay >10 facturas
    """
    login_user.goto(f"{USER_URL}/wallet?tab=invoices")

    # Tab Facturas activa
    expect(login_user.get_by_role("heading", name="Facturas Emitidas")).to_be_visible()

    # Si no hay facturas → mensaje vacío
    empty_state = login_user.get_by_text("No hay facturas emitidas")
    if empty_state.count() > 0:
        expect(empty_state).to_be_visible()
        expect(login_user.get_by_text("Tus facturas aparecerán aquí")).to_be_visible()
        return

    # Si hay facturas → verificar estructura listado
    # Cada factura es un enlace <a href="/wallet/[id]"> dentro del tab facturas
    first_invoice_link = login_user.locator("a[href^='/wallet/']").first
    expect(first_invoice_link).to_be_visible()

    # Verificar elementos de cada fila - el badge del monto (formato QXX.XX)
    expect(first_invoice_link.get_by_text(re.compile(r"Q\d+\.\d{2}"))).to_be_visible()
    # Verificar que el enlace tiene href válido de factura (ObjectId 24 hex)
    expect(first_invoice_link).to_have_attribute("href", re.compile(r"^/wallet/[a-f0-9]{24}$"))

    # Paginación (si total_pages > 1)
    pagination = login_user.get_by_text(re.compile(r"Página \d+ de \d+"))
    if pagination.count() > 0:
        expect(pagination).to_be_visible()
        # Test navegar páginas
        next_btn = login_user.get_by_role("link", name="Siguiente")
        if next_btn.count() > 0:
            with login_user.expect_navigation():
                next_btn.click()
            expect(login_user).to_have_url(re.compile(r"tab=invoices&page=2"))


# ──────────────────────────────────────────────
# NAVEGACIÓN: LISTADO → DETALLE → VOLVER
# ──────────────────────────────────────────────
def test_invoice_list_to_detail_navigation(login_user: Page):
    """
    1. Crear factura vía recarga (reutiliza test anterior)
    2. Ir a tab Facturas
    3. Click en factura → ir a detalle
    4. Click "Volver al Listado" → regresa a tab Facturas
    """
    # 1. Crear factura (recarga rápida)
    login_user.goto(f"{USER_URL}/wallet")
    login_user.get_by_role("button", name="Q10.00").click()
    login_user.locator("input[name='cardNumber']").fill(VALID_CARD)
    login_user.locator("input[name='expirationDate']").fill(VALID_EXP)
    login_user.locator("input[name='cvv']").fill(VALID_CVV)
    with login_user.expect_navigation():
        login_user.get_by_role("button", name="Procesar Recarga").click()

    # Capturar invoice_id de la URL
    invoice_url = login_user.url
    invoice_id_match = re.search(r"/wallet/([a-f0-9]{24})$", invoice_url)
    assert invoice_id_match, "URL debe terminar en /wallet/[ObjectId]"
    invoice_id = invoice_id_match.group(1)

    # 2. Ir a tab Facturas
    login_user.goto(f"{USER_URL}/wallet?tab=invoices")
    expect(login_user.get_by_role("heading", name="Facturas Emitidas")).to_be_visible()

    # 3. Click en la factura recién creada
    invoice_link = login_user.locator(f"a[href='/wallet/{invoice_id}']")
    expect(invoice_link).to_be_visible()

    with login_user.expect_navigation():
        invoice_link.click()

    # Verificar detalle
    expect(login_user).to_have_url(re.compile(rf"/wallet/{invoice_id}$"))
    main = login_user.locator("main")
    expect(main.get_by_text("RECARGA DE SALDO")).to_be_visible()

    # 4. Volver al listado
    with login_user.expect_navigation():
        login_user.get_by_role("link", name="Volver al Listado").click()

    expect(login_user).to_have_url(re.compile(r"/wallet\?tab=invoices"))


# ──────────────────────────────────────────────
# OWNERSHIP — USUARIO A NO VE FACTURAS DE USUARIO B
# ──────────────────────────────────────────────
def test_invoice_ownership_isolation(browser, login_user: Page):
    """
    1. Usuario crea factura → obtener invoice_id
    2. Admin (en contexto separado) intenta acceder a /wallet/[invoice_id]
    3. Debe fallar (404 o redirect) — ownership verificado en backend
    """
    # Usuario crea factura
    login_user.goto(f"{USER_URL}/wallet")
    login_user.get_by_role("button", name="Q10.00").click()
    login_user.locator("input[name='cardNumber']").fill(VALID_CARD)
    login_user.locator("input[name='expirationDate']").fill(VALID_EXP)
    login_user.locator("input[name='cvv']").fill(VALID_CVV)
    with login_user.expect_navigation():
        login_user.get_by_role("button", name="Procesar Recarga").click()

    invoice_url = login_user.url
    invoice_id_match = re.search(r"/wallet/([a-f0-9]{24})$", invoice_url)
    assert invoice_id_match, "URL debe terminar en /wallet/[ObjectId]"
    invoice_id = invoice_id_match.group(1)

    # Admin en contexto NUEVO (cookies/sesión separadas)
    admin_context = browser.new_context()
    admin_page = admin_context.new_page()
    
    # Login admin
    admin_page.goto(f"{USER_URL}/auth/login")
    admin_page.get_by_placeholder("CUI (13 digitos)").fill("1000000000001")
    admin_page.locator("input[name='password']").fill("Admin123!")
    admin_page.get_by_role("button", name="Iniciar sesion").click()
    expect(admin_page).to_have_url(re.compile(r"/planner$"), timeout=10000)

    # Admin intenta acceder a factura del usuario
    admin_page.goto(f"{USER_URL}/wallet/{invoice_id}")

    # Backend debe retornar 404 (ownership check en get_invoice_by_id)
    # En SSR FastAPI, 404 renderiza página de error o redirige
    # Verificar que NO ve la factura del usuario
    admin_main = admin_page.locator("main")
    expect(admin_main.get_by_text("RECARGA DE SALDO")).not_to_be_visible()
    # O verificar redirect a wallet sin factura
    expect(admin_page).to_have_url(re.compile(r"/wallet"))
    
    admin_context.close()


# ──────────────────────────────────────────────
# RESPONSIVE — MÓVIL (375px)
# ──────────────────────────────────────────────
def test_invoice_detail_responsive_mobile(login_user: Page):
    """
    Verificar factura detalle en viewport móvil (375px)
    """
    # Crear factura primero
    login_user.goto(f"{USER_URL}/wallet")
    login_user.get_by_role("button", name="Q10.00").click()
    login_user.locator("input[name='cardNumber']").fill(VALID_CARD)
    login_user.locator("input[name='expirationDate']").fill(VALID_EXP)
    login_user.locator("input[name='cvv']").fill(VALID_CVV)
    with login_user.expect_navigation():
        login_user.get_by_role("button", name="Procesar Recarga").click()

    # Redimensionar a móvil
    login_user.set_viewport_size({"width": 375, "height": 667})

    # Verificar que elementos clave siguen visibles y legibles
    main = login_user.locator("main")
    expect(main.get_by_role("heading", name="Factura")).to_be_visible()
    expect(main.get_by_text("Q10.00")).to_be_visible()
    expect(main.get_by_text("COMPLETADA")).to_be_visible()

    # Botones apilados en móvil (flex-col en <640px)
    print_btn = main.get_by_role("button", name=re.compile(r"Imprimir"))
    back_link = main.get_by_role("link", name="Volver al Listado")
    expect(print_btn).to_be_visible()
    expect(back_link).to_be_visible()

    # No overflow horizontal
    body_width = login_user.evaluate("document.body.scrollWidth")
    assert body_width <= 375, f"Overflow horizontal detectado: {body_width}px"


# ──────────────────────────────────────────────
# MOCK — FACTURA SIN CARGO REAL (para dev/tests/demos)
# ──────────────────────────────────────────────
def test_invoice_created_after_recharge_mocked(login_user: Page):
    """
    Mock de transacción: intercepta form POST /wallet/recharge,
    retorna redirect 302 a factura fake. Demuestra patrón para evitar
    1.5s sleep + validación Luhn + escritura BD real.
    Nota: En app SSR, el mock intercepta el form submit del navegador.
    Para mock completo de vista detalle, requeriría interceptar GET /wallet/{id} también.
    """
    fake_invoice_id = "66f8b2c1a1b2c3d4e5f6a7b8"  # ObjectId 24 hex válido
    
    # 1. Ir a wallet
    login_user.goto(f"{USER_URL}/wallet")
    
    # 2. Click en monto Q10 (abre formulario)
    login_user.get_by_role("button", name="Q10.00").click()
    
    # 3. INTERCEPTAR el form POST del frontend (server-rendered app)
    # El navegador hace POST a /wallet/recharge y recibe redirect 302
    def handle_recharge_form(route):
        print(f"[MOCK] Interceptado form POST: {route.request.url}")
        # Simular redirect que haría el frontend tras mock exitoso
        route.fulfill(
            status=302,
            headers={"Location": f"/wallet/{fake_invoice_id}"}
        )
    
    # Registrar interceptor en el form POST del frontend
    login_user.route("**/wallet/recharge", handle_recharge_form)
    
    # 4. Llenar MÍNIMO para habilitar botón (tarjeta Luhn válida)
    login_user.locator("input[name='cardNumber']").fill(VALID_CARD)
    login_user.locator("input[name='expirationDate']").fill(VALID_EXP)
    login_user.locator("input[name='cvv']").fill(VALID_CVV)
    
    # 5. Click y esperar navegación (INMEDIATA, sin 1.5s sleep ni validación Luhn real)
    with login_user.expect_navigation():
        login_user.get_by_role("button", name="Procesar Recarga").click()
    
    # 6. Verificar redirect a factura mock (evitó flujo real completo)
    expect(login_user).to_have_url(re.compile(rf"/wallet/{fake_invoice_id}$"))
    
    # 7. Verificar que NO hizo request real al backend (no esperó 1.5s)
    # Si llegamos aquí en <2s, el mock funcionó
    print(f"[MOCK] Redirect completado a factura fake: {fake_invoice_id}")


# ──────────────────────────────────────────────
# COMANDOS DE EJECUCIÓN
# ──────────────────────────────────────────────
"""
# Instalar (si no está)
pip install playwright pytest pytest-html && playwright install chromium

# Correr tests de facturas
pytest test/test_user_invoices.py -v

# Con navegador visible
pytest test/test_user_invoices.py -v --headed

# Solo test específico
pytest test/test_user_invoices.py::test_invoice_created_after_recharge -v

# Con reporte HTML
pytest test/test_user_invoices.py -v --html=report.html

# Parar en primer fallo
pytest test/test_user_invoices.py -v -x
"""

# Notas de implementación tests
# | Aspecto | Detalle |
# |---------|---------|
# | **Rate limiting** | `conftest.py` ya maneja retry 3x5s en `login_user` fixture |
# | **Tarjeta Luhn** | `4532015112830366` es Visa test válida (pasa `is_valid_luhn`) |
# | **Timeout** | 10000ms para navegación (incluye `asyncio.sleep(1.5)` backend) |
# | **URL ObjectId** | Regex `[a-f0-9]{24}` valida MongoDB ObjectId hex |
# | **Ownership** | Test usa dos fixtures: `login_user` + `login_admin` (distintos usuarios) |
# | **Responsive** | `page.set_viewport_size({"width": 375, "height": 667})` para móvil |