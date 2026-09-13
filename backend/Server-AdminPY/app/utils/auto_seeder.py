import json
import os
import random
import string
from datetime import datetime, timedelta
from app.configs.database import get_db


def generate_plate() -> str:
    letters = string.ascii_uppercase
    nums = str(random.randint(1000, 9999))
    end = "".join(random.choice(letters) for _ in range(3))
    return f"U{nums}{end}"


def get_line_color(line_name: str) -> str:
    name = line_name.lower()
    if "linea 1" in name and "12" not in name and "13" not in name and "18" not in name:
        return "#6A1B9A"
    if "linea 2" in name:
        return "#AB47BC"
    if "linea 5" in name:
        return "#1565C0"
    if "linea 6" in name or "poligono 6" in name:
        return "#FBC02D"
    if "linea 7" in name:
        return "#757575"
    if "linea 12" in name:
        return "#E65100"
    if "linea 13" in name:
        return "#4CAF50"
    if "linea 18" in name:
        return "#00ACC1"
    return "#3388ff"


def random_suffix() -> str:
    return "".join(random.choices(string.ascii_uppercase, k=4))


SEED_ALERTS = [
    {"title": "Retraso Linea 1", "description": "Servicio con retrasos de 15-20 minutos por congestion en zona 1.", "typeAlert": "INCIDENT"},
    {"title": "Mantenimiento Estacion Plaza Mayor", "description": "La estacion Plaza Mayor estara en mantenimiento hasta el viernes.", "typeAlert": "MAINTENANCE"},
    {"title": "Servicio Normal Linea 5", "description": "El servicio de la Linea 5 opera con normalidad.", "typeAlert": "INFO"},
    {"title": "Accidente Via Alterna", "description": "Accidente en la Via Alterna afecta servicio de Linea 7. Se usan rutas alternas.", "typeAlert": "INCIDENT"},
    {"title": "Nueva Parada Zona 10", "description": "Se habilita nueva parada en la Zona 10 de la Linea 12.", "typeAlert": "INFO"},
    {"title": "Cierre Calle Principal", "description": "Cierre temporal de la Calle Principal por evento cultural. Lineas 1 y 2 redirigidas.", "typeAlert": "MAINTENANCE"},
    {"title": "Baja Flota Linea 2", "description": "Dos unidades de la Linea 2 fuera de servicio por mantenimiento preventivo.", "typeAlert": "MAINTENANCE"},
    {"title": "Incidente Seguridad Zona 7", "description": "Reporte de incidente menor en la Zona 7. Patrullas en el area.", "typeAlert": "INCIDENT"},
    {"title": "Horario Extendido Feria", "description": "Servicio extendido hasta medianoche por Feria de Jocotenango en Lineas 1 y 6.", "typeAlert": "INFO"},
    {"title": "Falla Semaforo Rotonda", "description": "Falla en semaforo de la Rotonda Universidad. Transito con precaucion en Linea 5.", "typeAlert": "INCIDENT"},
]


def parse_geojson() -> tuple:
    geojson_path = os.path.join(os.path.dirname(__file__), "..", "data", "transmetro.geojson")
    if not os.path.exists(geojson_path):
        raise FileNotFoundError(f"No se encontro el archivo GeoJSON en: {geojson_path}")

    with open(geojson_path, "r", encoding="utf-8") as f:
        parsed = json.load(f)

    stations = []
    roads = []
    seen_station_names = set()
    seen_road_names = set()
    seen_route_codes = set()

    for feature in parsed["features"]:
        geom_type = feature["geometry"]["type"]
        props = feature.get("properties", {})

        if geom_type == "Point":
            coords = feature["geometry"]["coordinates"]
            if len(coords) > 2:
                coords = [coords[0], coords[1]]

            st_name = props.get("name", "Estacion Desconocida")
            if st_name in seen_station_names:
                st_name = f"{st_name} - {random_suffix()}"
            seen_station_names.add(st_name)

            stations.append({
                "name": st_name,
                "stationCode": f"EST-{random_suffix()}{random.randint(10,99)}",
                "typeStation": "CENTRALES",
                "location": {
                    "type": "Point",
                    "coordinates": coords,
                },
            })

        elif geom_type in ("LineString", "Polygon", "MultiLineString"):
            coords = feature["geometry"]["coordinates"]
            if geom_type == "Polygon":
                coords = coords[0]
            elif geom_type == "MultiLineString":
                coords = coords[0]

            coords = [c[:2] if len(c) > 2 else c for c in coords]

            route_code = f"L{random.randint(0, 99)}"
            if props.get("name"):
                import re
                match = re.search(r"Linea\s*(\d+)", props["name"], re.IGNORECASE)
                if match:
                    route_code = f"L{match.group(1)}"

            rd_name = props.get("name", "Ruta Desconocida")
            if rd_name in seen_road_names:
                rd_name = f"{rd_name} - {random_suffix()}"
            seen_road_names.add(rd_name)

            final_route_code = route_code
            if final_route_code in seen_route_codes:
                final_route_code = f"{final_route_code}-{random_suffix()}"
            seen_route_codes.add(final_route_code)

            road_color = get_line_color(props.get("name", ""))

            roads.append({
                "name": rd_name,
                "routeCode": final_route_code,
                "typeRoad": "CENTRALES",
                "status": "ACTIVE",
                "color": road_color,
                "path": {
                    "type": "LineString",
                    "coordinates": coords,
                },
            })

    return stations[:20], roads[:10]


