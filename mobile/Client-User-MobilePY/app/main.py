import flet as ft
from app.stores.auth_store import auth_store
from app.navigation.router import AppRouter


def main(page: ft.Page):
    page.title = "T-Conecta Ciudadano"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 400
    page.window.height = 700

    auth_store.init_auth()
    router = AppRouter(page)
    page.add(router.build())
    page.update()


ft.app(target=main)
