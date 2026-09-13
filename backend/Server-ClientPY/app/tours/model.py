from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, AliasChoices


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class PlanTourBody(BaseSchema):
    user_id: str = Field(
        validation_alias=AliasChoices("user_id", "userId"),
        alias="userId",
    )
    origin_lat: float = Field(
        validation_alias=AliasChoices("origin_lat", "originLat"),
        alias="originLat",
        ge=-90, le=90,
    )
    origin_lon: float = Field(
        validation_alias=AliasChoices("origin_lon", "originLon"),
        alias="originLon",
        ge=-180, le=180,
    )
    dest_lat: float = Field(
        validation_alias=AliasChoices("dest_lat", "destLat"),
        alias="destLat",
        ge=-90, le=90,
    )
    dest_lon: float = Field(
        validation_alias=AliasChoices("dest_lon", "destLon"),
        alias="destLon",
        ge=-180, le=180,
    )
    system_type: str = Field(
        default="TRANSMETRO",
        validation_alias=AliasChoices("system_type", "systemType"),
    )
    distance_meters: float | None = Field(
        default=None,
        validation_alias=AliasChoices("distance_meters", "distanceMeters"),
    )
    origin_name: str = Field(
        default="Origen",
        validation_alias=AliasChoices("origin_name", "originName"),
    )
    dest_name: str = Field(
        default="Destino",
        validation_alias=AliasChoices("dest_name", "destName"),
    )
    itinerary: str = Field(default="")


class TourResponse(BaseSchema):
    tour_id: str = Field(alias="tourId")
    system_type: str = Field(alias="systemType")
    estimated_distance: str = Field(alias="estimatedDistance")
    estimated_time: str = Field(alias="estimatedTime")
    charged_fare: str = Field(alias="chargedFare")
    remaining_balance: str = Field(alias="remainingBalance")
    courtesy_trips_left: int = Field(alias="courtesyTripsLeft")
    itinerary: str
