from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from enum import Enum


class StatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    CLOSED = "CLOSED"


class TypeRoadEnum(str, Enum):
    EXPRESS = "EXPRESS"
    RELEVOS = "RELEVOS"
    CENTRALES = "CENTRALES"


class RoadModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: Optional[str] = Field(None, alias="_id")
    name: str
    routeCode: str
    typeRoad: TypeRoadEnum = TypeRoadEnum.CENTRALES
    color: str = "#3388ff"
    status: StatusEnum = StatusEnum.ACTIVE
    stations: list[str] = []
    path: dict
    created_at: datetime = Field(default_factory=datetime.utcnow)
    isActive: bool = True
