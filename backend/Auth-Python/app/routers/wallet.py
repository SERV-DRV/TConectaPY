from fastapi import APIRouter, Depends, Query, HTTPException

from app.middlewares.validate_jwt import validate_jwt
from app.models.user import User
from app.services.invoice_service import get_user_invoices, get_invoice_by_id

router = APIRouter()


@router.get("/balance")
async def get_balance(user: User = Depends(validate_jwt)):
    from app.database_mongo import get_mongo_db
    mongo_db = get_mongo_db()
    wallet = await mongo_db.wallets.find_one({"_id": str(user.id)})
    if not wallet:
        return {"balance": 0.0, "courtesyTrips": 0, "hasCitizenCard": False}
    return {
        "balance": wallet.get("saldo", 0.0),
        "courtesyTrips": wallet.get("viajesCortesia", 0),
        "hasCitizenCard": wallet.get("hasCitizenCard", False),
    }


@router.get("/invoices")
async def list_invoices(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(validate_jwt),
):
    result = await get_user_invoices(user.id, page, limit)
    return result


@router.get("/invoice/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    user: User = Depends(validate_jwt),
):
    invoice = await get_invoice_by_id(invoice_id, user.id)
    if not invoice:
        raise HTTPException(404, "Factura no encontrada")
    return invoice
