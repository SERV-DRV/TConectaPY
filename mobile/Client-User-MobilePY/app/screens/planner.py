import flet as ft
import flet.map as fmap
import httpx
from app.stores.auth_store import auth_store
from app.stores.planner_store import planner_store

def PlannerScreen(page: ft.Page):
    origin_field = ft.TextField(label="Origen (ej: Irtra Petapa)", width=300)
    dest_field = ft.TextField(label="Destino (ej: USAC)", width=300)
    
    res_tiempo = ft.Text(size=14, weight=ft.FontWeight.BOLD)
    res_distancia = ft.Text(size=14, color=ft.colors.GREY_700)
    
    result_card = ft.Container(
        content=ft.Column([
            ft.Text("Resumen del Viaje", weight=ft.FontWeight.BOLD),
            res_tiempo,
            res_distancia
        ]),
        visible=False,
        bgcolor=ft.colors.GREEN_50,
        padding=10,
        border_radius=10,
        width=300
    )

    marker_layer = fmap.MarkerLayer(markers=[])
    polyline_layer = fmap.PolylineLayer(polylines=[])

    mapa = fmap.Map(
        expand=True,
        initial_center=fmap.MapLatitudeLongitude(14.62, -90.52),
        initial_zoom=12,
        interaction_configuration=fmap.MapInteractionConfiguration(
            flags=fmap.MapInteractiveFlag.ALL
        ),
        layers=[
            fmap.TileLayer(
                url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            ),
            polyline_layer,
            marker_layer,
        ],
    )

    map_container = ft.Container(
        content=mapa,
        height=350,
        border_radius=10,
        clip_behavior=ft.ClipBehavior.HARD_EDGE
    )

    coords = {"origin": None, "dest": None}

    async def geocode(query):
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"https://nominatim.openstreetmap.org/search?q={query}&countrycodes=gt&format=json&limit=1")
                data = res.json()
                if data:
                    return float(data[0]["lat"]), float(data[0]["lon"])
        except Exception:
            pass
        return None

    async def on_calculate(e):
        origin_btn.disabled = True
        page.update()
        
        orig_c = await geocode(origin_field.value)
        dest_c = await geocode(dest_field.value)
        
        if not orig_c or not dest_c:
            page.snack_bar = ft.SnackBar(ft.Text("No se encontró alguna de las ubicaciones"))
            page.snack_bar.open = True
            origin_btn.disabled = False
            page.update()
            return
            
        coords["origin"] = orig_c
        coords["dest"] = dest_c
        
        marker_layer.markers = [
            fmap.Marker(content=ft.Icon(ft.icons.LOCATION_ON, color="green", size=40), coordinates=fmap.MapLatitudeLongitude(*orig_c)),
            fmap.Marker(content=ft.Icon(ft.icons.LOCATION_ON, color="red", size=40), coordinates=fmap.MapLatitudeLongitude(*dest_c))
        ]

        try:
            async with httpx.AsyncClient() as client:
                url = f"https://router.project-osrm.org/route/v1/driving/{orig_c[1]},{orig_c[0]};{dest_c[1]},{dest_c[0]}?geometries=geojson"
                res = await client.get(url)
                route_data = res.json()
                
                if route_data.get("routes"):
                    route = route_data["routes"][0]
                    puntos = [fmap.MapLatitudeLongitude(p[1], p[0]) for p in route["geometry"]["coordinates"]]
                    
                    polyline_layer.polylines = [
                        fmap.Polyline(coordinates=puntos, color=ft.colors.BLUE_700, stroke_width=4)
                    ]
                    
                    dist_km = route["distance"] / 1000
                    mins = round(route["duration"] / 60)
                    res_tiempo.value = f"Tiempo estimado: {mins} min"
                    res_distancia.value = f"Distancia: {dist_km:.2f} km"
                    result_card.visible = True
                    
                    mapa.initial_center = fmap.MapLatitudeLongitude((orig_c[0]+dest_c[0])/2, (orig_c[1]+dest_c[1])/2)
                    mapa.initial_zoom = 13
        except Exception as ex:
            print("Error ruta:", ex)
            
        origin_btn.disabled = False
        page.update()

    async def on_pay(e):
        token = auth_store.token
        if token and coords["origin"] and coords["dest"]:
            await planner_store.plan_trip(
                token, 
                originLat=coords["origin"][0], 
                originLon=coords["origin"][1], 
                destLat=coords["dest"][0], 
                destLon=coords["dest"][1]
            )
            page.snack_bar = ft.SnackBar(ft.Text("Viaje pagado con éxito!", color=ft.colors.WHITE), bgcolor=ft.colors.GREEN)
            page.snack_bar.open = True
            page.update()

    origin_btn = ft.ElevatedButton("Calcular Ruta", on_click=on_calculate, width=300, bgcolor=ft.colors.BLUE_900, color=ft.colors.WHITE)
    pay_btn = ft.ElevatedButton("Pagar Viaje (Descontar Saldo)", on_click=on_pay, width=300, bgcolor=ft.colors.GREEN_600, color=ft.colors.WHITE)

    return ft.Column(
        [
            ft.Text("Planificador de Viajes", size=24, weight=ft.FontWeight.BOLD),
            map_container,
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
