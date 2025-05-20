from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class ScheduleSchema(BaseModel):
    date: str = Field(min_length=10, max_length=10, pattern=r"^\d{4}-\d{2}-\d{2}$")
    time: str = Field(min_length=5, max_length=5, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")

    @field_validator("date")
    def validate_schedule_date(cls, value: str):
        try:
            datetime.strptime(value, "%Y-%m-%d")

            return value
        except ValueError:
            raise ValueError("Invalid date format or date does not exist")

    @field_validator("time")
    def validate_time(cls, value: str):
        try:
            datetime.strptime(value, "%H:%M")

            return value
        except ValueError:
            raise ValueError("Invalid time format")
