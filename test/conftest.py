import re
import time
import pytest
from playwright.sync_api import Page, expect

ADMIN_URL = "http://localhost:5173"
USER_URL = "http://localhost:5174"
MAX_RETRIES = 3
RETRY_DELAY = 5

def _login(page, url, cui_placeholder, cui, password_selector, password, redirect_pattern):
    for attempt in range(MAX_RETRIES):
        page.goto(f"{url}/auth/login")
        page.get_by_placeholder(cui_placeholder).fill(cui)
        page.locator(password_selector).fill(password)
        page.get_by_role("button", name="Iniciar sesion").click()

        try:
            expect(page).to_have_url(re.compile(redirect_pattern), timeout=10000)
            return
        except Exception:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise

@pytest.fixture
def login_admin(page: Page):
    _login(page, ADMIN_URL, "Ej: 0000000000000", "1000000000001",
           "input[name='password']", "Admin123!", r"/dashboard$")
    return page

@pytest.fixture
def login_user(page: Page):
    _login(page, USER_URL, "CUI (13 digitos)", "2000000000002",
           "input[name='password']", "Usuario123!", r"/planner$")
    return page
