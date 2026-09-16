import flet as ft
from app.stores.auth_store import auth_store
from app.screens.login import LoginScreen
from app.screens.register import RegisterScreen
from app.screens.planner import PlannerScreen
from app.screens.wallet import WalletScreen
from app.screens.explore import ExploreScreen
from app.screens.alerts import AlertsScreen
from app.screens.profile import ProfileScreen


SCREEN_FACTORIES = [
    PlannerScreen,
    WalletScreen,
    ExploreScreen,
    AlertsScreen,
    ProfileScreen,
]


def _build_login_view(page: ft.Page):
    return ft.Column(
        [LoginScreen(page)],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        expand=True,
    )


def _build_register_view(page: ft.Page):
    return ft.Column(
        [RegisterScreen(page)],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        expand=True,
    )


def _build_main_view(page: ft.Page):
    screens_cache = {}
    content_area = ft.Container(expand=True)

    def get_screen(index):
        builders = [
            lambda: PlannerScreen(page),
            lambda: WalletScreen(page),
            lambda: ExploreScreen(page),
            lambda: AlertsScreen(page),
            lambda: ProfileScreen(page),
        ]
        if index not in screens_cache:
            screens_cache[index] = builders[index]()
        return screens_cache[index]

    def on_tab_change(e):
        index = nav_bar.selected_index
        screen = get_screen(index)
        content_area.content = screen
        if hasattr(screen, '_refresh'):
            page.run_task(screen._refresh)
        page.update()

    nav_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.MAP, label="Planificador"),
            ft.NavigationBarDestination(icon=ft.Icons.CREDIT_CARD, label="Billetera"),
            ft.NavigationBarDestination(icon=ft.Icons.BUS_ALERT, label="Explorar"),
            ft.NavigationBarDestination(icon=ft.Icons.WARNING, label="Alertas"),
            ft.NavigationBarDestination(icon=ft.Icons.PERSON, label="Perfil"),
        ],
        on_change=on_tab_change,
        selected_index=0,
    )

    content_area.content = get_screen(0)

    return ft.Column(
        [nav_bar, content_area],
        expand=True,
        spacing=0,
    )


def show_login(page: ft.Page):
    page.controls.clear()
    page.controls.append(_build_login_view(page))
    page.update()


def show_register(page: ft.Page):
    page.controls.clear()
    page.controls.append(_build_register_view(page))
    page.update()


def show_main(page: ft.Page):
    page.controls.clear()
    page.controls.append(_build_main_view(page))
    page.update()


class AppRouter:
    def __init__(self, page: ft.Page):
        self.page = page

    def go_login(self):
        show_login(self.page)

    def go_register(self):
        show_register(self.page)

    def go_main(self):
        show_main(self.page)
