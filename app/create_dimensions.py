import sqlite3
from app.database import get_connection


def create_dimension_tables():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # 1. Police District Dimension
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dim_district (
                district_code INTEGER PRIMARY KEY,
                district_name TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                zip TEXT,
                website TEXT,
                phone TEXT,
                fax TEXT,
                tty TEXT,
                x_coordinate REAL,
                y_coordinate REAL,
                latitude REAL,
                longitude REAL,
                location TEXT
            )
        """)

        # 2. Ward Dimension
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dim_ward (
                ward INTEGER PRIMARY KEY,
                alderman TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                zipcode TEXT,
                ward_phone TEXT,
                ward_fax TEXT,
                email TEXT,
                website TEXT,
                location_zip TEXT,
                location_city TEXT,
                location TEXT,
                location_address TEXT,
                location_state TEXT,
                city_hall_address TEXT,
                city_hall_city TEXT,
                city_hall_state TEXT,
                city_hall_zipcode TEXT,
                city_hall_phone TEXT
            )
        """)

        # 3. IUCR Dimension
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dim_iucr (
                iucr TEXT PRIMARY KEY,
                primary_type TEXT,
                description TEXT,
                index_code TEXT
            )
        """)

        # 4. Community Area Dimension
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dim_community (
                community_code INTEGER PRIMARY KEY,
                community_name TEXT,
                population INTEGER,
                area_sqmile REAL,
                area_sqkm REAL,
                density_per_sqmi REAL,
                density_per_sqkm REAL
            )
        """)

        # 5. Police Beat Dimension
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dim_police_beat (
                beat_num INTEGER PRIMARY KEY,
                district INTEGER,
                sector INTEGER,
                beat INTEGER
            )
        """)

        connection.commit()
        print("All five dimension tables created successfully.")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    create_dimension_tables()