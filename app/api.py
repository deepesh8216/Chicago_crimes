from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Body, Query
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError


# --------------------------------------------------
# 1. DATABASE CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "data" / "database" / "chicago_crime.db"

DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


# --------------------------------------------------
# 2. FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="Chicago Police Department Crime Analytics API",
    description="CRUD API for Chicago Police Department dimension tables",
    version="1.0.0"
)


# --------------------------------------------------
# 3. DIMENSION TABLE CONFIGURATION
# --------------------------------------------------

DIMENSION_TABLES = {

    "district": {
        "table": "dim_district",
        "primary_key": "district_code",
        "key_type": int,
        "crime_column": "district_code",
        "columns": [
            "district_code",
            "district_name",
            "address",
            "city",
            "state",
            "zip",
            "website",
            "phone",
            "fax",
            "tty",
            "x_coordinate",
            "y_coordinate",
            "latitude",
            "longitude",
            "location"
        ]
    },

    "ward": {
        "table": "dim_ward",
        "primary_key": "ward",
        "key_type": int,
        "crime_column": "ward_no",
        "columns": [
            "ward",
            "alderman",
            "address",
            "city",
            "state",
            "zipcode",
            "ward_phone",
            "ward_fax",
            "email",
            "website",
            "location_zip",
            "location_city",
            "location",
            "location_address",
            "location_state",
            "city_hall_address",
            "city_hall_city",
            "city_hall_state",
            "city_hall_zipcode",
            "city_hall_phone"
        ]
    },

    "iucr": {
        "table": "dim_iucr",
        "primary_key": "iucr",
        "key_type": str,
        "crime_column": "iucr_code",
        "columns": [
            "iucr",
            "primary_type",
            "description",
            "index_code"
        ]
    },

    "community": {
        "table": "dim_community",
        "primary_key": "community_code",
        "key_type": int,
        "crime_column": "community_code",
        "columns": [
            "community_code",
            "community_name",
            "population",
            "area_sqmile",
            "area_sqkm",
            "density_per_sqmi",
            "density_per_sqkm"
        ]
    },

    "police_beat": {
        "table": "dim_police_beat",
        "primary_key": "beat_num",
        "key_type": int,
        "crime_column": "beat_num",
        "columns": [
            "beat_num",
            "district",
            "sector",
            "beat"
        ]
    }
}


# --------------------------------------------------
# 4. HELPER FUNCTION
# --------------------------------------------------

def get_dimension_config(dimension_name):

    if dimension_name not in DIMENSION_TABLES:
        raise HTTPException(
            status_code=404,
            detail="Dimension table not found."
        )

    return DIMENSION_TABLES[dimension_name]


def convert_record_key(config, record_id):

    try:
        return config["key_type"](record_id)

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid record ID."
        )


# --------------------------------------------------
# 5. HOME ENDPOINT
# --------------------------------------------------

@app.get("/")
def home():

    return {
        "message": "Chicago Police Department Crime Analytics API",
        "database": "SQLite",
        "available_dimensions": list(DIMENSION_TABLES.keys()),
        "operations": ["GET", "POST", "PATCH", "DELETE"]
    }


# --------------------------------------------------
# 6. GET ALL RECORDS
# --------------------------------------------------

@app.get("/api/{dimension_name}")
def get_all_records(
    dimension_name: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0)
):

    config = get_dimension_config(dimension_name)

    query = text(
        f"""
        SELECT *
        FROM {config['table']}
        LIMIT :limit OFFSET :offset
        """
    )

    with engine.connect() as connection:

        result = connection.execute(
            query,
            {"limit": limit, "offset": offset}
        )

        records = [
            dict(row._mapping)
            for row in result
        ]

    return {
        "dimension": dimension_name,
        "count": len(records),
        "records": records
    }


# --------------------------------------------------
# 7. GET ONE RECORD
# --------------------------------------------------

@app.get("/api/{dimension_name}/{record_id}")
def get_one_record(
    dimension_name: str,
    record_id: str
):

    config = get_dimension_config(dimension_name)

    key = convert_record_key(config, record_id)

    query = text(
        f"""
        SELECT *
        FROM {config['table']}
        WHERE {config['primary_key']} = :record_id
        """
    )

    with engine.connect() as connection:

        result = connection.execute(
            query,
            {"record_id": key}
        ).fetchone()

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Record not found."
        )

    return dict(result._mapping)


