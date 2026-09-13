from pydantic import BaseModel, ConfigDict, Field, AliasChoices


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class ProfileResponse(BaseSchema):
    user_id: str = Field(alias="userId")
    full_name: str | None = Field(default=None, alias="fullName")
    preferred_language: str = Field(default="es", alias="preferredLanguage")
    frequent_routes: list[str] = Field(default_factory=list, alias="frequentRoutes")
    is_active: bool = Field(default=True, alias="isActive")
    created_at: str | None = Field(default=None, alias="createdAt")
    updated_at: str | None = Field(default=None, alias="updatedAt")


class ProfileUpdate(BaseSchema):
    full_name: str | None = Field(default=None, alias="fullName")
    preferred_language: str | None = Field(default=None, alias="preferredLanguage")
    frequent_routes: list[str] | None = Field(default=None, alias="frequentRoutes")
