from pydantic import BaseModel, Field, ConfigDict, AliasChoices
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


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class RoadCreate(BaseSchema):
    name: str = Field(min_length=2, max_length=100, validation_alias=AliasChoices("Name", "name"))
    routeCode: str = Field(validation_alias=AliasChoices("RouteCode", "routeCode"))
    typeRoad: TypeRoadEnum = Field(
        default=TypeRoadEnum.CENTRALES,
        validation_alias=AliasChoices("TypeRoad", "typeRoad"),
    )
    color: Optional[str] = Field(default="#3388ff", validation_alias=AliasChoices("Color", "color"))
    stations: Optional[list[str]] = Field(default=[], validation_alias=AliasChoices("Stations", "stations"))
    coordinates: list[list[float]] = Field(min_length=2, validation_alias=AliasChoices("Coordinates", "coordinates"))


class RoadUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    routeCode: Optional[str] = None
    typeRoad: Optional[TypeRoadEnum] = None
    color: Optional[str] = None
    stations: Optional[list[str]] = None
    coordinates: Optional[list[list[float]]] = Field(None, min_length=2)


class RoadStatusUpdate(BaseSchema):
    status: StatusEnum
