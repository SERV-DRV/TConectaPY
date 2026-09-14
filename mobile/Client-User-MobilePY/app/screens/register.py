import flet as ft
from app.stores.auth_store import auth_store


def RegisterScreen(page: ft.Page):
    cui_field = ft.TextField(label="CUI / DPI", keyboard_type=ft.KeyboardType.NUMBER, max_length=13, width=300)
    email_field = ft.TextField(label="Correo electronico", keyboard_type=ft.KeyboardType.EMAIL, width=300)
    password_field = ft.TextField(label="Contrasena", password=True, can_reveal_password=True, width=300)
    error_text = ft.Text("", color=ft.Colors.RED_500, visible=False)
    register_btn = ft.ElevatedButton("Registrarse", width=300,
                                      bgcolor=ft.Colors.GREEN_500, color=ft.Colors.WHITE)

    async def do_register():
        if not cui_field.value or not email_field.value or not password_field.value:
            error_text.value = "Complete todos los campos"
            error_text.visible = True
            page.update()
            return
        if len(str(cui_field.value)) != 13:
            error_text.value = "El CUI debe tener 13 digitos"
            error_text.visible = True
            page.update()
            return
        register_btn.disabled = True
        page.update()
        success = await auth_store.register(cui_field.value, email_field.value, password_field.value)
        if success:
            from app.navigation import show_main
            show_main(page)
        else:
            error_text.value = "Error en el registro"
            error_text.visible = True
            register_btn.disabled = False
            page.update()

    register_btn.on_click = lambda e: page.run_task(do_register)

    return ft.Column(
        [
            ft.Container(
                content=ft.Column([
                    ft.Text("T-Conecta", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                    ft.Text("Crear Cuenta", size=16, color=ft.Colors.GREY_600),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=0,
            ),
            cui_field,
            email_field,
            password_field,
            error_text,
            register_btn,
            ft.TextButton("Ya tienes cuenta? Iniciar sesion", on_click=lambda e: _go_login(page)),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15,
    )


def _go_login(page: ft.Page):
    from app.navigation import show_login
    show_login(page)
