from pydantic import BaseModel, Field, ConfigDict, AliasChoices
from enum import Enum


class StatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"


class TypeAlertEnum(str, Enum):
    INCIDENT = "INCIDENT"
    MAINTENANCE = "MAINTENANCE"
    INFO = "INFO"


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class AlertCreate(BaseSchema):
    title: str = Field(validation_alias=AliasChoices("Title", "title"))
    description: str = Field(validation_alias=AliasChoices("Description", "description"))
    typeAlert: TypeAlertEnum = Field(
        default=TypeAlertEnum.INFO,
        validation_alias=AliasChoices("TypeAlert", "typeAlert"),
    )


class AlertStatusUpdate(BaseSchema):
    status: StatusEnum
