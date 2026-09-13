from datetime import datetime
from fastapi import HTTPException
from app.configs.database import get_db


COLLECTION = "buses"


async def get_buses(status: str = None, assigned_road: str = None):
    db = get_db()
    query = {}
    if status:
        query["status"] = status
    if assigned_road:
        query["assignedRoad"] = assigned_road
    buses = await db[COLLECTION].find(query).sort("created_at", -1).to_list(1000)
    for b in buses:
        b["_id"] = str(b["_id"])
        if b.get("assignedRoad"):
            b["assignedRoad"] = str(b["assignedRoad"])
    return {"data": buses}


async def get_bus_by_id(bus_id: str):
    db = get_db()
    from bson import ObjectId
    bus = None
    try:
        bus = await db[COLLECTION].find_one({"_id": ObjectId(bus_id)})
    except Exception:
        pass
    if not bus:
        bus = await db[COLLECTION].find_one({"busNumber": {"$regex": f"^{bus_id}$", "$options": "i"}})
    if not bus:
        raise HTTPException(status_code=404, detail="Bus no encontrado")
    bus["_id"] = str(bus["_id"])
    if bus.get("assignedRoad"):
        bus["assignedRoad"] = str(bus["assignedRoad"])
    return bus


async def create_bus(data: dict):
    db = get_db()
    existing = await db[COLLECTION].find_one({"busNumber": data["busNumber"]})
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un bus con ese numero")
    existing_plate = await db[COLLECTION].find_one({"licensePlate": data["licensePlate"].upper()})
    if existing_plate:
        raise HTTPException(status_code=400, detail="Ya existe un bus con esa placa")
    data["licensePlate"] = data["licensePlate"].upper()
    if data.get("assignedRoad"):
        from bson import ObjectId
        road = await db["roads"].find_one({"_id": ObjectId(data["assignedRoad"])})
        if not road:
            raise HTTPException(status_code=400, detail="Ruta asignada no encontrada")
        bus_on_road = await db[COLLECTION].find_one({"assignedRoad": ObjectId(data["assignedRoad"])})
        if bus_on_road:
            raise HTTPException(status_code=400, detail="Ya hay un bus asignado a esa ruta")
        data["assignedRoad"] = ObjectId(data["assignedRoad"])
    data["created_at"] = datetime.utcnow()
    data["status"] = data.get("status", "ACTIVE")
    result = await db[COLLECTION].insert_one(data)
    data["_id"] = str(result.inserted_id)

    await db["alerts"].insert_one({
        "title": "Nuevo Bus Registrado",
        "description": f"Se registro el bus {data['busNumber']} con placa {data['licensePlate']}",
        "typeAlert": "INFO",
        "status": "ACTIVE",
        "created_at": datetime.utcnow(),
    })
    return data


async def update_bus(bus_id: str, data: dict):
    db = get_db()
    from bson import ObjectId
    update_data = {k: v for k, v in data.items() if v is not None}
    if "licensePlate" in update_data:
        update_data["licensePlate"] = update_data["licensePlate"].upper()
    if "assignedRoad" in update_data:
        if update_data["assignedRoad"] in ("", None):
            update_data.pop("assignedRoad", None)
            unset_data = {"$unset": {"assignedRoad": ""}}
        else:
            update_data["assignedRoad"] = ObjectId(update_data["assignedRoad"])
            unset_data = None
    else:
        unset_data = None
    bus = None
    try:
        set_op = {"$set": update_data} if update_data else {}
        if unset_data:
            set_op = {**set_op, **unset_data}
        bus = await db[COLLECTION].find_one_and_update(
            {"_id": ObjectId(bus_id)}, set_op, return_document=True
        )
    except Exception:
        pass
    if not bus:
        bus = await db[COLLECTION].find_one_and_update(
            {"busNumber": {"$regex": f"^{bus_id}$", "$options": "i"}},
            {"$set": update_data},
            return_document=True,
        )
    if not bus:
        raise HTTPException(status_code=404, detail="Bus no encontrado")

    await db["alerts"].insert_one({
        "title": "Bus Actualizado",
        "description": f"Se actualizo el bus {bus['busNumber']}",
        "typeAlert": "INFO",
        "status": "ACTIVE",
        "created_at": datetime.utcnow(),
    })
    bus["_id"] = str(bus["_id"])
    if bus.get("assignedRoad"):
        bus["assignedRoad"] = str(bus["assignedRoad"])
    return bus


async def change_bus_status(bus_id: str, status: str):
    db = get_db()
    from bson import ObjectId
    bus = None
    try:
        bus = await db[COLLECTION].find_one_and_update(
            {"_id": ObjectId(bus_id)},
            {"$set": {"status": status}},
            return_document=True,
        )
    except Exception:
        pass
    if not bus:
        bus = await db[COLLECTION].find_one_and_update(
            {"busNumber": {"$regex": f"^{bus_id}$", "$options": "i"}},
            {"$set": {"status": status}},
            return_document=True,
        )
    if not bus:
        raise HTTPException(status_code=404, detail="Bus no encontrado")

    alert_type = "INFO"
    alert_title = f"Estado del bus {bus['busNumber']} actualizado a {status}"
    if status == "MAINTENANCE":
        alert_type = "MAINTENANCE"
        alert_title = f"Bus {bus['busNumber']} en mantenimiento"

    await db["alerts"].insert_one({
        "title": alert_title,
        "description": f"El estado del bus {bus['busNumber']} cambio a {status}",
        "typeAlert": alert_type,
        "status": "ACTIVE",
        "created_at": datetime.utcnow(),
    })
    bus["_id"] = str(bus["_id"])
    if bus.get("assignedRoad"):
        bus["assignedRoad"] = str(bus["assignedRoad"])
    return bus
