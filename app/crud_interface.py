import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


# =====================================================
# DATABASE CONFIGURATION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "data" / "database" / "chicago_crime.db"


DIMENSION_TABLES = {
    "District": "dim_district",
    "Ward": "dim_ward",
    "IUCR": "dim_iucr",
    "Community": "dim_community",
    "Police Beat": "dim_police_beat"
}


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# =====================================================
# GET TABLE STRUCTURE
# =====================================================

def get_table_info(table_name):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(f"PRAGMA table_info({table_name})")

        columns = cursor.fetchall()

        return columns

    finally:
        connection.close()


# =====================================================
# GET PRIMARY KEY
# =====================================================

def get_primary_key(table_name):

    columns = get_table_info(table_name)

    for column in columns:

        if column[5] == 1:
            return column[1]

    return None


# =====================================================
# READ RECORDS
# =====================================================

def read_records(table_name):

    connection = get_connection()

    try:

        df = pd.read_sql_query(
            f'SELECT * FROM "{table_name}"',
            connection
        )

        return df

    finally:
        connection.close()


# =====================================================
# CONVERT INPUT VALUE
# =====================================================

def convert_value(value, column_type):

    if value == "":
        return None

    column_type = column_type.upper()

    if "INT" in column_type:
        return int(value)

    if any(
        item in column_type
        for item in ["REAL", "FLOAT", "DOUBLE"]
    ):
        return float(value)

    return value


# =====================================================
# DISPLAY CRUD INTERFACE
# =====================================================

