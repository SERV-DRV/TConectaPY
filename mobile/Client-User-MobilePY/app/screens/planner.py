import flet as ft
import httpx
from app.stores.auth_store import auth_store
from app.stores.planner_store import planner_store
from app.stores.wallet_store import wallet_store
from app.utils.ui_helpers import show_snackbar

try:
    import flet_map as fmap
    HAS_FLET_MAP = True
except Exception as ex:
    print(f"[PLANNER] flet_map import error: {ex}")
    HAS_FLET_MAP = False


def PlannerScreen(page: ft.Page):
    origin_field = ft.TextField(label="Origen (ej: Irtra Petapa)", width=300)
    dest_field = ft.TextField(label="Destino (ej: USAC)", width=300)
    tap_mode = ft.Text("Toca el mapa para seleccionar puntos", size=12, color=ft.Colors.GREY_600)

    status_text = ft.Text("", size=12, color=ft.Colors.GREY_600)
    res_tiempo = ft.Text(size=14, weight=ft.FontWeight.BOLD)
    res_distancia = ft.Text(size=14, color=ft.Colors.GREY_700)

    result_card = ft.Container(
        content=ft.Column([
            ft.Text("Resumen del Viaje", weight=ft.FontWeight.BOLD),
            res_tiempo,
            res_distancia
        ]),
        visible=False,
        bgcolor=ft.Colors.GREEN_50,
        padding=10,
        border_radius=10,
        width=300
    )

    if not HAS_FLET_MAP:
        def _no_map_msg():
            return ft.Column([
                ft.Icon(ft.Icons.MAP, size=60, color=ft.Colors.GREY_400),
                ft.Text("Mapa no disponible", size=18, color=ft.Colors.GREY_600),
                ft.Text("flet-map no se pudo cargar", size=12, color=ft.Colors.GREY_500),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
        return ft.Column([
            ft.Text("Planificador de Viajes", size=24, weight=ft.FontWeight.BOLD),
            _no_map_msg(),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)

    coords = {"origin": None, "dest": None}
    next_point = "origin"
    current_itinerary = ""

    def build_map(center_lat=14.62, center_lon=-90.52, zoom=12, markers=None, pts=None, tap_handler=None):
        if not HAS_FLET_MAP:
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.MAP, size=60, color=ft.Colors.GREY_400),
                    ft.Text("Mapa no disponible", size=16, color=ft.Colors.GREY_600),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                height=350,
            )
        layers = [fmap.TileLayer(
            url_template="https://tile-a.openstreetmap.fr/hot/{z}/{x}/{y}.png",
            user_agent_package_name="com.tconecta.app",
        )]
        if pts:
            layers.append(fmap.PolylineLayer(polylines=[
                fmap.PolylineMarker(coordinates=pts, color=ft.Colors.BLUE_700, stroke_width=4)
            ]))
        if markers:
            layers.append(fmap.MarkerLayer(markers=markers))

        return fmap.Map(
            expand=True,
            initial_center=fmap.MapLatitudeLongitude(center_lat, center_lon),
            initial_zoom=zoom,
            layers=layers,
            on_tap=tap_handler,
        )

    def on_map_tap(e):
        nonlocal next_point
        if not e.coordinates:
            return
        lat = e.coordinates.latitude
        lon = e.coordinates.longitude
        if next_point == "origin":
            coords["origin"] = (lat, lon)
            origin_field.value = f"({lat:.4f}, {lon:.4f})"
            next_point = "dest"
            tap_mode.value = "Ahora toca para el destino"
        else:
            coords["dest"] = (lat, lon)
            dest_field.value = f"({lat:.4f}, {lon:.4f})"
            next_point = "origin"
            tap_mode.value = "Puntos seleccionados. Calcular ruta!"
        update_map_visual()
        page.update()

    def update_map_visual():
        markers = []
        if coords["origin"]:
            markers.append(fmap.Marker(
                content=ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.GREEN, size=40),
                coordinates=fmap.MapLatitudeLongitude(*coords["origin"]),
            ))
        if coords["dest"]:
            markers.append(fmap.Marker(
                content=ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.RED, size=40),
                coordinates=fmap.MapLatitudeLongitude(*coords["dest"]),
            ))
        center_lat = 14.62
        center_lon = -90.52
        zoom = 12
        if coords["origin"] and coords["dest"]:
            center_lat = (coords["origin"][0] + coords["dest"][0]) / 2
            center_lon = (coords["origin"][1] + coords["dest"][1]) / 2
            zoom = 13
        elif coords["origin"]:
            center_lat, center_lon = coords["origin"]
            zoom = 15

        map_container.content = build_map(
            center_lat=center_lat, center_lon=center_lon, zoom=zoom,
            markers=markers if markers else None, tap_handler=on_map_tap,
        )

    map_container = ft.Container(
        content=build_map(tap_handler=on_map_tap),
        height=350,
        border_radius=10,
    )

    async def geocode(query):
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                res = await client.get(
                    "https://nominatim.openstreetmap.org/search",
                    params={"q": query, "countrycodes": "gt", "format": "json", "limit": "1"},
                    headers={"User-Agent": "TConectaApp/1.0"},
                )
                data = res.json()
                if data:
                    return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception as ex:
            print(f"Geocode error: {ex}")
        return None

    async def do_my_location():
        status_text.value = "Obteniendo ubicacion..."
        page.update()
        loc = await geocode("Guatemala, Zona 10, Guatemala")
        if loc:
            coords["origin"] = loc
            origin_field.value = f"Zona 10 ({loc[0]:.4f}, {loc[1]:.4f})"
            next_point = "dest"
            tap_mode.value = "Ahora toca el mapa para el destino"
            update_map_visual()
            status_text.value = "Ubicacion detectada. Selecciona destino."
        else:
            status_text.value = "No se pudo obtener ubicacion"
        page.update()

    async def do_calculate():
        nonlocal current_itinerary
        origin_text = origin_field.value.strip()
        dest_text = dest_field.value.strip()

        if not origin_text and not coords["origin"]:
            status_text.value = "Ingresa un origen o toca el mapa"
            page.update()
            return
        if not dest_text and not coords["dest"]:
            status_text.value = "Ingresa un destino o toca el mapa"
            page.update()
            return

        status_text.value = "Buscando ubicaciones..."
        result_card.visible = False
        origin_btn.disabled = True
        page.update()

        orig_c = coords["origin"]
        dest_c = coords["dest"]

        if not orig_c and origin_text:
            orig_c = await geocode(origin_text)
        if not dest_c and dest_text:
            dest_c = await geocode(dest_text)

        if not orig_c:
            status_text.value = "No se encontro el origen"
            origin_btn.disabled = False
            page.update()
            return
        if not dest_c:
            status_text.value = "No se encontro el destino"
            origin_btn.disabled = False
            page.update()
            return

        coords["origin"] = orig_c
        coords["dest"] = dest_c

        status_text.value = "Calculando ruta..."
        page.update()

        markers = [
            fmap.Marker(content=ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.GREEN, size=40), coordinates=fmap.MapLatitudeLongitude(*orig_c)),
            fmap.Marker(content=ft.Icon(ft.Icons.LOCATION_ON, color=ft.Colors.RED, size=40), coordinates=fmap.MapLatitudeLongitude(*dest_c)),
        ]

        mid_lat = (orig_c[0] + dest_c[0]) / 2
        mid_lon = (orig_c[1] + dest_c[1]) / 2

        polyline_pts = None
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                url = f"https://router.project-osrm.org/route/v1/driving/{orig_c[1]},{orig_c[0]};{dest_c[1]},{dest_c[0]}?geometries=geojson"
                res = await client.get(url)
                route_data = res.json()

                if route_data.get("routes"):
                    route = route_data["routes"][0]
                    polyline_pts = [fmap.MapLatitudeLongitude(p[1], p[0]) for p in route["geometry"]["coordinates"]]

                    dist_km = route["distance"] / 1000
                    mins = round(route["duration"] / 60)
                    res_tiempo.value = f"Tiempo estimado: {mins} min"
                    res_distancia.value = f"Distancia: {dist_km:.2f} km"
                    result_card.visible = True
                    status_text.value = ""

                    current_itinerary = ""
                    stations = planner_store.stations
                    roads = planner_store.roads
                    if stations and orig_c and dest_c:
                        def station_dist(slat, slon, plat, plon):
                            import math
                            return math.sqrt((slat - plat)**2 + (slon - plon)**2)
                        nearest_orig = min(stations, key=lambda s: station_dist(
                            s.get("location", {}).get("coordinates", [0, 0])[1],
                            s.get("location", {}).get("coordinates", [0, 0])[0],
                            orig_c[0], orig_c[1]))
                        nearest_dest = min(stations, key=lambda s: station_dist(
                            s.get("location", {}).get("coordinates", [0, 0])[1],
                            s.get("location", {}).get("coordinates", [0, 0])[0],
                            dest_c[0], dest_c[1]))
                        orig_name = nearest_orig.get("name", "Origen")
                        dest_name = nearest_dest.get("name", "Destino")
                        road_name = roads[0].get("name", "ruta") if roads else "ruta"
                        if nearest_orig.get("_id") == nearest_dest.get("_id"):
                            current_itinerary = f"1. Camina hacia Estacion {orig_name}.\n2. Toma ruta con transbordo hacia troncales.\n3. Baja en Estacion {dest_name}.\n4. Camina hacia tu destino."
                        else:
                            current_itinerary = f"1. Camina hacia Estacion {orig_name}.\n2. Aborda Ruta {road_name}.\n3. Baja en Estacion {dest_name}.\n4. Camina hacia tu destino."
                    else:
                        current_itinerary = ""
                else:
                    status_text.value = "No se encontro ruta entre los puntos"
        except Exception as ex:
            status_text.value = f"Error calculando ruta: {ex}"
            print("Error ruta:", ex)

        map_container.content = build_map(
            center_lat=mid_lat, center_lon=mid_lon, zoom=13,
            markers=markers, pts=polyline_pts, tap_handler=on_map_tap,
        )
        origin_btn.disabled = False
        page.update()

    async def do_pay():
        token = auth_store.token
        if not token:
            show_snackbar(page, "Inicia sesion primero")
            return
        if not coords["origin"] or not coords["dest"]:
            show_snackbar(page, "Calcula una ruta primero")
            return
        status_text.value = "Procesando pago..."
        page.update()
        success = await planner_store.plan_trip(
            token,
            originLat=coords["origin"][0],
            originLon=coords["origin"][1],
            destLat=coords["dest"][0],
            destLon=coords["dest"][1],
            itinerary=current_itinerary,
        )
        if success:
            await wallet_store.fetch_balance(token)
            show_snackbar(page, "Viaje pagado con exito!", bgcolor=ft.Colors.GREEN)
            status_text.value = ""
        else:
            show_snackbar(page, "Error al pagar viaje", bgcolor=ft.Colors.RED_500)
            status_text.value = ""
        page.update()

    location_btn = ft.ElevatedButton("Mi Ubicacion", width=300, bgcolor=ft.Colors.GREY_600, color=ft.Colors.WHITE)
    location_btn.on_click = lambda e: page.run_task(do_my_location)

    origin_btn = ft.ElevatedButton("Calcular Ruta", width=300, bgcolor=ft.Colors.BLUE_900, color=ft.Colors.WHITE)
    origin_btn.on_click = lambda e: page.run_task(do_calculate)

    pay_btn = ft.ElevatedButton("Pagar Viaje (Descontar Saldo)", width=300, bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE)
    pay_btn.on_click = lambda e: page.run_task(do_pay)

    return ft.Column(
        [
            ft.Text("Planificador de Viajes", size=24, weight=ft.FontWeight.BOLD),
            map_container,
            tap_mode,
            status_text,
            location_btn,
            origin_field,
            dest_field,
            origin_btn,
            result_card,
            pay_btn
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
    )
