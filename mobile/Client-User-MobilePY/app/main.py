import flet as ft
from app.stores.auth_store import auth_store
from app.navigation import show_login, show_register, show_main


def main(page: ft.Page):
    page.title = "T-Conecta Ciudadano"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 400
    page.window.height = 700

    auth_store.init_auth()

    if auth_store.is_authenticated:
        show_main(page)
    else:
        show_login(page)


ft.run(main)
