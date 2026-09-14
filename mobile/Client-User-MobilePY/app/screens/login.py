import flet as ft
from app.stores.auth_store import auth_store


def LoginScreen(page: ft.Page):
    cui_field = ft.TextField(label="CUI / DPI", keyboard_type=ft.KeyboardType.NUMBER, max_length=13, width=300)
    password_field = ft.TextField(label="Contrasena", password=True, can_reveal_password=True, width=300)
    error_text = ft.Text("", color=ft.Colors.RED_500, visible=False)
    login_btn = ft.ElevatedButton("Iniciar sesion", width=300,
                                   bgcolor=ft.Colors.BLUE_900, color=ft.Colors.WHITE)

    async def do_login():
        if not cui_field.value or not password_field.value:
            error_text.value = "Complete todos los campos"
            error_text.visible = True
            page.update()
            return
        login_btn.disabled = True
        page.update()
        success = await auth_store.login(cui_field.value, password_field.value)
        if success:
            from app.navigation import show_main
            show_main(page)
        else:
            error_text.value = "Credenciales invalidas"
            error_text.visible = True
            login_btn.disabled = False
            page.update()

    login_btn.on_click = lambda e: page.run_task(do_login)

    return ft.Column(
        [
            ft.Container(
                content=ft.Column([
                    ft.Text("T-Conecta", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                    ft.Text("Ciudadano", size=16, color=ft.Colors.GREY_600),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=0,
            ),
            cui_field,
            password_field,
            error_text,
            login_btn,
            ft.TextButton("No tienes cuenta? Registrarse", on_click=lambda e: _go_register(page)),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15,
    )


def _go_register(page: ft.Page):
    from app.navigation import show_register
    show_register(page)
