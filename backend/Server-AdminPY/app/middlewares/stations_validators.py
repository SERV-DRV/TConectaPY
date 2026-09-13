from pydantic import BaseModel, Field, ConfigDict, AliasChoices
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


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class StationCreate(BaseSchema):
    name: str = Field(min_length=2, max_length=100, validation_alias=AliasChoices("Name", "name"))
    stationCode: str = Field(validation_alias=AliasChoices("StationCode", "stationCode"))
    typeStation: TypeStationEnum = Field(
        default=TypeStationEnum.CENTRALES,
        validation_alias=AliasChoices("TypeStation", "typeStation"),
    )
    coordinates: list[float] = Field(min_length=2, max_length=2)


class StationUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    stationCode: Optional[str] = None
    typeStation: Optional[TypeStationEnum] = None
    coordinates: Optional[list[float]] = Field(None, min_length=2, max_length=2)


class StationStatusUpdate(BaseSchema):
    status: StatusEnum