# --------------------------------------------------
# 8. POST - CREATE RECORD
# --------------------------------------------------

@app.post("/api/{dimension_name}", status_code=201)
def create_record(
    dimension_name: str,
    record: dict[str, Any] = Body(...)
):

    config = get_dimension_config(dimension_name)

    allowed_columns = config["columns"]
    primary_key = config["primary_key"]

    # Check for unknown fields
    invalid_columns = set(record.keys()) - set(allowed_columns)

    if invalid_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid columns: {list(invalid_columns)}"
        )

    # Primary key is required
    if primary_key not in record or record[primary_key] is None:
        raise HTTPException(
            status_code=400,
            detail=f"{primary_key} is required."
        )

    if record[primary_key] == "":
        raise HTTPException(
            status_code=400,
            detail=f"{primary_key} cannot be empty."
        )

    # Prepare SQL query
    columns = list(record.keys())

    column_names = ", ".join(columns)

    placeholders = ", ".join(
        [f":{column}" for column in columns]
    )

    query = text(
        f"""
        INSERT INTO {config['table']}
        ({column_names})
        VALUES ({placeholders})
        """
    )

    try:

        with engine.begin() as connection:

            connection.execute(
                query,
                record
            )

        return {
            "message": "Record created successfully.",
            "dimension": dimension_name,
            "record": record
        }

    except IntegrityError:

        raise HTTPException(
            status_code=409,
            detail="Duplicate primary key or database constraint violation."
        )


# --------------------------------------------------
# 9. PATCH - UPDATE RECORD
# --------------------------------------------------

@app.patch("/api/{dimension_name}/{record_id}")
def update_record(
    dimension_name: str,
    record_id: str,
    updates: dict[str, Any] = Body(...)
):

    config = get_dimension_config(dimension_name)

    primary_key = config["primary_key"]

    allowed_columns = set(config["columns"]) - {primary_key}

    # Reject unknown fields and primary-key changes
    invalid_columns = set(updates.keys()) - allowed_columns

    if invalid_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid or non-editable columns: {list(invalid_columns)}"
        )

    if not updates:
        raise HTTPException(
            status_code=400,
            detail="At least one field is required."
        )

    key = convert_record_key(config, record_id)

    set_clause = ", ".join(
        [f"{column} = :{column}" for column in updates]
    )

    query = text(
        f"""
        UPDATE {config['table']}
        SET {set_clause}
        WHERE {primary_key} = :record_id
        """
    )

    parameters = dict(updates)
    parameters["record_id"] = key

    try:

        with engine.begin() as connection:

            result = connection.execute(
                query,
                parameters
            )

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="Record not found."
                )

        return {
            "message": "Record updated successfully.",
            "dimension": dimension_name,
            "record_id": key,
            "updated_fields": updates
        }

    except IntegrityError:

        raise HTTPException(
            status_code=409,
            detail="Database constraint violation."
        )


# --------------------------------------------------
# 10. DELETE - DELETE RECORD
# --------------------------------------------------

@app.delete("/api/{dimension_name}/{record_id}")
def delete_record(
    dimension_name: str,
    record_id: str
):

    config = get_dimension_config(dimension_name)

    key = convert_record_key(config, record_id)

    # Check whether crime records reference this dimension record
    reference_query = text(
        f"""
        SELECT COUNT(*)
        FROM crimes
        WHERE {config['crime_column']} = :record_id
        """
    )

    delete_query = text(
        f"""
        DELETE FROM {config['table']}
        WHERE {config['primary_key']} = :record_id
        """
    )

    with engine.begin() as connection:

        references = connection.execute(
            reference_query,
            {"record_id": key}
        ).scalar_one()

        if references > 0:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Cannot delete this record. "
                    f"It is referenced by {references} crime records."
                )
            )

        result = connection.execute(
            delete_query,
            {"record_id": key}
        )

        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Record not found."
            )

    return {
        "message": "Record deleted successfully.",
        "dimension": dimension_name,
        "record_id": key
    }


# --------------------------------------------------
# 11. RUN APPLICATION
# --------------------------------------------------

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )