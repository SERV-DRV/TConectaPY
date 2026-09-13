from fastapi import APIRouter, Request

from app.middlewares.validate_jwt import validate_jwt
from app.middlewares.tours_validators import PlanTourBody
from app.tours.controller import get_history, plan_tour

router = APIRouter()


@router.get("/history")
async def history(request: Request):
    await validate_jwt(request)
    user_id = request.state.user["id"]
    tours = await get_history(user_id)
    return tours


@router.post("/plan")
async def plan(request: Request, body: PlanTourBody):
    await validate_jwt(request)
    user_id = request.state.user["id"]
    data = body.model_dump(by_alias=True)
    data["userId"] = user_id
    result = await plan_tour(user_id, data)
    return result
