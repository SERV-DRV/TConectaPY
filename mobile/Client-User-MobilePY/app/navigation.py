import flet as ft


def show_login(page: ft.Page):
    from app.screens.login import LoginScreen
    page.controls.clear()
    page.controls.append(
        ft.Column(
            [LoginScreen(page)],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )
    )
    page.update()


def show_register(page: ft.Page):
    from app.screens.register import RegisterScreen
    page.controls.clear()
    page.controls.append(
        ft.Column(
            [RegisterScreen(page)],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )
    )
    page.update()


def show_main(page: ft.Page):
    from app.screens.planner import PlannerScreen
    from app.screens.wallet import WalletScreen
    from app.screens.explore import ExploreScreen
    from app.screens.alerts import AlertsScreen
    from app.screens.profile import ProfileScreen

    screens_cache = {}

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
        content_area.content = get_screen(index)
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
        bgcolor=ft.Colors.WHITE,
        indicator_color=ft.Colors.GREEN_500,
    )

    content_area = ft.Container(content=get_screen(0), expand=True)

    page.controls.clear()
    page.controls.append(nav_bar)
    page.controls.append(content_area)
    page.update()
