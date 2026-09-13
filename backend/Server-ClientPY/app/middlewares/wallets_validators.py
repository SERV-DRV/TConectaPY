from pydantic import BaseModel, ConfigDict, Field, AliasChoices


class BaseSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class WalletInitializeBody(BaseSchema):
    user_id: str = Field(alias="UserId")
    courtesy_trips: int = Field(default=5, alias="CourtesyTrips")
    balance: float = Field(default=0.0, alias="Balance")


class WalletRechargeBody(BaseSchema):
    user_id: str = Field(alias="UserId")
    amount: float = Field(alias="Amount")
