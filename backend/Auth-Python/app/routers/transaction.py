from fastapi import APIRouter, Depends

from app.middlewares.validate_jwt import validate_jwt
from app.models.user import User
from app.schemas.auth import TransactionRequest, TransactionResponse
from app.services import transaction_service

router = APIRouter()


@router.post("/recharge", response_model=TransactionResponse)
async def recharge(
    body: TransactionRequest,
    user: User = Depends(validate_jwt),
):
    result = await transaction_service.process_payment(
        user.id, body.CardNumber, body.Amount
    )
    return result


@router.post("/purchase-card", response_model=TransactionResponse)
async def purchase_card(
    body: TransactionRequest,
    user: User = Depends(validate_jwt),
):
    result = await transaction_service.purchase_card(
        user.id, body.CardNumber, body.Amount
    )
    return result
