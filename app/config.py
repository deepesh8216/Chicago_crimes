from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
DATABASE_URL = f"sqlite:///{(BASE_DIR / 'data' / 'database' / 'chicago_crime.db').as_posix()}"

SOURCE_FILES = {
    "crime": RAW_DATA_DIR / "chicago_crime_dataset.csv",
    "community": RAW_DATA_DIR / "chicago_city_community.csv",
    "district": RAW_DATA_DIR / "chicago_district_ps_info.csv",
    "beat": RAW_DATA_DIR / "chicago_police_beat_info.csv",
    "ward": RAW_DATA_DIR / "chicago_ward_offices.csv",
    "iucr": RAW_DATA_DIR / "iucr_codes.csv",
}

TABLES = {
    "dim_community": "community_code",
    "dim_district": "district_code",
    "dim_police_beat": "beat_num",
    "dim_ward": "ward_no",
    "dim_iucr": "iucr",
}
