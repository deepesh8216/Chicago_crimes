import pandas as pd
from pathlib import Path
from app.database import get_connection, DB_PATH


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"


def load_dimension_tables():

    connection = get_connection()

    try:

        # CSV files and their corresponding SQLite tables
        dimension_files = {
            "chicago_district_ps_info.csv": "dim_district",
            "chicago_ward_offices.csv": "dim_ward",
            "iucr_codes.csv": "dim_iucr",
            "chicago_city_community.csv": "dim_community",
            "chicago_police_beat_info.csv": "dim_police_beat"
        }

        for filename, table_name in dimension_files.items():

            # Check whether the table already contains records
            existing_count = pd.read_sql_query(
                f"SELECT COUNT(*) AS total FROM {table_name}",
                connection
            ).iloc[0, 0]

            if existing_count > 0:
                print(
                    f"Skipping {table_name}: "
                    f"already has {existing_count} records."
                )
                continue

            # Read the CSV file
            file_path = RAW_DIR / filename

            df = pd.read_csv(
                file_path,
                low_memory=False
            )

            # Standardize column names
            df.columns = (
                df.columns
                .str.strip()
                .str.lower()
                .str.replace(" ", "_")
            )

            # Clean duplicate ward records
            if table_name == "dim_ward":

                # Count non-missing values in each row
                df["completeness"] = df.notna().sum(axis=1)

                # Prefer the most complete record
                df = df.sort_values(
                    by=["ward", "completeness"],
                    ascending=[True, False]
                )

                # Keep one record per ward
                df = df.drop_duplicates(
                    subset=["ward"],
                    keep="first"
                )

                # Remove temporary column
                df = df.drop(
                    columns=["completeness"]
                )

            # Clean duplicate police beat records
            if table_name == "dim_police_beat":

                # Remove completely identical rows
                df = df.drop_duplicates(
                    keep="first"
                )

                # Keep one record per beat number
                df = df.drop_duplicates(
                    subset=["beat_num"],
                    keep="first"
                )

            # Standardize IUCR codes
            if table_name == "dim_iucr":

                df["iucr"] = (
                    df["iucr"]
                    .astype(str)
                    .str.strip()
                )

            # Insert records into SQLite
            df.to_sql(
                table_name,
                connection,
                if_exists="append",
                index=False
            )

            print(
                f"{table_name}: "
                f"{len(df)} records inserted."
            )

        connection.commit()

        print("\nAll dimension tables processed successfully.")
        print("Database location:", DB_PATH)

    except Exception as error:

        connection.rollback()

        print("\nError loading dimension data:", error)

        raise

    finally:

        connection.close()


if __name__ == "__main__":
    load_dimension_tables()