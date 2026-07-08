"""
Main FastAPI application.

Run with:  uvicorn main:app --reload
Docs at:   http://127.0.0.1:8000/docs
"""
import json
import csv
import io
import logging

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from Weather_Service import get_air_quality_advice
from sqlalchemy import func
from typing import Optional

import models, schemas, Weather_Service
from Database import engine, get_db
from datetime import date

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# Create DB tables on startup (fine for SQLite + a project this size)
models.Base.metadata.create_all(bind=engine)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Weather App API")

# Allow the React dev server (localhost:5173 for Vite) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Weather display endpoints (Assessment 1 needs) ----------

@app.get("/weather/current")
async def current_weather(
    location: str = Query(..., description="City, zip, landmark, or 'lat,lon'"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    logger.info(f"Weather request received for location: {location}")
    if (start_date and not end_date) or (end_date and not start_date):
        raise HTTPException(
            status_code=400,
            detail="Please provide both start_date and end_date."
        )

    if start_date and end_date and end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="end_date must be on or after start_date."
        )
    try:
        loc = await Weather_Service.geocode_location(location)

    except Weather_Service.LocationNotFoundError as e:
        logger.warning(f"Location not found: {location}")
        raise HTTPException(status_code=404, detail=str(e))

    except Weather_Service.WeatherServiceError as e:
        logger.error(f"Weather API unavailable: {e}")
        raise HTTPException(status_code=503, detail=str(e))

    # Decide which weather endpoint to use

    if start_date and end_date:

        weather_data = await Weather_Service.get_daily_range(
            loc["latitude"],
            loc["longitude"],
            start_date,
            end_date
        )

        temperature = None
        uv_index = None

    else:

        data = await Weather_Service.get_current_and_forecast(
            loc["latitude"],
            loc["longitude"]
        )

        logger.info(f"Successfully retrieved weather for {loc['name']}")

        temperature = data["current"]["temperature_2m"]

        daily = data.get("daily", {})

        uv_index = None

        if daily.get("uv_index_max"):
            uv_index = daily["uv_index_max"][0]


    air_quality = await Weather_Service.get_air_quality(
        loc["latitude"],
        loc["longitude"]
    )

    air_quality["status"] = Weather_Service.get_aqi_description(
        air_quality.get("european_aqi", 0)
    )

    air_quality["health_advice"] = Weather_Service.get_air_quality_advice(
        air_quality.get("european_aqi", 0)
    )

    return {
        "location": loc,

        "current": None if start_date else data.get("current"),

        "daily_forecast":
            weather_data if start_date
            else data.get("daily"),

        "start_date":
            start_date if start_date
            else date.today(),

        "end_date":
            end_date if end_date
            else data["daily"]["time"][-1],
        "air_quality":
            None if start_date
            else air_quality,
        "google_maps": Weather_Service.get_google_maps_url(
            loc["latitude"],
            loc["longitude"]
        ),
        "youtube": Weather_Service.get_youtube_url(
            loc["name"]
        ),
        "weather_advice":
            Weather_Service.current_weather_advice(temperature)
            if temperature is not None
            else ["Weather advice unavailable for custom date range."],
        "uv_index": uv_index,

        "uv_advice": Weather_Service.get_uv_advice(uv_index)
    }


# ---------- CRUD endpoints (Assessment 2, section 2.1) ----------

@app.post("/records", response_model=schemas.WeatherRecordOut)
async def create_record(payload: schemas.WeatherRecordCreate, db: Session = Depends(get_db)):
    try:
        loc = await Weather_Service.geocode_location(payload.location_query)

        daily = await Weather_Service.get_daily_range(
            loc["latitude"],
            loc["longitude"],
            payload.start_date,
            payload.end_date,
        )

    except Weather_Service.LocationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Weather_Service.WeatherServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))

    if not daily:
        raise HTTPException(
            status_code=400,
            detail="No weather data available for that date range"
        )

    record = models.WeatherRecord(
        location_query=payload.location_query,
        resolved_name=loc["name"],
        latitude=loc["latitude"],
        longitude=loc["longitude"],
        start_date=payload.start_date,
        end_date=payload.end_date,
        weather_data=json.dumps(daily),
    )

    try:
        db.add(record)
        db.commit()
        db.refresh(record)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save the record."
        )

    return _serialize(record)


