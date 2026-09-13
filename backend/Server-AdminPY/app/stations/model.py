from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from enum import Enum


class StatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    CLOSED = "CLOSED"


class TypeStationEnum(str, Enum):
    CENTRALES = "CENTRALES"
    CARRIL_LATERAL = "CARRIL LATERAL"
    TRASBORDO = "TRASBORDO"
    TERMINALES = "TERMINALES"


class StationModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: Optional[str] = Field(None, alias="_id")
    name: str
    stationCode: str
    typeStation: TypeStationEnum = TypeStationEnum.CENTRALES
    status: StatusEnum = StatusEnum.ACTIVE
    location: dict
    created_at: datetime = Field(default_factory=datetime.utcnow)
    isActive: bool = True
