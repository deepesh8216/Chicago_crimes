import pandas as pd

from app.database import get_connection, DB_PATH
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

CLEANED_FILE = (
    BASE_DIR / "data" / "processed" /
    "chicago_crime_cleaned.csv"
)


def load_crimes():

    # Read cleaned dataset
    df = pd.read_csv(CLEANED_FILE)

    # Remove duplicate Year column
    if "Year" in df.columns and "year" in df.columns:
        df = df.drop(columns=["Year"])

    # Convert boolean columns to integers
    df["arrest"] = df["arrest"].astype(int)
    df["domestic"] = df["domestic"].astype(int)

    print("Columns prepared:", len(df.columns))

    connection = get_connection()

    try:
        df.to_sql(
            "crimes",
            connection,
            if_exists="replace",
            index=False
        )

        count = pd.read_sql_query(
            "SELECT COUNT(*) AS total FROM crimes",
            connection
        )

        print("\nData loaded successfully.")
        print("Records inserted:", count.iloc[0, 0])
        print("Database:", DB_PATH)

    finally:
        connection.close()


if __name__ == "__main__":
    load_crimes()