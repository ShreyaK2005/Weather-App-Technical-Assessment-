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

    weather_code: Optional[int] = None

    humidity: Optional[float] = None

    wind_speed: Optional[float] = None

    rain: Optional[float] = None

    rain_probability: Optional[float] = None

    uv_index: Optional[float] = None

    sunrise: Optional[str] = None

    sunset: Optional[str] = None

    uv_advice: Optional[str] = None

    weather_advice: List[str] = []


class WeatherRecordCreate(BaseModel):
    location_query: str
    start_date: date
    end_date: date

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, end_date, info):

        start_date = info.data.get("start_date")

        if start_date:

            if end_date < start_date:
                raise ValueError(
                    "End date must be after start date."
                )

            if (end_date - start_date).days > 15:
                raise ValueError(
                    "Date range invalid. Please try to keep dates to maximum 15 days."
                )

        return end_date


class WeatherRecordUpdate(BaseModel):
    # Only allow updating the date range or the location query — not the
    # resolved lat/lon/weather_data directly, since those should always be
    # re-derived from a real API call, not hand-edited.
    location_query: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, end_date, info):

        start_date = info.data.get("start_date")

        if start_date and end_date:

            if end_date < start_date:
                raise ValueError(
                    "End date must be after start date."
                )

            if (end_date - start_date).days > 15:
                raise ValueError(
                    "Date range invalid. Please try to keep dates to maximum 15 days."
                )

        return end_date


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
