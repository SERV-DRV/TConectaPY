from datetime import datetime
from fastapi import HTTPException
from app.configs.database import get_db


COLLECTION = "roads"


async def process_stations(stations_array: list) -> list:
    db = get_db()
    from bson import ObjectId
    resolved = []
    for ref in stations_array:
        try:
            ObjectId(ref)
            resolved.append(ref)
        except Exception:
            station = await db["stations"].find_one({"stationCode": {"$regex": f"^{ref}$", "$options": "i"}})
            if station:
                resolved.append(str(station["_id"]))
    return resolved


async def get_roads(page: int = 1, limit: int = 10, status: str = None, type_road: str = None):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if type_road:
        query["typeRoad"] = type_road
    total = await db[COLLECTION].count_documents(query)
    skip = (page - 1) * limit
    roads = await db[COLLECTION].find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    for r in roads:
        r["_id"] = str(r["_id"])
        r["stations"] = [str(s) for s in r.get("stations", [])]
    return {
        "totalRecords": total,
        "page": page,
        "limit": limit,
        "totalPages": (total + limit - 1) // limit,
        "data": roads,
    }


async def get_all_roads(status: str = None, type_road: str = None):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if type_road:
        query["typeRoad"] = type_road
    roads = await db[COLLECTION].find(query).sort("created_at", -1).to_list(1000)
    for r in roads:
        r["_id"] = str(r["_id"])
        r["stations"] = [str(s) for s in r.get("stations", [])]
    return {"summary": {"totalRoads": len(roads)}, "data": roads}


async def get_road_by_id(road_id: str):
    db = get_db()
    from bson import ObjectId
    road = None
    try:
        road = await db[COLLECTION].find_one({"_id": ObjectId(road_id)})
    except Exception:
        pass
    if not road:
        road = await db[COLLECTION].find_one({"routeCode": {"$regex": f"^{road_id}$", "$options": "i"}})
    if not road:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    road["_id"] = str(road["_id"])
    road["stations"] = [str(s) for s in road.get("stations", [])]
    return road


async def create_road(data: dict):
    db = get_db()
    existing = await db[COLLECTION].find_one({"routeCode": data["routeCode"].upper()})
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una ruta con ese codigo")
    data["routeCode"] = data["routeCode"].upper()
    if "stations" in data and data["stations"]:
        data["stations"] = await process_stations(data["stations"])
    data["path"] = {
        "type": "LineString",
        "coordinates": data.pop("coordinates"),
    }
    data["created_at"] = datetime.utcnow()
    data["isActive"] = True
    data["status"] = data.get("status", "ACTIVE")
    data["color"] = data.get("color", "#3388ff")
    result = await db[COLLECTION].insert_one(data)
    data["_id"] = str(result.inserted_id)

    await db["alerts"].insert_one({
        "title": f"Nueva Ruta Creada: {data['name']}",
        "description": f"Se creo la ruta {data['name']} con codigo {data['routeCode']}",
        "typeAlert": "INFO",
        "status": "ACTIVE",
        "created_at": datetime.utcnow(),
    })
    return data


async def update_road(road_id: str, data: dict):
    db = get_db()
    from bson import ObjectId
    update_data = {k: v for k, v in data.items() if v is not None}
    if "coordinates" in update_data:
        update_data["path"] = {
            "type": "LineString",
            "coordinates": update_data.pop("coordinates"),
        }
    if "stations" in update_data and update_data["stations"]:
        update_data["stations"] = await process_stations(update_data["stations"])
    if "routeCode" in update_data:
        update_data["routeCode"] = update_data["routeCode"].upper()
    road = None
    try:
        road = await db[COLLECTION].find_one_and_update(
            {"_id": ObjectId(road_id)}, {"$set": update_data}, return_document=True
        )
    except Exception:
        pass
    if not road:
        road = await db[COLLECTION].find_one_and_update(
            {"routeCode": {"$regex": f"^{road_id}$", "$options": "i"}},
            {"$set": update_data},
            return_document=True,
        )
    if not road:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")

    await db["alerts"].insert_one({
        "title": f"Ruta Actualizada: {road['name']}",
        "description": f"Se actualizo la ruta {road['name']}",
        "typeAlert": "INFO",
        "status": "ACTIVE",
        "created_at": datetime.utcnow(),
    })
    road["_id"] = str(road["_id"])
    road["stations"] = [str(s) for s in road.get("stations", [])]
    return road


async def change_road_status(road_id: str, status: str):
    db = get_db()
    from bson import ObjectId
    road = None
    try:
        road = await db[COLLECTION].find_one_and_update(
            {"_id": ObjectId(road_id)},
            {"$set": {"status": status, "isActive": status == "ACTIVE"}},
            return_document=True,
        )
    except Exception:
        pass
    if not road:
        road = await db[COLLECTION].find_one_and_update(
            {"routeCode": {"$regex": f"^{road_id}$", "$options": "i"}},
            {"$set": {"status": status, "isActive": status == "ACTIVE"}},
            return_document=True,
        )
    if not road:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")

    alert_type = "INFO"
    alert_title = f"Estado de ruta {road['name']} actualizado a {status}"
    if status == "MAINTENANCE":
        alert_type = "MAINTENANCE"
        alert_title = f"Ruta {road['name']} en mantenimiento"
    elif status == "CLOSED":
        alert_type = "INCIDENT"
        alert_title = f"Ruta {road['name']} cerrada"

    await db["alerts"].insert_one({
        "title": alert_title,
        "description": f"El estado de la ruta {road['name']} cambio a {status}",
        "typeAlert": alert_type,
        "status": "ACTIVE",
        "created_at": datetime.utcnow(),
    })
    road["_id"] = str(road["_id"])
    road["stations"] = [str(s) for s in road.get("stations", [])]
    return road
