import flet as ft
from app.stores.auth_store import auth_store
from app.screens.login import LoginScreen
from app.screens.register import RegisterScreen
from app.screens.planner import PlannerScreen
from app.screens.wallet import WalletScreen
from app.screens.explore import ExploreScreen
from app.screens.alerts import AlertsScreen
from app.screens.profile import ProfileScreen


class AppRouter:
    def __init__(self, page: ft.Page):
        self.page = page

    def build(self):
        if not auth_store.is_authenticated:
            return ft.View(
                "/auth",
                [LoginScreen(self.page)],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                vertical_alignment=ft.MainAxisAlignment.CENTER,
            )

        return ft.View(
            "/",
            [
                ft.NavigationBar(
                    destinations=[
                        ft.NavigationBarDestination(icon=ft.Icons.MAP, text="Planificador"),
                        ft.NavigationBarDestination(icon=ft.Icons.CREDIT_CARD, text="Billetera"),
                        ft.NavigationBarDestination(icon=ft.Icons.BUS_ALERT, text="Explorar"),
                        ft.NavigationBarDestination(icon=ft.Icons.WARNING, text="Alertas"),
                        ft.NavigationBarDestination(icon=ft.Icons.PERSON, text="Perfil"),
                    ],
                    on_change=lambda e: self._on_tab_change(e.control.selected_index),
                    selected_index=0,
                    bgcolor=ft.Colors.WHITE,
                    indicator_color=ft.Colors.GREEN_500,
                ),
                ft.Container(
                    content=PlannerScreen(self.page),
                    expand=True,
                ),
            ],
            padding=0,
        )

    def _on_tab_change(self, index: int):
        screens = [
            PlannerScreen(self.page),
            WalletScreen(self.page),
            ExploreScreen(self.page),
            AlertsScreen(self.page),
            ProfileScreen(self.page),
        ]
        self.page.views.clear()
        self.page.views.append(
            ft.View(
                "/",
                [
                    ft.NavigationBar(
                        destinations=[
                            ft.NavigationBarDestination(icon=ft.Icons.MAP, text="Planificador"),
                            ft.NavigationBarDestination(icon=ft.Icons.CREDIT_CARD, text="Billetera"),
                            ft.NavigationBarDestination(icon=ft.Icons.BUS_ALERT, text="Explorar"),
                            ft.NavigationBarDestination(icon=ft.Icons.WARNING, text="Alertas"),
                            ft.NavigationBarDestination(icon=ft.Icons.PERSON, text="Perfil"),
                        ],
                        on_change=lambda e: self._on_tab_change(e.control.selected_index),
                        selected_index=index,
                    ),
                    ft.Container(content=screens[index], expand=True),
                ],
                padding=0,
            )
        )
        self.page.update()

    def go_login(self):
        self.page.views.clear()
        self.page.views.append(
            ft.View("/auth", [LoginScreen(self.page)])
        )
        self.page.update()