@app.get("/records", response_model=list[schemas.WeatherRecordOut])
def list_records(
    location: Optional[str] = Query(
        None,
        description="Optional location filter. Leave blank to return all records."
    ),
    db: Session = Depends(get_db),
):
    query = db.query(models.WeatherRecord)

    # Filter only if a location is provided
    if location:
        query = query.filter(
            models.WeatherRecord.location_query.ilike(f"%{location}%")
        )

    records = query.all()

    return [_serialize(record) for record in records]





@app.get("/records/{record_id}", response_model=schemas.WeatherRecordOut)
def get_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(models.WeatherRecord).filter(models.WeatherRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return _serialize(record)


@app.put("/records/{record_id}", response_model=schemas.WeatherRecordOut)
async def update_record(record_id: int, payload: schemas.WeatherRecordUpdate, db: Session = Depends(get_db)):
    record = db.query(models.WeatherRecord).filter(models.WeatherRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    new_location = payload.location_query or record.location_query
    new_start = payload.start_date or record.start_date
    new_end = payload.end_date or record.end_date
    if new_end < new_start:
        raise HTTPException(status_code=400, detail="end_date must be on or after start_date")

    # If location or dates changed, re-fetch weather data so it stays accurate
    if (payload.location_query, payload.start_date, payload.end_date) != (None, None, None):
        try:
            loc = await Weather_Service.geocode_location(new_location)

            daily = await Weather_Service.get_daily_range(
                loc["latitude"],
                loc["longitude"],
                new_start,
                new_end,
            )

        except Weather_Service.LocationNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))

        except Weather_Service.WeatherServiceError as e:
            raise HTTPException(status_code=503, detail=str(e))
        record.resolved_name = loc["name"]
        record.latitude = loc["latitude"]
        record.longitude = loc["longitude"]
        record.weather_data = json.dumps(daily)

    record.location_query = new_location
    record.start_date = new_start
    record.end_date = new_end

    try:
        db.commit()
        db.refresh(record)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to update the record."
        )

    return _serialize(record)


@app.delete("/records/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(models.WeatherRecord).filter(models.WeatherRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    try:
        db.delete(record)
        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to delete the record."
        )

    return {"detail": "deleted"}


# ---------- Export endpoint (Assessment 2, section 2.3) ----------

