"""
Chitral Tourism Explorer: geocode and insert/update candidate attractions.

This script uses OpenStreetMap Nominatim. Nominatim results are candidate
matches, not guaranteed surveyed coordinates. Verify every coordinate.
Run only after creating the database table with the supplied SQL file.
"""

import os
import time
from pathlib import Path

import dotenv
import psycopg2
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError

PROJECT_DIR = Path(__file__).resolve().parents[2]
dotenv.load_dotenv(PROJECT_DIR / "backend" / ".env")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "chitral_tourism_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD")
}

if not DB_CONFIG["password"]:
    raise RuntimeError("Set DB_PASSWORD in backend/.env before running this script.")

attractions = [
    ("Chitral Fort", "Historical", "Historic royal fort associated with the former rulers of Chitral, situated near the Chitral River.", "Accessible from Chitral town", "Spring, Summer, Autumn"),
    ("Shahi Mosque", "Religious and Historical", "An important historical mosque in Chitral known for its traditional architecture.", "Accessible from Chitral town", "All year"),
    ("Chitral Museum", "Museum", "A cultural museum displaying the traditional heritage, history and artifacts of Chitral.", "Accessible from Chitral town", "Spring, Summer, Autumn"),
    ("Chitral Polo Ground", "Cultural", "A traditional polo ground associated with the famous polo culture of Chitral.", "Accessible from Chitral town", "Summer"),
    ("Chitral Gol National Park", "National Park", "A protected mountain landscape known for markhor, wildlife and alpine scenery.", "Road access followed by local travel", "Spring, Summer, Autumn"),
    ("Birmoghlasht Summer Fort", "Historical and Viewpoint", "A historic summer residence associated with the former royal family of Chitral, offering mountain views.", "Mountain road; local transport recommended", "Summer, Autumn"),
    ("Bumburet Valley", "Valley", "The largest of the three famous Kalash valleys, known for its culture and mountain scenery.", "Road access through Ayun", "Spring, Summer, Autumn"),
    ("Rumbur Valley", "Valley", "A beautiful Kalash valley featuring traditional settlements and mountain landscapes.", "Mountain road through Kalash region", "Spring, Summer, Autumn"),
    ("Birir Valley", "Valley", "One of the three Kalash valleys, recognized for its cultural traditions and natural environment.", "Road access through Ayun", "Spring, Summer, Autumn"),
    ("Kalasha Dur Museum", "Museum", "A museum associated with the history and cultural heritage of the Kalash community.", "Local road access in Bumburet", "Spring, Summer, Autumn"),
    ("Garam Chashma", "Hot Spring", "A scenic valley famous for its natural hot springs and surrounding mountains.", "Road access from Chitral", "Spring, Summer, Autumn"),
    ("Shandur Pass", "Mountain Pass", "A high mountain pass famous for its traditional polo festival and alpine scenery. Located on the Upper Chitral and Gilgit-Baltistan boundary.", "Seasonal mountain road", "Summer"),
    ("Mastuj", "Scenic Town", "A scenic settlement in Upper Chitral surrounded by mountains and river landscapes.", "Road access from Chitral", "Spring, Summer, Autumn"),
    ("Booni", "Scenic Town", "An important town in Upper Chitral surrounded by beautiful mountain scenery.", "Road access", "Spring, Summer, Autumn"),
    ("Laspur Valley", "Valley", "A scenic Upper Chitral valley known for traditional settlements, mountain landscapes and access toward Shandur.", "Mountain road", "Summer"),
    ("Broghil Valley", "Valley", "A remote high-altitude valley in Upper Chitral featuring lakes, meadows and mountain scenery.", "Remote seasonal road; local guidance recommended", "Summer"),
    ("Madaklasht", "Valley", "A mountain settlement known for winter scenery, outdoor activities and beautiful landscapes.", "Mountain road", "Summer, Winter"),
    ("Ayun Valley", "Valley", "A scenic valley and gateway toward the Kalash valleys, situated near the Chitral River.", "Road access", "Spring, Summer, Autumn"),
    ("Drosh", "Scenic Town", "A town in Lower Chitral surrounded by mountain landscapes and traditional settlements.", "Road access", "All year"),
    ("Golen Gol", "Nature and Valley", "A mountain valley area known for natural scenery, streams and surrounding forests.", "Local road and trekking access", "Summer"),
    ("Qaqlasht Meadows", "Meadows", "High-altitude open meadows in Upper Chitral known for seasonal greenery and mountain views.", "Seasonal road access", "Spring, Summer"),
    ("Shandur Lake", "Lake", "A high-altitude lake in the Shandur Pass landscape, visited for its natural scenery.", "Seasonal mountain road", "Summer"),
    ("Terich Valley", "Valley", "A high mountain valley in Upper Chitral associated with trekking and access toward the Hindu Kush peaks.", "Local road and trekking access", "Summer"),
    ("Tirich Mir Viewpoint", "Mountain Viewpoint", "A representative viewpoint in the Chitral region for views toward Tirich Mir, the highest peak of the Hindu Kush.", "Viewpoint location requires local verification", "Summer"),
    ("Lowari Pass", "Mountain Pass", "A historic mountain crossing on the route connecting Chitral with Upper Dir.", "Mountain road; route conditions vary", "Season dependent"),
]

