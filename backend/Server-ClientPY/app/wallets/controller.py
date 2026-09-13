from datetime import datetime, timezone

from fastapi import HTTPException

from app.configs.database import get_db


async def get_balance(user_id: str) -> dict:
    db = get_db()
    wallet = await db.wallets.find_one({"_id": user_id})

    if not wallet:
        now = datetime.now(timezone.utc)
        new_wallet = {
            "_id": user_id,
            "saldo": 0.0,
            "viajesCortesia": 0,
            "hasCitizenCard": False,
            "historialRecargas": [],
            "status": True,
            "isActive": True,
            "created_at": now,
            "updated_at": now,
        }
        await db.wallets.insert_one(new_wallet)
        return {"balance": 0.0, "courtesyTrips": 0, "hasCitizenCard": False}

    return {
        "balance": wallet.get("saldo", 0.0),
        "courtesyTrips": wallet.get("viajesCortesia", 0),
        "hasCitizenCard": wallet.get("hasCitizenCard", False),
    }


async def get_recharge_history(user_id: str, page: int = 1, limit: int = 10) -> dict:
    db = get_db()
    wallet = await db.wallets.find_one({"_id": user_id})

    if not wallet:
        return {"history": [], "total": 0, "page": page, "limit": limit}

    history = wallet.get("historialRecargas", [])
    history_sorted = sorted(history, key=lambda x: x.get("fecha", ""), reverse=True)

    limit = min(limit, 100)
    start = (page - 1) * limit
    end = start + limit
    paginated = history_sorted[start:end]

    formatted = []
    for item in paginated:
        fecha = item.get("fecha")
        fecha_iso = fecha.isoformat() if isinstance(fecha, datetime) else str(fecha) if fecha else ""
        formatted.append({"amount": item.get("monto", 0.0), "date": fecha_iso})

    return {"history": formatted, "total": len(history), "page": page, "limit": limit}


async def initialize_wallet(user_id: str, courtesy_trips: int = 5, balance: float = 0.0) -> dict:
    db = get_db()
    now = datetime.now(timezone.utc)

    await db.wallets.update_one(
        {"_id": user_id},
        {
            "$set": {
                "saldo": balance,
                "viajesCortesia": courtesy_trips,
                "hasCitizenCard": True,
                "status": True,
                "isActive": True,
                "updated_at": now,
            },
            "$setOnInsert": {
                "_id": user_id,
                "historialRecargas": [],
                "created_at": now,
            },
        },
        upsert=True,
    )

    wallet = await db.wallets.find_one({"_id": user_id})
    return {
        "userId": user_id,
        "balance": wallet.get("saldo", 0.0),
        "courtesyTrips": wallet.get("viajesCortesia", 0),
        "hasCitizenCard": wallet.get("hasCitizenCard", True),
    }


async def recharge_wallet(user_id: str, amount: float) -> dict:
    db = get_db()

    if amount <= 0:
        raise HTTPException(status_code=400, detail="El monto debe ser mayor a 0")

    wallet = await db.wallets.find_one({"_id": user_id})
    if not wallet:
        raise HTTPException(status_code=404, detail="Billetera no encontrada")

    now = datetime.now(timezone.utc)
    new_balance = round(wallet.get("saldo", 0.0) + amount, 2)

    await db.wallets.update_one(
        {"_id": user_id},
        {
            "$set": {"saldo": new_balance, "updated_at": now},
            "$push": {"historialRecargas": {"monto": amount, "fecha": now}},
        },
    )

    return {
        "userId": user_id,
        "recharged": amount,
        "newBalance": new_balance,
    }
