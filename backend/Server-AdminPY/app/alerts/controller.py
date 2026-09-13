from datetime import datetime
from fastapi import HTTPException
from bson import ObjectId
from app.configs.database import get_db


COLLECTION = "alerts"


async def create_alert(data: dict):
    db = get_db()
    data["created_at"] = datetime.utcnow()
    data["status"] = data.get("status", "ACTIVE")
    result = await db[COLLECTION].insert_one(data)
    data["_id"] = str(result.inserted_id)
    return data


async def get_active_alerts():
    db = get_db()
    alerts = await db[COLLECTION].find({"status": "ACTIVE"}).sort("created_at", -1).to_list(1000)
    for a in alerts:
        a["_id"] = str(a["_id"])
    return {"total": len(alerts), "data": alerts}


async def resolve_alert(alert_id: str, status: str):
    db = get_db()
    alert = await db[COLLECTION].find_one_and_update(
        {"_id": ObjectId(alert_id)},
        {"$set": {"status": status}},
        return_document=True,
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    alert["_id"] = str(alert["_id"])
    return alert


async def delete_alert(alert_id: str):
    db = get_db()
    from bson import ObjectId
    result = await db[COLLECTION].delete_one({"_id": ObjectId(alert_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return {"message": "Alerta eliminada"}
