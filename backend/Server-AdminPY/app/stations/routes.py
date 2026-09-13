from fastapi import APIRouter, Depends, Query
from app.middlewares.validate_jwt import validate_jwt, require_admin_role
from app.middlewares.stations_validators import StationCreate, StationUpdate, StationStatusUpdate
from app.stations.controller import (
    get_all_stations, get_stations, get_station_by_id,
    create_station, update_station, change_station_status,
)

router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get("")
async def list_stations(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: str = Query(None),
    typeStation: str = Query(None),
    _=Depends(validate_jwt),
):
    return await get_stations(page, limit, status, typeStation)


@router.get("/all")
async def list_all_stations(
    status: str = Query(None),
    typeStation: str = Query(None),
    _=Depends(validate_jwt),
):
    return await get_all_stations(status, typeStation)


@router.get("/{station_id}")
async def get_station(station_id: str, _=Depends(validate_jwt)):
    return await get_station_by_id(station_id)


@router.post("", status_code=201)
async def add_station(data: StationCreate, _=Depends(require_admin_role)):
    return await create_station(data.model_dump())


@router.put("/{station_id}")
async def edit_station(station_id: str, data: StationUpdate, _=Depends(require_admin_role)):
    return await update_station(station_id, data.model_dump())


@router.put("/{station_id}/status")
async def update_station_status(station_id: str, data: StationStatusUpdate, _=Depends(require_admin_role)):
    return await change_station_status(station_id, data.status.value)
