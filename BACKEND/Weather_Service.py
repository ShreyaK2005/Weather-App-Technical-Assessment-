"""
Talks to the Open-Meteo API (no API key required):
- Geocoding: resolves a free-text location into lat/lon (this is also our
  "fuzzy match / validate the location really exists" logic).
- Forecast: current weather + 5-day forecast.
- Archive: historical daily temps, for date ranges in the past.

Docs: https://open-meteo.com/en/docs
"""
import httpx
from datetime import date
import os
from dotenv import load_dotenv
load_dotenv()

GEOCODE_URL = os.getenv("GEOCODE_URL")
FORECAST_URL = os.getenv("FORECAST_URL")
ARCHIVE_URL = os.getenv("ARCHIVE_URL")
AIR_QUALITY_URL = os.getenv("AIR_QUALITY_URL")


class LocationNotFoundError(Exception):
    pass
class WeatherServiceError(Exception):
    pass


async def geocode_location(query: str) -> dict:
    """
    Resolve free-text (city, zip, landmark, 'lat,lon') into coordinates.
    Raises LocationNotFoundError if nothing matches — this is our
    location-validation / fuzzy-match step.
    """
    query = query.strip()

    # Support raw "lat,lon" input directly
    if "," in query:
        parts = query.split(",")
        if len(parts) == 2:
            try:
                lat, lon = float(parts[0]), float(parts[1])
                return {"name": f"{lat},{lon}", "latitude": lat, "longitude": lon}
            except ValueError:
                pass  # fall through to geocoding search

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                GEOCODE_URL,
                params={"name": query, "count": 1}
            )
            resp.raise_for_status()
            data = resp.json()

    except (httpx.RequestError, httpx.HTTPStatusError):
        raise WeatherServiceError(
            "Unable to connect to the weather service."
        )

    results = data.get("results")
    if not results:
        raise LocationNotFoundError(f"Oops! Location not found, please try again: '{query}'")

    top = results[0]
    label = f"{top['name']}, {top.get('admin1', '')} {top.get('country', '')}".strip()
    return {"name": label, "latitude": top["latitude"], "longitude": top["longitude"]}


