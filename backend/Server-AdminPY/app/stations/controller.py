from datetime import datetime
from fastapi import HTTPException
from app.configs.database import get_db


COLLECTION = "stations"


async def get_all_stations(status: str = None, type_station: str = None):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if type_station:
        query["typeStation"] = type_station
    stations = await db[COLLECTION].find(query).sort("created_at", -1).to_list(1000)
    for s in stations:
        s["_id"] = str(s["_id"])
    return {"totalRecords": len(stations), "data": stations}


async def get_stations(page: int = 1, limit: int = 10, status: str = None, type_station: str = None):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if type_station:
        query["typeStation"] = type_station
    total = await db[COLLECTION].count_documents(query)
    skip = (page - 1) * limit
    stations = await db[COLLECTION].find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    for s in stations:
        s["_id"] = str(s["_id"])
    return {
        "totalRecords": total,
        "page": page,
        "limit": limit,
        "totalPages": (total + limit - 1) // limit,
        "data": stations,
    }


async def get_station_by_id(station_id: str):
    db = get_db()
    from bson import ObjectId
    station = None
    try:
        station = await db[COLLECTION].find_one({"_id": ObjectId(station_id)})
    except Exception:
        pass
    if not station:
        station = await db[COLLECTION].find_one({"stationCode": {"$regex": f"^{station_id}$", "$options": "i"}})
    if not station:
        raise HTTPException(status_code=404, detail="Estacion no encontrada")
    station["_id"] = str(station["_id"])
    return station


async def create_station(data: dict):
    db = get_db()
    existing = await db[COLLECTION].find_one({"stationCode": data["stationCode"].upper()})
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una estacion con ese codigo")
    data["stationCode"] = data["stationCode"].upper()
    data["location"] = {
        "type": "Point",
        "coordinates": data.pop("coordinates"),
    }
    data["created_at"] = datetime.utcnow()
    data["isActive"] = True
    data["status"] = data.get("status", "ACTIVE")
    result = await db[COLLECTION].insert_one(data)
    data["_id"] = str(result.inserted_id)
    return data


async def update_station(station_id: str, data: dict):
    db = get_db()
    from bson import ObjectId
    update_data = {k: v for k, v in data.items() if v is not None}
    if "coordinates" in update_data:
        update_data["location"] = {
            "type": "Point",
            "coordinates": update_data.pop("coordinates"),
        }
    if "stationCode" in update_data:
        update_data["stationCode"] = update_data["stationCode"].upper()
    station = None
    try:
        station = await db[COLLECTION].find_one_and_update(
            {"_id": ObjectId(station_id)}, {"$set": update_data}, return_document=True
        )
    except Exception:
        pass
    if not station:
        station = await db[COLLECTION].find_one_and_update(
            {"stationCode": {"$regex": f"^{station_id}$", "$options": "i"}},
            {"$set": update_data},
            return_document=True,
        )
    if not station:
        raise HTTPException(status_code=404, detail="Estacion no encontrada")
    station["_id"] = str(station["_id"])
    return station


async def change_station_status(station_id: str, status: str):
    db = get_db()
    from bson import ObjectId
    station = None
    try:
        station = await db[COLLECTION].find_one_and_update(
            {"_id": ObjectId(station_id)},
            {"$set": {"status": status, "isActive": status == "ACTIVE"}},
            return_document=True,
        )
    except Exception:
        pass
    if not station:
        station = await db[COLLECTION].find_one_and_update(
            {"stationCode": {"$regex": f"^{station_id}$", "$options": "i"}},
            {"$set": {"status": status, "isActive": status == "ACTIVE"}},
            return_document=True,
        )
    if not station:
        raise HTTPException(status_code=404, detail="Estacion no encontrada")

    alert_type = "INFO"
    alert_title = f"Estado de estacion {station['name']} actualizado a {status}"
    if status == "MAINTENANCE":
        alert_type = "MAINTENANCE"
        alert_title = f"Estacion {station['name']} en mantenimiento"
    elif status in ("CLOSED", "INACTIVE"):
        alert_type = "INCIDENT"
        alert_title = f"Estacion {station['name']} cerrada/inactiva"

    await db["alerts"].insert_one({
        "title": alert_title,
        "description": f"El estado de la estacion {station['name']} cambio a {status}",
        "typeAlert": alert_type,
        "status": "ACTIVE",
        "created_at": datetime.utcnow(),
    })

    station["_id"] = str(station["_id"])
    return station
