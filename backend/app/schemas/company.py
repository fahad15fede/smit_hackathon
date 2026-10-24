from datetime import date, time
from typing import Literal
from zoneinfo import available_timezones

from pydantic import BaseModel, Field, field_validator

from .common import ORMModel

Weekday = Literal["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class CompanyOut(ORMModel):
    id: int
    name: str
    timezone: str
    office_start: time
    grace_minutes: int
    weekend_days: list[Weekday]

    @field_validator("weekend_days", mode="before")
    @classmethod
    def split_days(cls, value: str | list[str]) -> list[str]:
        return [day for day in value.split(",") if day] if isinstance(value, str) else value


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    timezone: str | None = None
    office_start: time | None = None
    grace_minutes: int | None = Field(default=None, ge=0, le=240)
    weekend_days: list[Weekday] | None = Field(default=None, max_length=6)

    @field_validator("timezone")
    @classmethod
    def known_timezone(cls, value: str | None) -> str | None:
        if value is not None and value not in available_timezones():
            raise ValueError("Unknown timezone")
        return value


class HolidayCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    day: date


class HolidayOut(ORMModel):
    id: int
    name: str
    day: date