async def get_current_and_forecast(lat: float, lon: float) -> dict:
    """Current conditions + 5-day daily forecast."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": (
            "temperature_2m,"
            "weather_code,"
            "wind_speed_10m,"
            "relative_humidity_2m"
        ),
        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min,"
            "weather_code,"
            "uv_index_max,"
            "precipitation_sum,"
            "precipitation_probability_max,"
            "wind_speed_10m_max,"
            "relative_humidity_2m_mean,"
            "sunrise,"
            "sunset"
        ),
        "forecast_days": 5,
        "timezone": "auto",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(FORECAST_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

            daily = data.get("daily", {})

            daily["weather_advice"] = [
                weather_advice(hi, lo)
                for hi, lo in zip(
                    daily.get("temperature_2m_max", []),
                    daily.get("temperature_2m_min", [])
                )
            ]

            daily["uv_advice"] = [
                get_uv_advice(uv)
                for uv in daily.get("uv_index_max", [])
            ]

            data["daily"] = daily

            return data

    except (httpx.RequestError, httpx.HTTPStatusError):
        raise WeatherServiceError(
            "Unable to connect to the weather service."
        )


async def get_daily_range(lat: float, lon: float, start: date, end: date) -> list:
    """
    Daily max/min temps for an arbitrary date range.
    Uses the archive endpoint for past dates and the forecast endpoint for
    upcoming ones — Open-Meteo splits these across two APIs.
    """
    today = date.today()
    results = []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:

            if start < today:
                resp = await client.get(
                    ARCHIVE_URL,
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "start_date": start.isoformat(),
                        "end_date": min(end, today).isoformat(),
                        "daily": (
                            "temperature_2m_max,"
                            "temperature_2m_min,"
                            "weather_code,"
                            "precipitation_sum,"
                            "wind_speed_10m_max"
                        ),
                        "timezone": "auto",
                    },
                )
                resp.raise_for_status()
                results.append(resp.json().get("daily", {}))

            if end >= today:
                resp = await client.get(
                    FORECAST_URL,
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "start_date": max(start, today).isoformat(),
                        "end_date": end.isoformat(),
                        "daily": (
                            "temperature_2m_max,"
                            "temperature_2m_min,"
                            "weather_code,"
                            "uv_index_max,"
                            "precipitation_sum,"
                            "precipitation_probability_max,"
                            "wind_speed_10m_max,"
                            "relative_humidity_2m_mean,"
                            "sunrise,"
                            "sunset"
                        ),
                        "timezone": "auto",
                    },
                )
                resp.raise_for_status()
                results.append(resp.json().get("daily", {}))

    except (httpx.RequestError, httpx.HTTPStatusError):
        raise WeatherServiceError(
            "Unable to retrieve weather data from Open-Meteo."
        )

    # Merge the (up to 2) daily blocks into a flat list of {date, temp_max, temp_min}
    merged = []
    for block in results:
        dates = block.get("time", [])

        tmax = block.get("temperature_2m_max", [])
        tmin = block.get("temperature_2m_min", [])
        weather = block.get("weather_code", [])
        uv = block.get("uv_index_max", [])
        humidity = block.get("relative_humidity_2m_mean", [])
        wind = block.get("wind_speed_10m_max", [])
        rain = block.get("precipitation_sum", [])
        rain_prob = block.get("precipitation_probability_max", [])
        sunrise = block.get("sunrise", [])
        sunset = block.get("sunset", [])

        for i in range(len(dates)):
            merged.append({
                "date": dates[i],

                "temp_max":
                    tmax[i] if i < len(tmax) else None,

                "temp_min":
                    tmin[i] if i < len(tmin) else None,

                "weather_code":
                    weather[i] if i < len(weather) else None,

                "uv_index":
                    uv[i] if i < len(uv) else None,

                "humidity":
                    humidity[i] if i < len(humidity) else None,

                "wind_speed":
                    wind[i] if i < len(wind) else None,

                "rain":
                    rain[i] if i < len(rain) else None,

                "rain_probability":
                    rain_prob[i] if i < len(rain_prob) else None,

                "sunrise":
                    sunrise[i] if i < len(sunrise) else None,

                "sunset":
                    sunset[i] if i < len(sunset) else None,

                "uv_advice":
                    get_uv_advice(uv[i])
                    if i < len(uv)
                    else "UV data unavailable.",
                         
                "weather_advice":
                     weather_advice(
                     tmax[i] if i < len(tmax) else 25,
                     tmin[i] if i < len(tmin) else 15
            )
            })
    return merged


async def get_air_quality(lat: float, lon: float) -> dict:
    """
    Fetch current air quality information for a location.
    """

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "european_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone",
        "timezone": "auto",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(AIR_QUALITY_URL, params=params)
            response.raise_for_status()
            data = response.json()

    except (httpx.RequestError, httpx.HTTPStatusError):
        raise WeatherServiceError("Unable to retrieve air quality data.")

    return data.get("current", {})


def get_google_maps_url(lat: float, lon: float) -> str:
    return f"https://www.google.com/maps?q={lat},{lon}"
def get_youtube_url(location: str) -> str:
    return (
        f"https://www.youtube.com/results?search_query={location}"
    )

def weather_advice(temp_max: float, temp_min: float) -> list[str]:

        advice = []

        if temp_max >= 35:
            advice.extend([
                "Stay hydrated.",
                "Wear light clothing.",
                "Avoid prolonged outdoor activity during the afternoon."
            ])

        elif temp_max >= 30:
            advice.extend([
                "Carry water if you're outdoors.",
                "Wear light clothing.",
                "Use sunscreen during peak sunlight hours."
            ])

        if temp_min <= 10:
            advice.extend([
                "Wear warm clothing.",
                "Be cautious of cold weather."
            ])

        elif temp_min <= 20:
            advice.append(
                "Carry a light jacket for cooler mornings and evenings."
            )

        if 20 < temp_max < 30:
            advice.append(
                "Weather conditions are comfortable for most outdoor activities."
            )

        return advice

def get_aqi_description(aqi: int) -> str:
    if aqi <= 20:
        return "Excellent"

    elif aqi <= 40:
        return "Good"

    elif aqi <= 60:
        return "Moderate"

    elif aqi <= 80:
        return "Poor"

    elif aqi <= 100:
        return "Very Poor"

    return "Extremely Poor"
def get_air_quality_advice(aqi: int) -> str:
    if aqi <= 20:
        return "Excellent air quality. Outdoor activities are ideal."

    elif aqi <= 40:
        return "Air quality is good. Most people can enjoy outdoor activities."

    elif aqi <= 60:
        return "Sensitive individuals should limit prolonged outdoor exertion."

    elif aqi <= 80:
        return "Consider reducing outdoor activities, especially if you have asthma."

    elif aqi <= 100:
        return "Avoid strenuous outdoor exercise."

    return "Stay indoors if possible and wear a mask when outside."
def get_uv_advice(uv):
    if uv is None:
        return "UV data unavailable."

    if uv <= 2:
        return "Low UV exposure. Minimal protection needed."

    elif uv <= 5:
        return "Moderate UV exposure. Consider sunglasses and sunscreen."

    elif uv <= 7:
        return "High UV exposure. Use sunscreen and seek shade during midday."

    elif uv <= 10:
        return "Very High UV exposure. Wear protective clothing and avoid prolonged sun exposure."

    else:
        return "Extreme UV exposure. Avoid going outdoors unless absolutely necessary."

def get_weather_description(code):

    weather_codes = {
        0: "Clear Sky",
        1: "Mainly Clear",
        2: "Partly Cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing Rime Fog",
        51: "Light Drizzle",
        53: "Moderate Drizzle",
        55: "Dense Drizzle",
        61: "Light Rain",
        63: "Moderate Rain",
        65: "Heavy Rain",
        71: "Light Snow",
        73: "Moderate Snow",
        75: "Heavy Snow",
        80: "Rain Showers",
        81: "Heavy Rain Showers",
        82: "Violent Rain Showers",
        95: "Thunderstorm",
        96: "Thunderstorm with Hail",
        99: "Severe Thunderstorm",
    }

    return weather_codes.get(code, "Unknown")

def current_weather_advice(temp: float) -> list[str]:
    advice = []

    if temp >= 35:
        advice.extend([
            "Stay hydrated.",
            "Wear light clothing.",
            "Avoid prolonged outdoor activity during the afternoon."
        ])

    elif temp >= 30:
        advice.extend([
            "Carry water if you're outdoors.",
            "Wear light clothing.",
            "Use sunscreen."
        ])

    elif temp <= 10:
        advice.extend([
            "Wear warm clothing.",
            "Be cautious of cold weather."
        ])

    elif temp <= 20:
        advice.append(
            "Carry a light jacket."
        )

    else:
        advice.append(
            "Weather conditions are comfortable."
        )

    return advice
