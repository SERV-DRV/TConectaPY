import flet as ft
from app.stores.auth_store import auth_store
from app.stores.planner_store import planner_store


def ExploreScreen(page: ft.Page):
    roads_list = ft.Column()
    stations_list = ft.Column()
    loading_text = ft.Text("Cargando...", color=ft.Colors.GREY_500)

    roads_container = ft.Container(content=roads_list, visible=True)
    stations_container = ft.Container(content=stations_list, visible=False)

    async def load_data():
        token = auth_store.token
        if not token:
            roads_list.controls.clear()
            roads_list.controls.append(ft.Text("Inicia sesion para ver datos", color=ft.Colors.GREY_500))
            page.update()
            return

        loading_text.visible = True
        page.update()

        try:
            await planner_store.fetch_map_data(token)
        except Exception as ex:
            print(f"[EXPLORE] fetch_map_data exception: {ex}")

        loading_text.visible = False
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
                    leading=ft.Icon(ft.Icons.DIRECTIONS_BUS),
                ))
            )
        if not planner_store.roads:
            roads_list.controls.append(ft.Text("No hay rutas disponibles", color=ft.Colors.GREY_500))
        if not planner_store.stations:
            stations_list.controls.append(ft.Text("No hay estaciones disponibles", color=ft.Colors.GREY_500))

        page.update()

    def on_roads(e):
        roads_container.visible = True
        stations_container.visible = False
        tab_roads.content = ft.Text("Rutas", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900)
        tab_stations.content = ft.Text("Estaciones", weight=ft.FontWeight.NORMAL, color=ft.Colors.GREY_500)
        page.update()

    def on_stations(e):
        roads_container.visible = False
        stations_container.visible = True
        tab_roads.content = ft.Text("Rutas", weight=ft.FontWeight.NORMAL, color=ft.Colors.GREY_500)
        tab_stations.content = ft.Text("Estaciones", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900)
        page.update()

    tab_roads = ft.Container(
        content=ft.Text("Rutas", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
        padding=10,
        on_click=on_roads,
    )
    tab_stations = ft.Container(
        content=ft.Text("Estaciones", weight=ft.FontWeight.NORMAL, color=ft.Colors.GREY_500),
        padding=10,
        on_click=on_stations,
    )

    page.run_task(load_data)

    return ft.Column(
        [
            ft.Text("Infraestructura", size=24, weight=ft.FontWeight.BOLD),
            ft.Row([tab_roads, tab_stations]),
            loading_text,
            roads_container,
            stations_container,
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )
