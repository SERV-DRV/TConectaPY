import flet as ft


def show_snackbar(page: ft.Page, message: str, bgcolor=None, color=None):
    try:
        sb = ft.SnackBar(
            ft.Text(message, color=color or ft.Colors.WHITE),
            bgcolor=bgcolor or ft.Colors.GREY_800,
        )
        page.overlay.append(sb)
        sb.open = True
        page.update()
    except Exception as ex:
        print(f"[SNACKBAR ERROR] {ex}")
