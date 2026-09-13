import flet as ft
from app.stores.auth_store import auth_store


def RegisterScreen(page: ft.Page):
    cui_field = ft.TextField(label="CUI / DPI", keyboard_type=ft.KeyboardType.NUMBER, max_length=13, width=300)
    email_field = ft.TextField(label="Correo electronico", keyboard_type=ft.KeyboardType.EMAIL, width=300)
    password_field = ft.TextField(label="Contrasena", password=True, can_reveal_password=True, width=300)
    error_text = ft.Text("", color=ft.Colors.RED_500, visible=False)

    async def on_register(e):
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
        success = await auth_store.register(cui_field.value, email_field.value, password_field.value)
        if success:
            from app.navigation.router import AppRouter
            router = AppRouter(page)
            page.views.clear()
            page.views.append(router.build())
            page.update()
        else:
            error_text.value = "Error en el registro"
            error_text.visible = True
            page.update()

    return ft.Column(
        [
            ft.Container(
                content=ft.Column([
                    ft.Text("T-Conecta", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                    ft.Text("Crear Cuenta", size=16, color=ft.Colors.GREY_600),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.all(0),
            ),
            cui_field,
            email_field,
            password_field,
            error_text,
            ft.ElevatedButton("Registrarse", on_click=on_register, width=300,
                              bgcolor=ft.Colors.GREEN_500, color=ft.Colors.WHITE),
            ft.TextButton("Ya tienes cuenta? Iniciar sesion", on_click=lambda e: page.go("/login")),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15,
    )
