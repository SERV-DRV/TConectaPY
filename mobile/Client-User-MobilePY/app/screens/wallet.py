import flet as ft
from app.stores.auth_store import auth_store
from app.stores.wallet_store import wallet_store


def WalletScreen(page: ft.Page):
    balance_text = ft.Text("Q0.00", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
    status_text = ft.Text("", size=12, color=ft.Colors.GREY_600)
    amount_field = ft.TextField(label="Monto (Q)", keyboard_type=ft.KeyboardType.NUMBER, width=300)
    card_field_recharge = ft.TextField(label="Numero de tarjeta", keyboard_type=ft.KeyboardType.NUMBER, max_length=16, width=300)
    exp_field_recharge = ft.TextField(label="MM/YY", width=140)
    cvv_field_recharge = ft.TextField(label="CVV", password=True, width=140)
    card_field_purchase = ft.TextField(label="Numero de tarjeta", keyboard_type=ft.KeyboardType.NUMBER, max_length=16, width=300)
    exp_field_purchase = ft.TextField(label="MM/YY", width=140)
    cvv_field_purchase = ft.TextField(label="CVV", password=True, width=140)

    recharge_form = ft.Column([
        amount_field,
        card_field_recharge,
        ft.Row([exp_field_recharge, cvv_field_recharge]),
    ], visible=True)

    purchase_form = ft.Column([
        card_field_purchase,
        ft.Row([exp_field_purchase, cvv_field_purchase]),
    ], visible=False)

    recharge_btn = ft.ElevatedButton("Recargar", width=300, bgcolor=ft.Colors.GREEN_500, color=ft.Colors.WHITE)

    purchase_btn = ft.ElevatedButton("Comprar Tarjeta (Q20)", width=300, bgcolor=ft.Colors.BLUE_900, color=ft.Colors.WHITE)

    def on_tab_recharge(e):
        recharge_form.visible = True
        purchase_form.visible = False
        recharge_btn.visible = True
        purchase_btn.visible = False
        tab_recharge.content = ft.Text("Recargar", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900)
        tab_purchase.content = ft.Text("Comprar Tarjeta", weight=ft.FontWeight.NORMAL, color=ft.Colors.GREY_500)
        page.update()

    def on_tab_purchase(e):
        recharge_form.visible = False
        purchase_form.visible = True
        recharge_btn.visible = False
        purchase_btn.visible = True
        tab_recharge.content = ft.Text("Recargar", weight=ft.FontWeight.NORMAL, color=ft.Colors.GREY_500)
        tab_purchase.content = ft.Text("Comprar Tarjeta", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900)
        page.update()

    tab_recharge = ft.Container(
        content=ft.Text("Recargar", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
        padding=10,
        on_click=on_tab_recharge,
    )
    tab_purchase = ft.Container(
        content=ft.Text("Comprar Tarjeta", weight=ft.FontWeight.NORMAL, color=ft.Colors.GREY_500),
        padding=10,
        on_click=on_tab_purchase,
    )

    async def load_balance():
        token = auth_store.token
        if token:
            try:
                await wallet_store.fetch_balance(token)
                balance_text.value = f"Q{wallet_store.balance:.2f}"
                print(f"[WALLET] Balance loaded: {wallet_store.balance}")
            except Exception as ex:
                print(f"[WALLET ERROR] load_balance: {ex}")
                balance_text.value = "Q0.00"
                status_text.value = "Saldo no disponible (servicio)"
            page.update()

    async def do_recharge():
        token = auth_store.token
        if not token:
            status_text.value = "Inicia sesion primero"
            page.update()
            return
        if not amount_field.value:
            status_text.value = "Ingresa un monto"
            page.update()
            return
        status_text.value = "Procesando recarga..."
        recharge_btn.disabled = True
        page.update()
        try:
            success = await wallet_store.recharge(
                token,
                card_field_recharge.value or "",
                exp_field_recharge.value or "",
                cvv_field_recharge.value or "",
                float(amount_field.value),
            )
            if success:
                status_text.value = wallet_store.last_message or "Recarga exitosa!"
                await load_balance()
            else:
                status_text.value = wallet_store.last_message or "Error en la recarga"
        except Exception as ex:
            status_text.value = f"Error: {ex}"
            print(f"[WALLET ERROR] recharge: {ex}")
        recharge_btn.disabled = False
        page.update()

    async def do_purchase():
        token = auth_store.token
        if not token:
            status_text.value = "Inicia sesion primero"
            page.update()
            return
        status_text.value = "Procesando compra..."
        purchase_btn.disabled = True
        page.update()
        try:
            success = await wallet_store.purchase_card(
                token,
                card_field_purchase.value or "",
                exp_field_purchase.value or "",
                cvv_field_purchase.value or "",
            )
            if success:
                status_text.value = wallet_store.last_message or "Tarjeta comprada!"
                await load_balance()
            else:
                status_text.value = wallet_store.last_message or "Error en la compra"
        except Exception as ex:
            status_text.value = f"Error: {ex}"
            print(f"[WALLET ERROR] purchase: {ex}")
        purchase_btn.disabled = False
        page.update()

    recharge_btn.on_click = lambda e: page.run_task(do_recharge)
    purchase_btn.on_click = lambda e: page.run_task(do_purchase)

    page.run_task(load_balance)

    col = ft.Column(
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
            status_text,
            ft.Row([tab_recharge, tab_purchase]),
            recharge_form,
            purchase_form,
            recharge_btn,
            purchase_btn,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15,
        scroll=ft.ScrollMode.AUTO,
    )
    col._refresh = load_balance
    return col