def show_crud_interface():

    st.header("Dimension Table Management")

    st.write(
        "Manage the five dimension tables stored in the "
        "Chicago Crime SQLite database."
    )

    selected_dimension = st.selectbox(
        "Select Dimension Table",
        list(DIMENSION_TABLES.keys())
    )

    table_name = DIMENSION_TABLES[selected_dimension]

    primary_key = get_primary_key(table_name)

    if primary_key is None:

        st.error(
            "No primary key found for this table. "
            "CRUD operations cannot continue."
        )

        return

    # =================================================
    # DISPLAY CURRENT RECORDS
    # =================================================

    st.subheader(f"{selected_dimension} Records")

    records = read_records(table_name)

    st.dataframe(
        records,
        use_container_width=True,
        hide_index=True
    )

    st.caption(f"Total records: {len(records)}")

    # =================================================
    # CRUD TABS
    # =================================================

    view_tab, add_tab, update_tab, delete_tab = st.tabs(
        ["View Records", "Add Record", "Update Record", "Delete Record"]
    )

    # =================================================
    # VIEW
    # =================================================

    with view_tab:

        st.subheader("View Records")

        st.dataframe(
            records,
            use_container_width=True,
            hide_index=True
        )

    # =================================================
    # ADD
    # =================================================

    with add_tab:

        st.subheader(f"Add New {selected_dimension} Record")

        columns = get_table_info(table_name)

        with st.form(f"add_record_form_{table_name}"):

            new_values = {}

            for column in columns:

                column_name = column[1]
                column_type = column[2]

                # Include the primary key in the form.
                new_values[column_name] = st.text_input(
                    column_name.replace("_", " ").title(),
                    key=f"add_{table_name}_{column_name}"
                )

            submitted = st.form_submit_button("Add Record")

            if submitted:

                connection = None

                try:

                    column_names = list(new_values.keys())

                    # Convert input values according to SQLite column types.
                    values = []

                    for column_name in column_names:

                        column_type = next(
                            col[2]
                            for col in columns
                            if col[1] == column_name
                        )

                        values.append(
                            convert_value(
                                new_values[column_name],
                                column_type
                            )
                        )

                    # Check that the primary key has been entered.
                    primary_key_index = column_names.index(primary_key)

                    if values[primary_key_index] is None:

                        st.error(
                            f"{primary_key} is required."
                        )

                    else:

                        placeholders = ", ".join(
                            ["?"] * len(column_names)
                        )

                        columns_sql = ", ".join(
                            f'"{column}"'
                            for column in column_names
                        )

                        query = (
                            f'INSERT INTO "{table_name}" '
                            f'({columns_sql}) '
                            f'VALUES ({placeholders})'
                        )

                        connection = get_connection()

                        connection.execute(query, values)

                        connection.commit()

                        st.success(
                            "Record added successfully."
                        )

                        st.cache_data.clear()

                except Exception as error:

                    st.error(
                        f"Unable to add record: {error}"
                    )

                finally:

                    if connection is not None:
                        connection.close()

    # =================================================
    # UPDATE
    # =================================================

    with update_tab:

        st.subheader(f"Update {selected_dimension} Record")

        records = read_records(table_name)

        if records.empty:

            st.info("No records available to update.")

        else:

            record_ids = records[primary_key].dropna().tolist()

            selected_id = st.selectbox(
                "Select Record ID",
                record_ids,
                key=f"update_id_{table_name}"
            )

            selected_record = records[
                records[primary_key] == selected_id
            ].iloc[0]

            columns = get_table_info(table_name)

            with st.form(f"update_form_{table_name}"):

                updated_values = {}

                for column in columns:

                    column_name = column[1]
                    column_type = column[2]

                    if column[5] == 1:
                        continue

                    current_value = selected_record[column_name]

                    if pd.isna(current_value):
                        current_value = ""
                    else:
                        current_value = str(current_value)

                    updated_values[column_name] = st.text_input(
                        column_name.replace("_", " ").title(),
                        value=current_value,
                        key=f"update_{table_name}_{column_name}"
                    )

                update_button = st.form_submit_button(
                    "Save Changes"
                )

                if update_button:

                    try:

                        set_clause = ", ".join(
                            f'"{column}" = ?'
                            for column in updated_values
                        )

                        values = []

                        for column in updated_values:

                            column_type = next(
                                col[2]
                                for col in columns
                                if col[1] == column
                            )

                            values.append(
                                convert_value(
                                    updated_values[column],
                                    column_type
                                )
                            )

                        values.append(selected_id)

                        query = (
                            f'UPDATE "{table_name}" '
                            f'SET {set_clause} '
                            f'WHERE "{primary_key}" = ?'
                        )

                        connection = get_connection()

                        try:

                            connection.execute(query, values)
                            connection.commit()

                            st.success(
                                "Record updated successfully."
                            )

                            st.cache_data.clear()

                        finally:
                            connection.close()

                    except Exception as error:

                        st.error(
                            f"Unable to update record: {error}"
                        )

    # =================================================
    # DELETE
    # =================================================

    with delete_tab:

        st.subheader(f"Delete {selected_dimension} Record")

        records = read_records(table_name)

        if records.empty:

            st.info("No records available to delete.")

        else:

            record_ids = records[primary_key].dropna().tolist()

            selected_id = st.selectbox(
                "Select Record to Delete",
                record_ids,
                key=f"delete_id_{table_name}"
            )

            selected_record = records[
                records[primary_key] == selected_id
            ]

            st.write("Selected record:")

            st.dataframe(
                selected_record,
                use_container_width=True,
                hide_index=True
            )

            confirm_delete = st.checkbox(
                "I confirm that I want to delete this record.",
                key=f"confirm_{table_name}"
            )

            if st.button(
                "Delete Record",
                key=f"delete_button_{table_name}"
            ):

                if not confirm_delete:

                    st.warning(
                        "Please confirm before deleting."
                    )

                else:

                    # Protect dimension records referenced by crimes
                    reference_columns = {
                        "dim_district": ("district_code", "district_code"),
                        "dim_ward": ("ward", "ward_no"),
                        "dim_iucr": ("iucr", "iucr_code"),
                        "dim_community": ("community_code", "community_code"),
                        "dim_police_beat": ("beat_num", "beat_num")
                    }

                    dimension_column, crime_column = (
                        reference_columns[table_name]
                    )

                    connection = get_connection()

                    try:

                        cursor = connection.cursor()

                        cursor.execute(
                            f'SELECT COUNT(*) FROM crimes '
                            f'WHERE "{crime_column}" = ?',
                            (selected_id,)
                        )

                        reference_count = cursor.fetchone()[0]

                        if reference_count > 0:

                            st.error(
                                f"Cannot delete this record. "
                                f"It is referenced by "
                                f"{reference_count} crime records."
                            )

                        else:

                            cursor.execute(
                                f'DELETE FROM "{table_name}" '
                                f'WHERE "{primary_key}" = ?',
                                (selected_id,)
                            )

                            connection.commit()

                            st.success(
                                "Record deleted successfully."
                            )

                            st.cache_data.clear()

                    except Exception as error:

                        st.error(
                            f"Unable to delete record: {error}"
                        )

                    finally:
                        connection.close()