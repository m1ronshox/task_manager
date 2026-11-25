from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, Field, HttpUrl, StringConstraints

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Short = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
Phone = Annotated[str, StringConstraints(pattern=r"^\+?[0-9]{7,15}$")]
Money = Annotated[int, Field(ge=0, le=10_000_000)]
Status = Literal["new", "confirmed", "in_progress", "completed", "cancelled"]


class VehicleInput(BaseModel):
    make: Short
    model: Short
    year: int = Field(ge=1900, le=datetime.now().year + 1)
    engine: Short = Field(max_length=40)
    fuel: Short = Field(max_length=40)
    plate: Short = Field(max_length=24)
    mileage: int = Field(ge=0, le=9_999_999)
    image: HttpUrl | None = None


class BookingInput(BaseModel):
    vehicle_id: int
    service_id: int
    starts_at: AwareDatetime
    phone: Phone
    notes: str = Field(default="", max_length=1200)


class QuantityInput(BaseModel):
    quantity: int = Field(ge=0, le=99)


class ProfileInput(BaseModel):
    phone: Phone | None = None
    language: Literal["uz", "ru", "en"] = "uz"


class MaintenanceInput(BaseModel):
    title: Name
    performed_on: date
    next_on: date | None = None
    cost: Money = 0
    oil_change: bool = False


class CategoryInput(BaseModel):
    name: Name = Field(max_length=100)


class ServiceInput(BaseModel):
    category_id: int
    name: Name
    description: str = Field(max_length=1600)
    price: Money | None = None
    make: Short | None = None
    duration: int = Field(ge=15, le=480)
    available: bool = False
    image: HttpUrl | None = None


class ProductInput(BaseModel):
    category_id: int
    name: Name
    description: str = Field(max_length=1600)
    make: Short | None = None
    price: Money
    stock: int = Field(ge=0, le=1_000_000)
    image: HttpUrl | None = None


class BannerInput(BaseModel):
    title: Name
    description: str = Field(max_length=1000)
    image: HttpUrl | None = None
    active: bool = True


class StatusInput(BaseModel):
    status: Status



class BusinessInput(BaseModel):
    phone: Phone | None = None
    address: str | None = Field(default=None, max_length=240)
    hours: str | None = Field(default=None, max_length=160)
