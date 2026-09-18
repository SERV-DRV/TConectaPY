import flet as ft


def main(page: ft.Page):
    page.title = "T-Conecta Ciudadano"
    page.theme_mode = ft.ThemeMode.LIGHT
    try:
        page.window.width = 400
        page.window.height = 700
    except Exception:
        pass

    from app.stores.auth_store import auth_store
    try:
        auth_store.init_auth()
    except Exception as ex:
        print(f"[MAIN] init_auth error: {ex}")

    from app.navigation import show_login, show_main
    try:
        if auth_store.is_authenticated:
            show_main(page)
        else:
            show_login(page)
    except Exception as ex:
        print(f"[MAIN] navigation error: {ex}")
        try:
            show_login(page)
        except Exception as ex2:
            print(f"[MAIN] fallback login error: {ex2}")
            page.controls.append(
                ft.Column(
                    [
                        ft.Text("T-Conecta", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                        ft.Text("Error al iniciar. Reinstala la app.", color=ft.Colors.RED_500),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
            page.update()


ft.run(main)
