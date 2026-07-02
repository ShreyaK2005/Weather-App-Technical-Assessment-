"""
Pydantic schemas — define the shape of data going in/out of the API.
This is where request validation (like date range checks) is enforced.
"""
from datetime import date
from typing import List, Optional
from pydantic import BaseModel, field_validator


class DailyWeather(BaseModel):
    date: date
    temp_max: float
    temp_min: float


class WeatherRecordCreate(BaseModel):
    location_query: str
    start_date: date
    end_date: date

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, end_date, info):
        start_date = info.data.get("start_date")
        if start_date and end_date < start_date:
            raise ValueError("end_date must be on or after start_date")
        return end_date


class WeatherRecordUpdate(BaseModel):
    # Only allow updating the date range or the location query — not the
    # resolved lat/lon/weather_data directly, since those should always be
    # re-derived from a real API call, not hand-edited.
    location_query: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class WeatherRecordOut(BaseModel):
    id: int
    location_query: str
    resolved_name: str
    latitude: float
    longitude: float
    start_date: date
    end_date: date
    weather_data: List[DailyWeather]

    class Config:
        from_attributes = True
