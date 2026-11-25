import sqlite3
from pathlib import Path

import pandas as pd

from app.database import DB_PATH
from app.config import BASE_DIR


# =====================================================
# FILE CONFIGURATION
# =====================================================

CLEANED_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "chicago_crime_cleaned.csv"
)


# =====================================================
# LOAD CLEANED CRIME DATA
# =====================================================

def load_crime_data():

    print("Reading cleaned Chicago crime dataset...")

    if not CLEANED_FILE.exists():
        raise FileNotFoundError(
            f"Cleaned CSV not found: {CLEANED_FILE}"
        )

    df = pd.read_csv(CLEANED_FILE)

    print("Original dataset shape:", df.shape)

    # Remove duplicate Year column.
    # SQLite column names are case-insensitive.
    if "Year" in df.columns and "year" in df.columns:
        df = df.drop(columns=["Year"])

    # Standardize boolean columns.
    for column in ["arrest", "domestic"]:

        if column in df.columns:

            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
                .str.lower()
                .map({
                    "true": 1,
                    "false": 0,
                    "1": 1,
                    "0": 0,
                    "yes": 1,
                    "no": 0
                })
            )

            df[column] = df[column].fillna(0).astype(int)

    # Convert date column.
    if "date" in df.columns:

        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        ).astype("string")

    # Convert numeric columns.
    numeric_columns = [
        "id",
        "beat_num",
        "district_code",
        "ward_no",
        "community_code",
        "year",
        "Month",
        "x_coordinate",
        "y_coordinate",
        "latitude",
        "longitude"
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    return df


# =====================================================
# LOAD DATA INTO SQLITE
# =====================================================

def load_database(df):

    print("Connecting to SQLite database...")

    connection = sqlite3.connect(DB_PATH)

    try:

        # Load the cleaned crime data.
        # This replaces only the crimes table.
        df.to_sql(
            "crimes",
            connection,
            if_exists="replace",
            index=False
        )

        connection.commit()

        print("Crime data loaded successfully.")

        cursor = connection.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM crimes"
        )

        total_records = cursor.fetchone()[0]

        print("Total crime records:", total_records)

    finally:

        connection.close()


# =====================================================
# CREATE REPORTING VIEWS
# =====================================================

def create_reporting_views():

    print("Creating SQL reporting views...")

    connection = sqlite3.connect(DB_PATH)

    try:

        cursor = connection.cursor()

        # ---------------------------------------------
        # YEARLY CRIME REPORT
        # ---------------------------------------------

        cursor.execute(
            "DROP VIEW IF EXISTS vw_crime_yearly"
        )

        cursor.execute("""
            CREATE VIEW vw_crime_yearly AS

            SELECT
                year,
                COUNT(*) AS crime_count,

                SUM(
                    CASE
                        WHEN arrest = 1 THEN 1
                        ELSE 0
                    END
                ) AS arrest_count,

                ROUND(
                    100.0 *
                    SUM(
                        CASE
                            WHEN arrest = 1 THEN 1
                            ELSE 0
                        END
                    ) / COUNT(*),
                    2
                ) AS arrest_percentage

            FROM crimes

            WHERE year IS NOT NULL

            GROUP BY year

            ORDER BY year
        """)

        # ---------------------------------------------
        # CRIME CATEGORY REPORT
        # ---------------------------------------------

        cursor.execute(
            "DROP VIEW IF EXISTS vw_crime_by_category"
        )

        cursor.execute("""
            CREATE VIEW vw_crime_by_category AS

            SELECT
                primary_type,

                COUNT(*) AS crime_count,

                ROUND(
                    100.0 * COUNT(*) /
                    (SELECT COUNT(*) FROM crimes),
                    2
                ) AS percentage,

                SUM(
                    CASE
                        WHEN arrest = 1 THEN 1
                        ELSE 0
                    END
                ) AS arrest_count

            FROM crimes

            GROUP BY primary_type

            ORDER BY crime_count DESC
        """)

        connection.commit()

        print("Reporting views created successfully.")

    finally:

        connection.close()


# =====================================================
# VERIFY DATABASE TABLES
# =====================================================

def verify_database():

    connection = sqlite3.connect(DB_PATH)

    try:

        cursor = connection.cursor()

        tables = [
            "crimes",
            "dim_district",
            "dim_ward",
            "dim_iucr",
            "dim_community",
            "dim_police_beat"
        ]

        print("\nDATABASE VALIDATION")
        print("-------------------")

        for table in tables:

            cursor.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                AND name = ?
                """,
                (table,)
            )

            exists = cursor.fetchone()

            if exists:

                cursor.execute(
                    f'SELECT COUNT(*) FROM "{table}"'
                )

                count = cursor.fetchone()[0]

                print(f"{table}: {count} records")

            else:

                print(f"WARNING: {table} does not exist.")

        views = [
            "vw_crime_yearly",
            "vw_crime_by_category"
        ]

        print("\nREPORTING VIEWS")
        print("----------------")

        for view in views:

            cursor.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'view'
                AND name = ?
                """,
                (view,)
            )

            if cursor.fetchone():

                print(f"{view}: Available")

            else:

                print(f"{view}: Missing")

    finally:

        connection.close()


# =====================================================
# RUN ETL PIPELINE
# =====================================================

def run_pipeline():

    print("\n================================")
    print("CHICAGO CRIME ETL PIPELINE")
    print("================================\n")

    # Step 1: Read cleaned data.
    df = load_crime_data()

    # Step 2: Load into SQLite.
    load_database(df)

    # Step 3: Create reporting views.
    create_reporting_views()

    # Step 4: Validate database.
    verify_database()

    print("\n================================")
    print("ETL PIPELINE COMPLETED")
    print("================================")

    return df


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    cleaned_data = run_pipeline()

    print("\nFinal dataset information:")

    print("Rows:", len(cleaned_data))

    print("Columns:", len(cleaned_data.columns))

    print("\nMissing values:")

    print(
        cleaned_data.isnull()
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )