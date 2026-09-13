from fastapi import APIRouter, Depends, Query
from app.middlewares.validate_jwt import validate_jwt, require_admin_role
from app.middlewares.roads_validators import RoadCreate, RoadUpdate, RoadStatusUpdate
from app.roads.controller import (
    get_roads, get_all_roads, get_road_by_id,
    create_road, update_road, change_road_status,
)

router = APIRouter(prefix="/roads", tags=["Roads"])


@router.get("")
async def list_roads(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: str = Query(None),
    typeRoad: str = Query(None),
    _=Depends(validate_jwt),
):
    return await get_roads(page, limit, status, typeRoad)


@router.get("/all")
async def list_all_roads(
    status: str = Query(None),
    typeRoad: str = Query(None),
    _=Depends(validate_jwt),
):
    return await get_all_roads(status, typeRoad)


@router.get("/{road_id}")
async def get_road(road_id: str, _=Depends(validate_jwt)):
    return await get_road_by_id(road_id)


@router.post("", status_code=201)
async def add_road(data: RoadCreate, _=Depends(require_admin_role)):
    return await create_road(data.model_dump())


@router.put("/{road_id}")
async def edit_road(road_id: str, data: RoadUpdate, _=Depends(require_admin_role)):
    return await update_road(road_id, data.model_dump())


@router.put("/{road_id}/status")
async def update_road_status(road_id: str, data: RoadStatusUpdate, _=Depends(require_admin_role)):
    return await change_road_status(road_id, data.status.value)
