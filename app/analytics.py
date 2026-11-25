import sqlite3

import pandas as pd
import numpy as np

from app.database import DB_PATH


# =====================================================
# DATABASE QUERY FUNCTION
# =====================================================

def read_sql(query, params=None):

    connection = sqlite3.connect(DB_PATH)

    try:

        df = pd.read_sql_query(
            query,
            connection,
            params=params or {}
        )

        return df

    finally:

        connection.close()


# =====================================================
# GET CRIME DATA
# =====================================================

def get_crimes():

    return read_sql(
        "SELECT * FROM crimes"
    )


# =====================================================
# DASHBOARD ANALYTICS
# =====================================================

def get_dashboard_data():

    # ---------------------------------------------
    # YEARLY CRIME ANALYSIS
    # ---------------------------------------------

    yearly = read_sql("""
        SELECT
            year,
            COUNT(*) AS crime_count,

            SUM(
                CASE WHEN arrest = 1 THEN 1 ELSE 0 END
            ) AS arrest_count,

            ROUND(
                100.0 *
                SUM(
                    CASE WHEN arrest = 1 THEN 1 ELSE 0 END
                ) / COUNT(*),
                2
            ) AS arrest_rate

        FROM crimes

        WHERE year IS NOT NULL

        GROUP BY year

        ORDER BY year
    """)

    # ---------------------------------------------
    # CRIME CATEGORY ANALYSIS
    # ---------------------------------------------

    categories = read_sql("""
        SELECT
            COALESCE(primary_type, 'UNKNOWN') AS primary_type,
            COUNT(*) AS crime_count,

            ROUND(
                100.0 * COUNT(*) /
                (SELECT COUNT(*) FROM crimes),
                2
            ) AS percentage

        FROM crimes

        GROUP BY primary_type

        ORDER BY crime_count DESC
    """)

    # ---------------------------------------------
    # MONTHLY CRIME ANALYSIS
    # ---------------------------------------------

    monthly = read_sql("""
        SELECT
            Month AS month,
            COUNT(*) AS crime_count

        FROM crimes

        WHERE Month IS NOT NULL

        GROUP BY Month

        ORDER BY Month
    """)

    # ---------------------------------------------
    # MONTH AND WEEKDAY ANALYSIS
    # ---------------------------------------------

    weekday_month = read_sql("""
        SELECT
            Month AS month,
            DayOfWeek AS day_of_week,
            COUNT(*) AS crime_count

        FROM crimes

        WHERE Month IS NOT NULL
          AND DayOfWeek IS NOT NULL

        GROUP BY Month, DayOfWeek

        ORDER BY Month
    """)

    # ---------------------------------------------
    # COMMUNITY AREA ANALYSIS
    # ---------------------------------------------

    communities = read_sql("""
        SELECT
            c.community_code,

            COALESCE(
                d.community_name,
                'Unknown'
            ) AS community_name,

            COUNT(*) AS crime_count

        FROM crimes c

        LEFT JOIN dim_community d

            ON CAST(c.community_code AS TEXT)
             = CAST(d.community_code AS TEXT)

        GROUP BY
            c.community_code,
            d.community_name

        ORDER BY crime_count DESC

        LIMIT 10
    """)

    # ---------------------------------------------
    # FBI CRIME CLASSIFICATION ANALYSIS
    # ---------------------------------------------

    fbi = read_sql("""
        SELECT
            fbi_code,
            COUNT(*) AS crime_count

        FROM crimes

        GROUP BY fbi_code

        ORDER BY crime_count DESC

        LIMIT 10
    """)

    # ---------------------------------------------
    # TOTAL CRIME COUNT
    # ---------------------------------------------

    total_result = read_sql("""
        SELECT COUNT(*) AS total
        FROM crimes
    """)

    total = int(
        total_result.iloc[0]["total"]
    )

    # ---------------------------------------------
    # ARREST RATE
    # ---------------------------------------------

    arrest_result = read_sql("""
        SELECT
            AVG(arrest * 1.0) AS arrest_rate

        FROM crimes

        WHERE arrest IS NOT NULL
    """)

    arrest_value = arrest_result.iloc[0]["arrest_rate"]

    arrest_rate = (
        float(arrest_value * 100)
        if pd.notna(arrest_value)
        else 0.0
    )

    # ---------------------------------------------
    # RETURN DASHBOARD DATA
    # ---------------------------------------------

    return {

        "yearly": yearly,

        "categories": categories,

        "monthly": monthly,

        "weekday_month": weekday_month,

        "communities": communities,

        "fbi": fbi,

        "total": total,

        "arrest_rate": arrest_rate

    }


# =====================================================
# STATISTICAL ANALYSIS
# =====================================================

def get_statistical_insights():

    df = get_crimes()

    result = {}

    if df.empty:

        return result

    # ---------------------------------------------
    # COMMUNITY AREA OUTLIER ANALYSIS
    # ---------------------------------------------

    if "community_code" in df.columns:

        counts = (
            df.groupby("community_code", dropna=True)
            .size()
        )

        if len(counts):

            q1 = counts.quantile(0.25)

            q3 = counts.quantile(0.75)

            iqr = q3 - q1

            upper_limit = q3 + 1.5 * iqr

            outliers = counts[
                counts > upper_limit
            ]

            result["community_outliers"] = (
                outliers.sort_values(ascending=False)
            )

            result["community_q1"] = q1

            result["community_q3"] = q3

            result["community_iqr"] = iqr

            result["community_upper_limit"] = upper_limit

        else:

            result["community_outliers"] = pd.Series(
                dtype=float
            )

    # ---------------------------------------------
    # CORRELATION ANALYSIS
    # ---------------------------------------------

    numeric = df.select_dtypes(
        include=["number"]
    )

    if not numeric.empty:

        result["correlation"] = numeric.corr(
            numeric_only=True
        )

    # ---------------------------------------------
    # CRIME CODE ANALYSIS
    # ---------------------------------------------

    if "iucr_code" in df.columns:

        result["unique_crime_codes"] = int(
            df["iucr_code"].nunique()
        )

    # ---------------------------------------------
    # MISSING VALUE ANALYSIS
    # ---------------------------------------------

    result["missing_pct"] = (
        df.isna()
        .mean()
        .mul(100)
        .round(2)
        .sort_values(ascending=False)
    )

    # ---------------------------------------------
    # HOURLY ANALYSIS
    # ---------------------------------------------

    # The current cleaned dataset does not contain
    # a reliable hour column.
    # Therefore, hourly analysis is not calculated.

    result["hour_peak"] = None

    return result


# =====================================================
# TEST ANALYTICS MODULE
# =====================================================

if __name__ == "__main__":

    print("\nCHICAGO CRIME ANALYTICS TEST")

    print("\n1. Crime Records")

    crime_data = get_crimes()

    print("Total records:", len(crime_data))

    print("\n2. Dashboard Analytics")

    dashboard = get_dashboard_data()

    print("Total crimes:", dashboard["total"])

    print(
        "Arrest rate:",
        round(dashboard["arrest_rate"], 2),
        "%"
    )

    print("\nYearly Crime Counts:")

    print(dashboard["yearly"])

    print("\nTop Crime Categories:")

    print(dashboard["categories"].head(5))

    print("\n3. Statistical Insights")

    insights = get_statistical_insights()

    print("\nCommunity Outliers:")

    print(insights.get("community_outliers"))

    print("\nUnique IUCR Codes:")

    print(insights.get("unique_crime_codes"))

    print("\nAnalytics test completed successfully.")