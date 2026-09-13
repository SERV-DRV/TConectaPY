from fastapi import APIRouter, Query, Request

from app.middlewares.validate_jwt import validate_jwt
from app.middlewares.verify_internal_secret import verify_internal_secret
from app.middlewares.wallets_validators import WalletInitializeBody, WalletRechargeBody
from app.wallets.controller import get_balance, get_recharge_history, initialize_wallet, recharge_wallet

router = APIRouter()


@router.get("/balance")
async def balance(request: Request):
    await validate_jwt(request)
    user_id = request.state.user["id"]
    result = await get_balance(user_id)
    return result


@router.get("/history")
async def history(
    request: Request,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
):
    await validate_jwt(request)
    user_id = request.state.user["id"]
    result = await get_recharge_history(user_id, page=page, limit=limit)
    return result


@router.post("/initialize")
async def initialize(request: Request, body: WalletInitializeBody):
    await verify_internal_secret(request)
    data = body.model_dump()
    result = await initialize_wallet(
        user_id=data["UserId"],
        courtesy_trips=data.get("CourtesyTrips", 5),
        balance=data.get("Balance", 0.0),
    )
    return result


@router.post("/recharge")
async def recharge(request: Request, body: WalletRechargeBody):
    await verify_internal_secret(request)
    data = body.model_dump()
    result = await recharge_wallet(
        user_id=data["UserId"],
        amount=data["Amount"],
    )
    return result