@app.get("/records/{record_id}/export")
async def export_record (record_id: int, format: str = Query("json", enum=["json", "csv", "xml", "markdown","pdf"]), db: Session = Depends(get_db)):
    record = db.query(models.WeatherRecord).filter(models.WeatherRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    data = _serialize(record)
    # Fetch live weather information for the stored location
    weather = await Weather_Service.get_current_and_forecast(
        record.latitude,
        record.longitude
    )

    air_quality = await Weather_Service.get_air_quality(
        record.latitude,
        record.longitude
    )

    temperature = weather["current"]["temperature_2m"]

    uv_index = None
    if weather.get("daily", {}).get("uv_index_max"):
        uv_index = weather["daily"]["uv_index_max"][0]

    google_maps = Weather_Service.get_google_maps_url(
        record.latitude,
        record.longitude
    )

    youtube = Weather_Service.get_youtube_url(
        record.resolved_name
    )

    weather_advice = "<br/>".join(
        Weather_Service.current_weather_advice(temperature)
    )

    aqi_status = Weather_Service.get_aqi_description(
        air_quality.get("european_aqi", 0)
    )

    aqi_advice = Weather_Service.get_air_quality_advice(
        air_quality.get("european_aqi", 0)
    )

    uv_advice = Weather_Service.get_uv_advice(
        uv_index
    )

    if format == "json":
        content = json.dumps(data, default=str, indent=2)
        media_type = "application/json"

    elif format == "csv":
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["date", "temp_max", "temp_min"])
        writer.writeheader()
        for row in data["weather_data"]:
            writer.writerow(row)
        content = buf.getvalue()
        media_type = "text/csv"

    elif format == "xml":
        rows = "".join(
            f"<day><date>{d['date']}</date><temp_max>{d['temp_max']}</temp_max>"
            f"<temp_min>{d['temp_min']}</temp_min></day>"
            for d in data["weather_data"]
        )
        content = f"<record><location>{data['resolved_name']}</location>{rows}</record>"
        media_type = "application/xml"

    elif format == "markdown":
        lines = [f"# Weather Record: {data['resolved_name']}", "", "| Date | Max Temp | Min Temp |", "|---|---|---|"]
        for d in data["weather_data"]:
            lines.append(f"| {d['date']} | {d['temp_max']} | {d['temp_min']} |")
        content = "\n".join(lines)
        media_type = "text/markdown"

    elif format == "pdf":
        buffer = io.BytesIO()

        doc = SimpleDocTemplate(buffer)

        styles = getSampleStyleSheet()

        elements = []

        elements.append(
            Paragraph(
                f"<b>Weather Record</b>",
                styles["Title"]
            )
        )

        elements.append(
            Paragraph(
                f"Location: {data['resolved_name']}",
                styles["Heading2"]
            )
        )

        elements.append(
            Paragraph(
                f"Date Range: {data['start_date']} to {data['end_date']}",
                styles["Normal"]
            )
        )
        elements.append(
            Paragraph(
                f"<b>Current Temperature:</b> {temperature} °C",
                styles["Normal"]
            )
        )

        elements.append(
            Paragraph(
                f"<b>Air Quality:</b> {aqi_status}",
                styles["Normal"]
            )
        )

        elements.append(
            Paragraph(
                f"<b>Health Advice:</b><br/>{aqi_advice}",
                styles["Normal"]
            )
        )

        elements.append(
            Paragraph(
                f"<b>UV Index:</b> {uv_index}",
                styles["Normal"]
            )
        )

        elements.append(
            Paragraph(
                f"<b>UV Advice:</b> {uv_advice}",
                styles["Normal"]
            )
        )

        elements.append(
            Paragraph(
                f"<b>Weather Recommendation:</b> {weather_advice}",
                styles["Normal"]
            )
        )

        elements.append(
            Paragraph(
                f"<b>Google Maps:</b> {google_maps}",
                styles["Normal"]
            )
        )

        elements.append(
            Paragraph(
                f"<b>YouTube:</b> {youtube}",
                styles["Normal"]
            )
        )

        elements.append(Paragraph("<br/>", styles["Normal"]))

        elements.append(Paragraph("<br/>", styles["Normal"]))

        table_data = [[
            "Date",
            "Max Temp",
            "Min Temp",
            "Humidity",
            "Wind",
            "Rain",
            "Rain %",
            "UV",
            "Sunrise",
            "Sunset"
        ]]

        for day in data["weather_data"]:
            table_data.append([
                day.get("date", "-"),
                str(day.get("temp_max", "-")),
                str(day.get("temp_min", "-")),
                str(day.get("humidity", "-")),
                str(day.get("wind_speed", "-")),
                str(day.get("rain", "-")),
                str(day.get("rain_probability", "-")),
                str(day.get("uv_index", "-")),
                day.get("sunrise", "-"),
                day.get("sunset", "-")
            ])

        table = Table(table_data)

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ]))

        elements.append(table)

        doc.build(elements)

        buffer.seek(0)

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    f"attachment; filename=record_{record_id}.pdf"
            },
        )

    return StreamingResponse(
        io.StringIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=record_{record_id}.{format}"},
    )


def _serialize(record: models.WeatherRecord) -> dict:
    return {
        "id": record.id,
        "location_query": record.location_query,
        "resolved_name": record.resolved_name,
        "latitude": record.latitude,
        "longitude": record.longitude,
        "start_date": record.start_date,
        "end_date": record.end_date,
        "weather_data": json.loads(record.weather_data),
    }
