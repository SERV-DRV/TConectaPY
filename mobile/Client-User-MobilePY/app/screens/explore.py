import flet as ft
from app.stores.auth_store import auth_store
from app.stores.planner_store import planner_store


def ExploreScreen(page: ft.Page):
    roads_list = ft.Column()
    stations_list = ft.Column()
    tabs = ft.Tabs(selected_index=0, tabs=[
        ft.Tab(text="Rutas"),
        ft.Tab(text="Estaciones"),
    ])

    async def load_data(e=None):
        token = auth_store.token
        if token:
            await planner_store.fetch_map_data(token)
            roads_list.controls.clear()
            stations_list.controls.clear()
            for road in planner_store.roads:
                roads_list.controls.append(
                    ft.Card(content=ft.ListTile(
                        title=ft.Text(road.get("name", "")),
                        subtitle=ft.Text(f"{road.get('routeCode', '')} - {road.get('typeRoad', '')}"),
                        leading=ft.Icon(ft.Icons.ROUTE),
                    ))
                )
            for station in planner_store.stations:
                stations_list.controls.append(
                    ft.Card(content=ft.ListTile(
                        title=ft.Text(station.get("name", "")),
                        subtitle=ft.Text(f"{station.get('stationCode', '')} - {station.get('typeStation', '')}"),
                        leading=ft.Icon(ft.Icons.LOCAL_BUS),
                    ))
                )
            page.update()

    page.on_mount = load_data

    return ft.Column(
        [
            ft.Text("Infraestructura", size=24, weight=ft.FontWeight.BOLD),
            tabs,
            ft.Container(
                content=roads_list if tabs.selected_index == 0 else stations_list,
                expand=True,
            ),
        ],
        expand=True,
    )
