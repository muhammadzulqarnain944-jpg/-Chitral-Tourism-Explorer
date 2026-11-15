# Chitral Tourism Explorer

A student Web GIS project using FastAPI, PostgreSQL/PostGIS, Leaflet and OpenStreetMap.

## Project structure

```text
Chitral_Tourist_Points/
├── backend/
│   ├── .env                 # Create this from .env.example
│   ├── .env.example
│   ├── database.py
│   ├── main.py
│   └── requirements.txt
├── data/
│   ├── database/
│   │   └── chitral_tourism_database.sql
│   └── scripts/
│       └── insert_tourist_data.py
├── documentation/
└── frontend/
    ├── app.js
    ├── index.html
    └── style.css
└── README.md
```

## Step 1 - Create the PostgreSQL database

In pgAdmin, create a database named `chitral_tourism_db`.
Open its Query Tool and run all of `data/database/chitral_tourism_database.sql`.

The script creates PostGIS and `public.tourist_attractions` if they do not exist.
It does not delete your existing data.

## Step 2 - Configure the password

Copy `backend/.env.example` to `backend/.env`.
Set the real PostgreSQL password in `.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=chitral_tourism_db
DB_USER=postgres
DB_PASSWORD=YOUR_POSTGRES_PASSWORD
```

Do not upload or share `.env`. A password shown in an earlier screenshot should be changed.

## Step 3 - Install dependencies

From the project root in VS Code terminal:

```bash
python -m pip install -r backend/requirements.txt
```

## Step 4 - Import the tourism dataset (optional)

The geocoding importer queries Nominatim, which is rate limited. Run it only after
the table exists and after checking that network access is available:

```bash
python data/scripts/insert_tourist_data.py
```

Nominatim matches are candidate coordinates. The importer labels them
"Needs manual verification"; check them in QGIS/OSM before relying on them.

## Step 5 - Start the API and website

From the project root:

```bash
python -m uvicorn main:app --app-dir backend --reload
```

Open these pages:

- Website: http://127.0.0.1:8000/
- Swagger API: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/api/health
- Locations: http://127.0.0.1:8000/api/locations
- Categories: http://127.0.0.1:8000/api/categories
- Weather example: http://127.0.0.1:8000/api/weather?latitude=35.85&longitude=71.78

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Database and PostGIS check |
| GET | `/api/locations` | All tourist locations |
| GET | `/api/locations?category=Valley` | Filter by category |
| GET | `/api/categories` | Category totals |
| GET | `/api/weather?latitude=35.85&longitude=71.78` | Current weather |

## Important notes

- Keep the database name consistent: `chitral_tourism_db`.
- This project uses `psycopg` (version 3) in the API and `psycopg2` in the importer.
- The frontend is served by FastAPI at `/static`; do not launch the HTML using Live Server.
- Weather requires an internet connection to Open-Meteo.
- Map tiles require an internet connection to OpenStreetMap.
- Coordinates returned by geocoding are not guaranteed surveyed coordinates.