async def seed_transmetro_data():
    db = get_db()

    station_count = await db["stations"].count_documents({})
    road_count = await db["roads"].count_documents({})
    alert_count = await db["alerts"].count_documents({})

    if station_count > 0 or road_count > 0:
        print("[SEED] Las colecciones ya contienen datos. Saltando siembra.")
        return

    print("\n--- Iniciando Auto-Seeder de Transmetro (GeoJSON) ---\n")
    print("[SEED] Limpiando colecciones...")
    await db["buses"].delete_many({})
    await db["alerts"].delete_many({})

    print("[SEED] Leyendo transmetro.geojson...")
    stations, roads = parse_geojson()
    print(f"[SEED] Encontradas: {len(stations)} estaciones y {len(roads)} rutas")

    print("[SEED] Insertando estaciones...")
    station_ids = []
    if stations:
        res = await db["stations"].insert_many(stations)
        station_ids = res.inserted_ids
    print(f"[SEED] {len(stations)} estaciones insertadas.")

    print("[SEED] Insertando rutas y asignando buses...")
    import random
    
    # Aseguramos tener exactamente 10 rutas (limitar si hay mas, o iterar hasta 10)
    for i, road_data in enumerate(roads[:10]):
        road_data["created_at"] = datetime.utcnow()
        road_data["isActive"] = True
        
        # Asignar exactamente 2 estaciones por ruta (secuencialmente para que las 20 esten en las 10 rutas)
        # Ruta 0: st 0, 1 | Ruta 1: st 2, 3 | etc...
        start_idx = i * 2
        assigned_station_ids = station_ids[start_idx:start_idx+2] if start_idx+2 <= len(station_ids) else []
        road_data["stations"] = assigned_station_ids
        
        result = await db["roads"].insert_one(road_data)
        road_id = result.inserted_id
        print(f"   - Ruta creada: {road_data['name']} (Code: {road_data['routeCode']}) con {len(assigned_station_ids)} estaciones")

        # 1 Bus por ruta
        bus_num = f"TM-{road_data['routeCode'].replace('L', '')}01-{random.randint(10, 99)}"
        bus_data = {
            "busNumber": bus_num,
            "licensePlate": generate_plate(),
            "capacity": random.randint(80, 120),
            "assignedRoad": road_id,
            "status": "ACTIVE",
            "created_at": datetime.utcnow(),
        }
        await db["buses"].insert_one(bus_data)
        print(f"      Bus asignado: {bus_num} (Placa: {bus_data['licensePlate']})")

    print("[SEED] Insertando alertas...")
    now = datetime.utcnow()
    alerts_to_insert = []
    for i, alert in enumerate(SEED_ALERTS):
        created = now - timedelta(hours=random.randint(1, 72))
        status = "ACTIVE" if i < 7 else "RESOLVED"
        alerts_to_insert.append({
            **alert,
            "status": status,
            "created_at": created,
        })
    await db["alerts"].insert_many(alerts_to_insert)
    print(f"[SEED] {len(alerts_to_insert)} alertas insertadas.")

    total_buses = await db["buses"].count_documents({})
    print(f"\n[SEED] Resumen: {len(stations)} estaciones, {len(roads)} rutas, {total_buses} buses, {len(alerts_to_insert)} alertas")
    print("[SEED] Auto-Seeder finalizado con exito!\n")
