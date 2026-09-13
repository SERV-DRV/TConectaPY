import flet as ft
from app.stores.auth_store import auth_store
from app.stores.wallet_store import wallet_store


def WalletScreen(page: ft.Page):
    balance_text = ft.Text("Q0.00", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
    amount_field = ft.TextField(label="Monto (Q)", keyboard_type=ft.KeyboardType.NUMBER, width=300)
    card_field = ft.TextField(label="Numero de tarjeta", keyboard_type=ft.KeyboardType.NUMBER, max_length=16, width=300)
    exp_field = ft.TextField(label="MM/YY", width=140)
    cvv_field = ft.TextField(label="CVV", password=True, width=140)
    tabs = ft.Tabs(selected_index=0, tabs=[
        ft.Tab(text="Recargar"),
        ft.Tab(text="Comprar Tarjeta"),
    ])
    tab_content = ft.Container()

    async def load_balance(e=None):
        token = auth_store.token
        if token:
            await wallet_store.fetch_balance(token)
            balance_text.value = f"Q{wallet_store.balance:.2f}"
            page.update()

    async def on_recharge(e):
        token = auth_store.token
        if token and amount_field.value:
            success = await wallet_store.recharge(token, card_field.value or "", exp_field.value or "", cvv_field.value or "", float(amount_field.value))
            if success:
                page.snack_bar = ft.SnackBar(ft.Text("Recarga exitosa!"))
                page.snack_bar.open = True
                await load_balance()
                page.update()

    async def on_purchase(e):
        token = auth_store.token
        if token:
            success = await wallet_store.purchase_card(token, card_field.value or "", exp_field.value or "", cvv_field.value or "")
            if success:
                page.snack_bar = ft.SnackBar(ft.Text("Tarjeta comprada!"))
                page.snack_bar.open = True
                await load_balance()
                page.update()

    page.on_mount = load_balance

    return ft.Column(
        [
            ft.Container(
                content=ft.Column([
                    ft.Text("Saldo disponible", color=ft.Colors.WHITE70),
                    balance_text,
                    ft.Text("T-Conecta", color=ft.Colors.WHITE70),
                ]),
                gradient=ft.LinearGradient(colors=[ft.Colors.BLUE_900, ft.Colors.PURPLE_900]),
                border_radius=15,
                padding=20,
                width=350,
            ),
            tabs,
            amount_field,
            card_field,
            ft.Row([exp_field, cvv_field]),
            ft.ElevatedButton("Recargar", on_click=on_recharge, width=300, bgcolor=ft.Colors.GREEN_500, color=ft.Colors.WHITE),
            ft.ElevatedButton("Comprar Tarjeta (Q20)", on_click=on_purchase, width=300, bgcolor=ft.Colors.BLUE_900, color=ft.Colors.WHITE),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15,
        scroll=ft.ScrollMode.AUTO,
    )
