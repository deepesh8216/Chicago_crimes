import pandas as pd
import numpy as np
from sqlalchemy import text
from app.database import engine

def read_sql(query, params=None):
    with engine.connect() as conn:
        return pd.read_sql_query(text(query), conn, params=params or {})

def get_crimes():
    return read_sql("SELECT * FROM fact_crime")

def get_dashboard_data():
    yearly = read_sql("""
        SELECT year, COUNT(*) AS crime_count,
               SUM(CASE WHEN arrest=1 THEN 1 ELSE 0 END) AS arrest_count,
               ROUND(100.0 * SUM(CASE WHEN arrest=1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS arrest_rate
        FROM fact_crime WHERE year IS NOT NULL GROUP BY year ORDER BY year
    """)
    categories = read_sql("""
        SELECT COALESCE(i.primary_type, 'UNKNOWN') AS primary_type, COUNT(*) AS crime_count
        FROM fact_crime c LEFT JOIN dim_iucr i ON CAST(c.iucr_code AS TEXT)=CAST(i.iucr AS TEXT)
        GROUP BY COALESCE(i.primary_type, 'UNKNOWN')
        ORDER BY crime_count DESC
    """)
    monthly = read_sql("""
        SELECT month, COUNT(*) AS crime_count FROM fact_crime
        WHERE month IS NOT NULL GROUP BY month ORDER BY month
    """)
    weekday_month = read_sql("""
        SELECT month, day_of_week, COUNT(*) AS crime_count FROM fact_crime
        WHERE month IS NOT NULL AND day_of_week IS NOT NULL
        GROUP BY month, day_of_week
    """)
    communities = read_sql("""
        SELECT c.community_code, COALESCE(d.community_name, 'Unknown') AS community_name,
               COUNT(*) AS crime_count
        FROM fact_crime c LEFT JOIN dim_community d
          ON CAST(c.community_code AS TEXT)=CAST(d.community_code AS TEXT)
        GROUP BY c.community_code, d.community_name ORDER BY crime_count DESC LIMIT 10
    """)
    hourly = read_sql("""
        SELECT hour, COUNT(*) AS crime_count FROM fact_crime
        WHERE hour IS NOT NULL GROUP BY hour ORDER BY hour
    """)
    fbi = read_sql("""
        SELECT fbi_code, COUNT(*) AS crime_count FROM fact_crime
        GROUP BY fbi_code ORDER BY crime_count DESC LIMIT 10
    """)
    total = read_sql("SELECT COUNT(*) AS n FROM fact_crime").iloc[0, 0]
    arrest = read_sql("SELECT AVG(CASE WHEN arrest IS NOT NULL THEN arrest * 1.0 END) AS rate FROM fact_crime").iloc[0, 0]
    return {
        "yearly": yearly, "categories": categories, "monthly": monthly,
        "weekday_month": weekday_month, "communities": communities,
        "hourly": hourly, "fbi": fbi, "total": int(total or 0),
        "arrest_rate": float(arrest * 100) if pd.notna(arrest) else 0.0
    }

def get_statistical_insights():
    df = get_crimes()
    result = {}
    if not df.empty:
        counts = df.groupby("community_code", dropna=True).size()
        q1, q3 = counts.quantile([0.25, 0.75]) if len(counts) else (np.nan, np.nan)
        iqr = q3 - q1
        outliers = counts[counts > q3 + 1.5 * iqr] if len(counts) else pd.Series(dtype=float)
        result["community_outliers"] = outliers.sort_values(ascending=False)
        numeric = df.select_dtypes(include=["number"]).corr(numeric_only=True)
        result["correlation"] = numeric
        result["hour_peak"] = int(df["hour"].mode().iloc[0]) if df["hour"].notna().any() else None
        result["unique_crime_codes"] = int(df["iucr_code"].nunique())
        result["missing_pct"] = (df.isna().mean() * 100).round(2).sort_values(ascending=False)
    return result
