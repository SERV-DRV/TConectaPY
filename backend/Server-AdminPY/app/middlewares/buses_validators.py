import re
from pydantic import BaseModel, Field, ConfigDict, AliasChoices, field_validator
from typing import Optional
from enum import Enum


class StatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class BusCreate(BaseSchema):
    busNumber: str = Field(validation_alias=AliasChoices("BusNumber", "busNumber"))
    licensePlate: str = Field(validation_alias=AliasChoices("LicensePlate", "licensePlate"))
    capacity: int = Field(ge=10, le=200, validation_alias=AliasChoices("Capacity", "capacity"))
    assignedRoad: Optional[str] = Field(None, validation_alias=AliasChoices("AssignedRoad", "assignedRoad"))

    @field_validator("licensePlate")
    @classmethod
    def validate_license_plate(cls, v):
        if not re.match(r"^[UCP]\d{3,4}[A-Z]{3}$", v.upper()):
            raise ValueError("Placa invalida. Formato: U/C/P + 3-4 digitos + 3 letras")
        return v.upper()


class BusUpdate(BaseSchema):
    busNumber: Optional[str] = None
    licensePlate: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=10, le=200)
    assignedRoad: Optional[str] = None

    @field_validator("licensePlate")
    @classmethod
    def validate_license_plate(cls, v):
        if v is not None and not re.match(r"^[UCP]\d{3,4}[A-Z]{3}$", v.upper()):
            raise ValueError("Placa invalida. Formato: U/C/P + 3-4 digitos + 3 letras")
        return v.upper() if v else v


class BusStatusUpdate(BaseSchema):
    status: StatusEnum
