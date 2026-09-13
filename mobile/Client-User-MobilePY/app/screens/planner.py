import flet as ft
from app.stores.auth_store import auth_store
from app.stores.planner_store import planner_store


def PlannerScreen(page: ft.Page):
    origin_field = ft.TextField(label="Origen (direccion)", width=300)
    dest_field = ft.TextField(label="Destino (direccion)", width=300)
    result_card = ft.Container(visible=False)
    map_placeholder = ft.Container(
        content=ft.Text("Mapa aqui\n(Requiere Flet Google Maps plugin)", text_align=ft.TextAlign.CENTER),
        height=400,
        bgcolor=ft.Colors.GREY_200,
        border_radius=10,
    )

    async def on_search_origin(e):
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"https://nominatim.openstreetmap.org/search?q={origin_field.value}&countrycodes=gt&format=json&limit=1")
                data = resp.json()
                if data:
                    pass
        except Exception:
            pass

    async def on_pay(e):
        token = auth_store.token
        if token:
            await planner_store.plan_trip(token, originLat=14.62, originLon=-90.52, destLat=14.63, destLon=-90.51)
            page.snack_bar = ft.SnackBar(ft.Text("Viaje pagado!"))
            page.snack_bar.open = True
            page.update()

    return ft.Column(
        [
            ft.Text("Planificador de Viajes", size=24, weight=ft.FontWeight.BOLD),
            map_placeholder,
            ft.Container(padding=10),
            origin_field,
            dest_field,
            ft.ElevatedButton("Calcular Ruta", width=300, bgcolor=ft.Colors.BLUE_900, color=ft.Colors.WHITE),
            result_card,
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
    )
