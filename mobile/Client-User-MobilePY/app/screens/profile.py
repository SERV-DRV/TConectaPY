import flet as ft
from app.stores.auth_store import auth_store


def ProfileScreen(page: ft.Page):
    user = auth_store.user or {}

    def on_logout(e):
        auth_store.logout()
        from app.navigation import show_login
        show_login(page)

    return ft.Column(
        [
            ft.Container(
                content=ft.Column([
                    ft.Text("Mi Perfil", size=24, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.Row([ft.Text("CUI:"), ft.Text(user.get("cui", "-"), weight=ft.FontWeight.BOLD)]),
                    ft.Row([ft.Text("Rol:"), ft.Container(
                        content=ft.Text(user.get("role", "User"), size=10, color=ft.Colors.WHITE),
                        bgcolor=ft.Colors.PURPLE_500,
                        border_radius=5,
                        padding=ft.Padding(left=8, right=8, top=2, bottom=2),
                    )]),
                    ft.Row([ft.Text("Estado:"), ft.Text("Activo", color=ft.Colors.GREEN_500)]),
                    ft.Divider(),
                    ft.ElevatedButton("Cerrar sesion", on_click=on_logout,
                                      bgcolor=ft.Colors.RED_500, color=ft.Colors.WHITE, width=300),
                ]),
                padding=20,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,
    )
