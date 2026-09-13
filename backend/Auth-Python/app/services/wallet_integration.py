from datetime import datetime, timezone

from app.database_mongo import get_mongo_db


async def initialize_wallet(user_id: str) -> bool:
    try:
        mongo_db = get_mongo_db()
        now = datetime.now(timezone.utc)

        await mongo_db.wallets.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "saldo": 20.0,
                    "viajesCortesia": 5,
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
        return True
    except Exception as e:
        print(f"[TransmetroAuth] WalletIntegration | initializeWallet error: {e}")
        return False


async def add_funds(user_id: str, amount: float) -> bool:
    try:
        mongo_db = get_mongo_db()
        now = datetime.now(timezone.utc)

        wallet = await mongo_db.wallets.find_one({"_id": user_id})
        if not wallet:
            return False

        new_balance = round(wallet.get("saldo", 0.0) + amount, 2)

        await mongo_db.wallets.update_one(
            {"_id": user_id},
            {
                "$set": {"saldo": new_balance, "updated_at": now},
                "$push": {"historialRecargas": {"monto": amount, "fecha": now}},
            },
        )
        return True
    except Exception as e:
        print(f"[TransmetroAuth] WalletIntegration | addFunds error: {e}")
        return False


async def has_citizen_card(user_id: str) -> bool:
    try:
        mongo_db = get_mongo_db()
        wallet = await mongo_db.wallets.find_one({"_id": user_id})
        if wallet:
            return wallet.get("hasCitizenCard", False)
    except Exception as e:
        print(f"[TransmetroAuth] WalletIntegration | hasCitizenCard error: {e}")
    return False
