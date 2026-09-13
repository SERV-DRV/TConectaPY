from datetime import datetime
from typing import Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field


class BaseAuthSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


# ── Auth ────────────────────────────────────────────────


class RegisterRequest(BaseAuthSchema):
    CUI: str = Field(
        validation_alias=AliasChoices("CUI", "cui"),
        min_length=13,
        max_length=13,
        pattern=r"^\d{13}$",
        examples=["0000000000000"],
    )
    Email: EmailStr = Field(
        validation_alias=AliasChoices("Email", "email"),
    )
    Password: str = Field(
        validation_alias=AliasChoices("Password", "password"),
        min_length=6,
    )


class LoginRequest(BaseAuthSchema):
    CUI: str = Field(
        validation_alias=AliasChoices("CUI", "cui"),
        min_length=13,
        max_length=13,
        pattern=r"^\d{13}$",
    )
    Password: str = Field(
        validation_alias=AliasChoices("Password", "password"),
    )


class RecoverPasswordRequest(BaseAuthSchema):
    Email: EmailStr = Field(
        validation_alias=AliasChoices("Email", "email"),
    )


class ResetPasswordRequest(BaseAuthSchema):
    Email: EmailStr = Field(
        validation_alias=AliasChoices("Email", "email"),
    )
    Token: str = Field(
        validation_alias=AliasChoices("Token", "token"),
    )
    NewPassword: str = Field(
        validation_alias=AliasChoices("NewPassword", "newPassword"),
        min_length=6,
    )


class UpdateEmailRequest(BaseAuthSchema):
    NewEmail: EmailStr = Field(
        validation_alias=AliasChoices("NewEmail", "newEmail"),
    )


# ── Auth Responses ──────────────────────────────────────


class AuthResponse(BaseAuthSchema):
    token: str
    userId: str
    role: str


class MessageResponse(BaseAuthSchema):
    message: str


class TokenResponse(BaseAuthSchema):
    message: str
    token: str


class EmailResponse(BaseAuthSchema):
    email: str


class UpdateEmailResponse(BaseAuthSchema):
    message: str
    email: str


# ── User List ───────────────────────────────────────────


class UserOut(BaseAuthSchema):
    id: str
    cui: str
    email: str
    role: str
    isActive: bool
    createdAt: datetime


# ── Transaction ─────────────────────────────────────────


class TransactionRequest(BaseAuthSchema):
    CardNumber: str = Field(
        validation_alias=AliasChoices("CardNumber", "cardNumber"),
        min_length=15,
        max_length=19,
    )
    ExpirationDate: str = Field(
        validation_alias=AliasChoices("ExpirationDate", "expirationDate"),
    )
    CVV: str = Field(
        validation_alias=AliasChoices("CVV", "cvv"),
        min_length=3,
        max_length=4,
        pattern=r"^\d{3,4}$",
    )
    Amount: float = Field(
        validation_alias=AliasChoices("Amount", "amount"),
        gt=0,
    )


class TransactionResponse(BaseAuthSchema):
    isSuccess: bool
    message: str
    transactionId: str


# ── Error ───────────────────────────────────────────────


class ErrorResponse(BaseAuthSchema):
    StatusCode: int
    Message: str
    Detailed: Optional[str] = None
