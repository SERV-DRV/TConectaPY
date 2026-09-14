import flet as ft
from app.stores.auth_store import auth_store
from app.stores.alerts_store import alerts_store


def AlertsScreen(page: ft.Page):
    alerts_list = ft.Column()

    async def load_alerts():
        token = auth_store.token
        if token:
            await alerts_store.fetch_alerts(token)
            alerts_list.controls.clear()
            for alert in alerts_store.alerts:
                alert_type = alert.get("typeAlert", "INFO")
                color = ft.Colors.BLUE if alert_type == "INFO" else ft.Colors.RED if alert_type == "INCIDENT" else ft.Colors.AMBER
                alerts_list.controls.append(
                    ft.Card(content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Container(
                                    content=ft.Text(alert_type, size=10, color=ft.Colors.WHITE),
                                    bgcolor=color,
                                    border_radius=5,
                                    padding=ft.Padding(left=8, right=8, top=2, bottom=2),
                                ),
                                ft.Text(alert.get("created_at", ""), size=10, color=ft.Colors.GREY_500),
                            ]),
                            ft.Text(alert.get("title", ""), weight=ft.FontWeight.BOLD),
                            ft.Text(alert.get("description", ""), size=12, color=ft.Colors.GREY_600),
                        ]),
                        padding=15,
                    ))
                )
            if not alerts_store.alerts:
                alerts_list.controls.append(ft.Text("No hay alertas", color=ft.Colors.GREY_500))
            page.update()

    def on_mount(e):
        page.run_task(load_alerts)

    page.on_mount = on_mount
    page.run_task(load_alerts)

    return ft.Column(
        [
            ft.Text("Alertas de Servicio", size=24, weight=ft.FontWeight.BOLD),
            alerts_list,
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )
