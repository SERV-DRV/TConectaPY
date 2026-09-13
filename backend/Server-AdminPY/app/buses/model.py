from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from enum import Enum


class StatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"


class BusModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: Optional[str] = Field(None, alias="_id")
    busNumber: str
    licensePlate: str
    capacity: int
    status: StatusEnum = StatusEnum.ACTIVE
    assignedRoad: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
