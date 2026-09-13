from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from app.configs.database import get_db
from app.utils.geo_utils import haversine_distance, estimate_time_minutes

FARES = {
    "TRANSMETRO": 1.00,
    "TUBUS": 1.00,
    "TRANSURBANO": 2.00,
}


def _serialize_tour(doc: dict) -> dict:
    tour_id = str(doc.get("_id", ""))
    created = doc.get("created_at")
    created_iso = created.isoformat() if isinstance(created, datetime) else str(created) if created else ""
    return {
        "tourId": tour_id,
        "systemType": doc.get("systemType", ""),
        "originLat": doc.get("origen", {}).get("lat"),
        "originLon": doc.get("origen", {}).get("lon"),
        "destLat": doc.get("destino", {}).get("lat"),
        "destLon": doc.get("destino", {}).get("lon"),
        "distanceMeters": doc.get("distanciaMetros"),
        "estimatedTimeMinutes": doc.get("tiempoEstimadoMinutos"),
        "chargedFare": doc.get("tarifaCobrada"),
        "originName": doc.get("originName", "Origen"),
        "destName": doc.get("destName", "Destino"),
        "itinerary": doc.get("itinerary", ""),
        "status": doc.get("status", True),
        "createdAt": created_iso,
    }


async def get_history(user_id: str) -> list[dict]:
    db = get_db()
    cursor = db.tours.find({"userId": user_id, "isActive": True}).sort("created_at", -1)
    tours = await cursor.to_list(length=100)
    return [_serialize_tour(t) for t in tours]


async def plan_tour(user_id: str, body: dict) -> dict:
    db = get_db()

    wallet = await db.wallets.find_one({"_id": user_id})
    if not wallet:
        raise HTTPException(status_code=404, detail="Billetera no encontrada. Inicializa primero.")
    if not wallet.get("isActive", True):
        raise HTTPException(status_code=403, detail="Billetera inactiva")

    system_type = body.get("systemType", "TRANSMETRO")
    fare = FARES.get(system_type, 1.00)

    courtesy_left = wallet.get("viajesCortesia", 0)
    used_courtesy = False
    new_courtesy = courtesy_left
    new_balance = wallet.get("saldo", 0.0)

    if courtesy_left > 0:
        new_courtesy = courtesy_left - 1
        used_courtesy = True
    else:
        if new_balance < fare:
            raise HTTPException(status_code=402, detail="Saldo insuficiente")
        new_balance = round(new_balance - fare, 2)

    origin_lat = body["originLat"]
    origin_lon = body["originLon"]
    dest_lat = body["destLat"]
    dest_lon = body["destLon"]

    distance = body.get("distanceMeters")
    if not distance:
        distance = haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon)

    time_est = body.get("estimatedTimeMinutes")
    if not time_est:
        time_est = estimate_time_minutes(distance)

    tour_id = str(uuid4())
    now = datetime.now(timezone.utc)
    tour_doc = {
        "_id": tour_id,
        "userId": user_id,
        "origen": {"lat": origin_lat, "lon": origin_lon},
        "destino": {"lat": dest_lat, "lon": dest_lon},
        "distanciaMetros": round(distance, 2),
        "tiempoEstimadoMinutos": time_est,
        "tarifaCobrada": 0.0 if used_courtesy else fare,
        "systemType": system_type,
        "itinerary": body.get("itinerary", ""),
        "originName": body.get("originName", "Origen"),
        "destName": body.get("destName", "Destino"),
        "status": True,
        "isActive": True,
        "created_at": now,
    }
    await db.tours.insert_one(tour_doc)

    await db.wallets.update_one(
        {"_id": user_id},
        {"$set": {"saldo": new_balance, "viajesCortesia": new_courtesy, "updated_at": now}},
    )

    return {
        "tourId": tour_id,
        "systemType": system_type,
        "estimatedDistance": f"{round(distance, 2)} m",
        "estimatedTime": f"{time_est} min",
        "chargedFare": f"Q{0.0 if used_courtesy else fare:.2f}",
        "remainingBalance": f"Q{new_balance:.2f}",
        "courtesyTripsLeft": new_courtesy,
        "itinerary": body.get("itinerary", ""),
    }