MIN_LAT, MAX_LAT = 35.0, 37.0
MIN_LON, MAX_LON = 71.0, 73.9

geolocator = Nominatim(user_agent="chitral_tourism_webgis_student_project")

def main():
    inserted_or_updated = 0
    found = 0
    failed = []

    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                ALTER TABLE public.tourist_attractions
                ADD COLUMN IF NOT EXISTS coordinate_source TEXT;
                ALTER TABLE public.tourist_attractions
                ADD COLUMN IF NOT EXISTS coordinate_status TEXT;
                ALTER TABLE public.tourist_attractions
                ADD COLUMN IF NOT EXISTS osm_display_name TEXT;
            """)
            conn.commit()

            for name, category, description, accessibility, season in attractions:
                print(f"\nSearching: {name}")
                query = f"{name}, Chitral, Khyber Pakhtunkhwa, Pakistan"

                try:
                    location = geolocator.geocode(
                        query,
                        country_codes="pk",
                        viewbox=[(MAX_LAT, MIN_LON), (MIN_LAT, MAX_LON)],
                        bounded=True,
                        exactly_one=True,
                        timeout=20
                    )
                    time.sleep(1.1)

                    if location is None:
                        print("No geocoding match:", name)
                        failed.append(name)
                        continue

                    lat, lon = float(location.latitude), float(location.longitude)
                    if not (MIN_LAT <= lat <= MAX_LAT and MIN_LON <= lon <= MAX_LON):
                        print("Outside study-area bounding box:", name, lat, lon)
                        failed.append(name)
                        continue

                    found += 1
                    print("Candidate:", location.address, lat, lon)

                    cur.execute("""
                        INSERT INTO public.tourist_attractions (
                            name, category, description, latitude, longitude,
                            elevation_m, accessibility, best_visit_season, geom,
                            coordinate_source, coordinate_status, osm_display_name
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, NULL, %s, %s,
                            ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                            %s, %s, %s
                        )
                        ON CONFLICT (LOWER(name)) DO UPDATE SET
                            category = EXCLUDED.category,
                            description = EXCLUDED.description,
                            latitude = EXCLUDED.latitude,
                            longitude = EXCLUDED.longitude,
                            accessibility = EXCLUDED.accessibility,
                            best_visit_season = EXCLUDED.best_visit_season,
                            geom = EXCLUDED.geom,
                            coordinate_source = EXCLUDED.coordinate_source,
                            coordinate_status = EXCLUDED.coordinate_status,
                            osm_display_name = EXCLUDED.osm_display_name,
                            updated_at = CURRENT_TIMESTAMP;
                    """, (
                        name, category, description, lat, lon,
                        accessibility, season, lon, lat,
                        "OpenStreetMap Nominatim",
                        "Needs manual verification",
                        location.address
                    ))
                    conn.commit()
                    inserted_or_updated += 1

                except GeocoderServiceError as error:
                    print("Geocoding service error:", error)
                    failed.append(name)
                    time.sleep(2)
                except Exception as error:
                    conn.rollback()
                    print("Database/import error:", error)
                    failed.append(name)

            cur.execute("SELECT COUNT(*) FROM public.tourist_attractions;")
            total = cur.fetchone()[0]

    print("\n===== CHITRAL TOURISM DATASET SUMMARY =====")
    print("Candidate locations:", len(attractions))
    print("Successfully geocoded:", found)
    print("Inserted/updated:", inserted_or_updated)
    print("Total database records:", total)
    if failed:
        print("Needs attention:", ", ".join(failed))
    print("Dataset processing completed. Verify coordinates manually.")

if __name__ == "__main__":
    main()
