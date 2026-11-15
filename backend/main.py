
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from database import get_connection


app = FastAPI(
    title="Chitral Tourism Explorer API",
    description="WebGIS application for exploring tourist attractions in Chitral.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"

if FRONTEND_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(FRONTEND_DIR)),
        name="static"
    )


@app.get("/", include_in_schema=False)
def home():
    index_file = FRONTEND_DIR / "index.html"

    if index_file.exists():
        return FileResponse(index_file)

    return {"message": "Chitral Tourism Explorer API is running"}


@app.get("/api/health")
def health_check():
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    current_database() AS database_name,
                    PostGIS_Full_Version() AS postgis_version,
                    to_regclass('public.tourist_attractions') IS NOT NULL
                        AS table_exists
            """)

            result = cursor.fetchone()

        return {
            "status": "online",
            "database_connected": True,
            "database_name": result["database_name"],
            "postgis_version": result["postgis_version"],
            "table_exists": result["table_exists"]
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(error)}"
        )

    finally:
        if connection is not None:
            connection.close()


@app.get("/api/locations")
def get_locations(category: Optional[str] = Query(None)):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            query = """
                SELECT
                    id,
                    name,
                    category,
                    description,
                    COALESCE(latitude, ST_Y(geom)) AS latitude,
                    COALESCE(longitude, ST_X(geom)) AS longitude,
                    elevation_m,
                    accessibility,
                    best_visit_season
                FROM public.tourist_attractions
                WHERE latitude IS NOT NULL
                   OR geom IS NOT NULL
            """

            params = ()

            if category:
                query += " AND LOWER(category) = LOWER(%s)"
                params = (category,)

            query += " ORDER BY name"

            cursor.execute(query, params)
            rows = cursor.fetchall()

        locations = []

        for row in rows:
            locations.append({
                "id": row["id"],
                "name": row["name"],
                "category": row["category"],
                "description": row["description"],
                "latitude": (
                    float(row["latitude"])
                    if row["latitude"] is not None else None
                ),
                "longitude": (
                    float(row["longitude"])
                    if row["longitude"] is not None else None
                ),
                "elevation": row["elevation_m"],
                "accessibility": row["accessibility"],
                "best_visit_season": row["best_visit_season"]
            })

        return {
            "count": len(locations),
            "locations": locations
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(error)}"
        )

    finally:
        if connection is not None:
            connection.close()


@app.get("/api/categories")
def get_categories():
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT category
                FROM public.tourist_attractions
                WHERE category IS NOT NULL
                ORDER BY category
            """)

            rows = cursor.fetchall()

        return {
            "categories": [row["category"] for row in rows]
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(error)}"
        )

    finally:
        if connection is not None:
            connection.close()


@app.get("/api/locations/{location_id}")
def get_location(location_id: int):
    connection = None

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    name,
                    category,
                    description,
                    COALESCE(latitude, ST_Y(geom)) AS latitude,
                    COALESCE(longitude, ST_X(geom)) AS longitude,
                    elevation_m,
                    accessibility,
                    best_visit_season
                FROM public.tourist_attractions
                WHERE id = %s
            """, (location_id,))

            row = cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Tourist location not found"
            )

        result = dict(row)

        if result["latitude"] is not None:
            result["latitude"] = float(result["latitude"])

        if result["longitude"] is not None:
            result["longitude"] = float(result["longitude"])

        result["elevation"] = result.pop("elevation_m")

        return result

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(error)}"
        )

    finally:
        if connection is not None:
            connection.close()
