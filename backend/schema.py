from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TelegramLogin(BaseModel):
    init_data: str = Field(min_length=1, max_length=16384)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class UserCreate(BaseModel):
    telegram_id: int
    first_name: str
    username: str | None = None


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    first_name: str
    username: str | None

    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    completed: bool | None = None

    @field_validator("title", "completed")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Field cannot be null")
        return value


class TaskResponse(BaseModel):
    id: int
    title: str
    completed: bool
    user_id: int

    model_config = ConfigDict(from_attributes=True)