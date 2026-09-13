from fastapi import APIRouter, Depends, Query
from app.middlewares.validate_jwt import validate_jwt, require_admin_role
from app.middlewares.buses_validators import BusCreate, BusUpdate, BusStatusUpdate
from app.buses.controller import get_buses, get_bus_by_id, create_bus, update_bus, change_bus_status

router = APIRouter(prefix="/buses", tags=["Buses"])


@router.get("")
async def list_buses(
    status: str = Query(None),
    assignedRoad: str = Query(None),
):
    return await get_buses(status, assignedRoad)


@router.get("/{bus_id}")
async def get_bus(bus_id: str):
    return await get_bus_by_id(bus_id)


@router.post("", status_code=201)
async def add_bus(data: BusCreate):
    return await create_bus(data.model_dump())


@router.put("/{bus_id}")
async def edit_bus(bus_id: str, data: BusUpdate):
    return await update_bus(bus_id, data.model_dump(exclude_unset=True))


@router.patch("/{bus_id}/status")
async def update_bus_status(bus_id: str, data: BusStatusUpdate):
    return await change_bus_status(bus_id, data.status.value)
