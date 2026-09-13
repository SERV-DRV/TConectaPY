from pydantic import BaseModel, ConfigDict, Field, AliasChoices


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class ProfileUpdate(BaseSchema):
    full_name: str | None = Field(default=None, alias="fullName")
    preferred_language: str | None = Field(default=None, alias="preferredLanguage")
    frequent_routes: list[str] | None = Field(default=None, alias="frequentRoutes")
