from fastapi import APIRouter, Request

from app.middlewares.validate_jwt import validate_jwt
from app.middlewares.profiles_validators import ProfileUpdate
from app.profiles.controller import get_profile, update_profile

router = APIRouter()


@router.get("/me")
async def get_me(request: Request):
    await validate_jwt(request)
    user_id = request.state.user["id"]
    profile = await get_profile(user_id)
    return profile


@router.put("/me")
async def update_me(request: Request, body: ProfileUpdate):
    await validate_jwt(request)
    user_id = request.state.user["id"]
    data = body.model_dump(exclude_unset=True)
    profile = await update_profile(user_id, data)
    return profile
