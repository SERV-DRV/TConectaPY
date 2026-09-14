from fastapi import APIRouter, Depends

from app.middlewares.validate_jwt import validate_jwt
from app.database_mongo import get_mongo_db
from app.models.user import User

router = APIRouter()


@router.get("/balance")
async def get_balance(user: User = Depends(validate_jwt)):
    mongo_db = get_mongo_db()
    wallet = await mongo_db.wallets.find_one({"_id": str(user.id)})
    if not wallet:
        return {"balance": 0.0, "courtesyTrips": 0, "hasCitizenCard": False}
    return {
        "balance": wallet.get("saldo", 0.0),
        "courtesyTrips": wallet.get("viajesCortesia", 0),
        "hasCitizenCard": wallet.get("hasCitizenCard", False),
    }
