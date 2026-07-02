"""
SQLAlchemy ORM models.

WeatherRecord = the CRUD entity from Tech Assessment #2, section 2.1.
Each row represents: a user-submitted location + date range, with the
weather data fetched and stored for that range.
"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text
from sqlalchemy.sql import func
from Database import Base


class WeatherRecord(Base):
    __tablename__ = "weather_records"

    id = Column(Integer, primary_key=True, index=True)

    # What the user typed in (e.g. "Nagpur", "10001", "40.7,-74.0")
    location_query = Column(String, nullable=False)

    # Resolved/validated location info (from geocoding)
    resolved_name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # Date range requested
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    # Weather data for the range, stored as JSON text
    # e.g. [{"date": "2026-07-01", "temp_max": 30.2, "temp_min": 21.5}, ...]
    weather_data = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
