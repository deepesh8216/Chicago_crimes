import sqlite3
from pathlib import Path

# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Central database directory
DB_DIR = BASE_DIR / "data" / "database"

# Create database directory if it does not exist
DB_DIR.mkdir(parents=True, exist_ok=True)

# Single SQLite database path
DB_PATH = DB_DIR / "chicago_crime.db"


def get_connection():

    connection = sqlite3.connect(DB_PATH)

    # Enable foreign key support
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def create_crimes_table():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crimes (
            id INTEGER PRIMARY KEY,
            case_number TEXT,
            date TEXT,
            block TEXT,
            iucr_code TEXT,
            primary_type TEXT,
            location_desc TEXT,
            arrest INTEGER,
            domestic INTEGER,
            beat_num INTEGER,
            district_code INTEGER,
            ward_no INTEGER,
            community_code INTEGER,
            fbi_code TEXT,
            x_coordinate REAL,
            y_coordinate REAL,
            year INTEGER,
            date_of_update TEXT,
            latitude REAL,
            longitude REAL,
            location TEXT,
            Month INTEGER,
            DayOfWeek TEXT
        )
    """)

    connection.commit()
    connection.close()
