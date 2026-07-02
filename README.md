# Weather-App
# Weather App — Backend (Python)

FastAPI + SQLAlchemy (SQLite) + Open-Meteo API (no key required).

## Project structure
```
pmAccelerator Assessment
├── main.py            # FastAPI app, all endpoints
├── database.py        # SQLAlchemy engine/session setup
├── models.py          # DB table definitions
├── schemas.py         # Pydantic request/response validation
├── weather_service.py # Calls to the external Open-Meteo API
├── requirements.txt
└── README.md
```

## Setup (VS Code)

1. Open the `backend/` folder in VS Code (`code backend`).
2. Install the **Python** extension (Microsoft) if you don't have it — VS Code will
   prompt you when it detects `.py` files.
3. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```
4. In VS Code, hit `Cmd/Ctrl+Shift+P` → "Python: Select Interpreter" → pick the
   `venv` one, so VS Code's linting/autocomplete matches what you actually run.
5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```
7. Open **http://127.0.0.1:8000/docs** — this is FastAPI's auto-generated interactive
   API explorer. You can test every endpoint here before the frontend exists.

## Endpoints so far

| Method | Path | Purpose |
|---|---|---|
| GET | `/weather/current?location=...` | Current + 5-day forecast for a location |
| POST | `/records` | Create a stored record (location + date range → fetched & saved) |
| GET | `/records` | List all stored records |
| GET | `/records/{id}` | Get one record |
| PUT | `/records/{id}` | Update a record's location/date range (re-fetches weather) |
| DELETE | `/records/{id}` | Delete a record |
| GET | `/records/{id}/export?format=json\|csv\|xml\|markdown` | Export a record |

## What's not done yet (next steps)
- PDF export format
- Bonus API integration (2.2): YouTube videos / Google Maps for the location
- Location input can be a city name, zip, or `"lat,lon"` string — landmark names
  will work if Open-Meteo's geocoder recognizes them, worth testing a few
- `.env` handling if you swap to an API that needs a key (Open-Meteo doesn't)

## Notes on design decisions
- **Open-Meteo** was chosen over OpenWeatherMap because it needs no API key
  (one less thing to configure) and has a free historical archive endpoint,
  which the date-range CRUD feature needs.
- Location validation = geocoding. If Open-Meteo can't resolve the input to
  coordinates, we return a 404 — this satisfies "validate the location really
  exists" and gives basic fuzzy matching for free (Open-Meteo's geocoder does
  its own fuzzy text matching).
- CORS is currently locked to `localhost:5173` (Vite's default port) — update
  this in `main.py` if your frontend runs elsewhere.
