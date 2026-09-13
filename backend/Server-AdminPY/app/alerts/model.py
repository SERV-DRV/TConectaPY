from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from enum import Enum


class StatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"


class TypeAlertEnum(str, Enum):
    INCIDENT = "INCIDENT"
    MAINTENANCE = "MAINTENANCE"
    INFO = "INFO"


class AlertModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: Optional[str] = Field(None, alias="_id")
    title: str
    description: str
    typeAlert: TypeAlertEnum = TypeAlertEnum.INFO
    status: StatusEnum = StatusEnum.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
