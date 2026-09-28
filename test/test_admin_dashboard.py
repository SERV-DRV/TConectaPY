from playwright.sync_api import Page, expect

def test_admin_dashboard(login_admin: Page):
    login_admin.wait_for_load_state("networkidle")
    expect(login_admin.get_by_role("heading", name="Dashboard")).to_be_visible()
