from app.crud_interface import show_crud_interface
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import calendar


# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Chicago Crime Analytics",
    page_icon="📊",
    layout="wide"
)


# =====================================================
# 2. DATABASE CONNECTION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = (
    BASE_DIR
    / "data"
    / "database"
    / "chicago_crime.db"
)


@st.cache_data
def load_crime_data():

    connection = sqlite3.connect(DB_PATH)

    query = """
        SELECT *
        FROM crimes
    """

    df = pd.read_sql_query(query, connection)

    connection.close()

    df.columns = df.columns.str.lower()

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df["arrest"] = pd.to_numeric(
        df["arrest"],
        errors="coerce"
    )

    df["community_code"] = pd.to_numeric(
        df["community_code"],
        errors="coerce"
    )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce"
    )

    df["month"] = pd.to_numeric(
        df["month"],
        errors="coerce"
    )

    return df


@st.cache_data
def load_community_data():

    connection = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(
        """
        SELECT community_code, community_name
        FROM dim_community
        """,
        connection
    )

    connection.close()

    return df


# =====================================================
# 3. LOAD DATA
# =====================================================

try:

    crime_df = load_crime_data()
    community_df = load_community_data()

except Exception as error:

    st.error(f"Database loading failed: {error}")
    st.stop()


if crime_df.empty:

    st.warning("No crime records available.")
    st.stop()


# =====================================================
# 4. TITLE
# =====================================================

st.title("Chicago Police Department Crime Analytics Dashboard")

st.markdown(
    """
    Interactive crime analysis using Python, Pandas,
    Plotly, Streamlit and SQLite3.
    """
)

st.divider()


# =====================================================
# 5. SIDEBAR FILTERS
# =====================================================

st.sidebar.header("Dashboard Filters")

year_values = sorted(
    crime_df["year"].dropna().unique().tolist()
)

selected_years = st.sidebar.multiselect(
    "Select Year",
    year_values,
    default=year_values
)

crime_types = sorted(
    crime_df["primary_type"].dropna().unique().tolist()
)

selected_crimes = st.sidebar.multiselect(
    "Select Crime Type",
    crime_types,
    default=crime_types
)

arrest_options = st.sidebar.selectbox(
    "Arrest Status",
    ["All", "Arrested", "Not Arrested"]
)

community_options = sorted(
    community_df["community_code"].dropna().tolist()
)

selected_communities = st.sidebar.multiselect(
    "Community Areas",
    community_options,
    default=community_options
)


# =====================================================
# 6. APPLY FILTERS
# =====================================================

filtered_df = crime_df.copy()

if selected_years:

    filtered_df = filtered_df[
        filtered_df["year"].isin(selected_years)
    ]

if selected_crimes:

    filtered_df = filtered_df[
        filtered_df["primary_type"].isin(selected_crimes)
    ]

if selected_communities:

    filtered_df = filtered_df[
        filtered_df["community_code"].isin(
            selected_communities
        )
    ]

if arrest_options == "Arrested":

    filtered_df = filtered_df[
        filtered_df["arrest"] == 1
    ]

elif arrest_options == "Not Arrested":

    filtered_df = filtered_df[
        filtered_df["arrest"] == 0
    ]


# =====================================================
# 7. KPI CARDS
# =====================================================

st.header("Crime Overview")

total_crimes = len(filtered_df)

total_arrests = int(
    filtered_df["arrest"].fillna(0).sum()
)

arrest_rate = (
    total_arrests / total_crimes * 100
    if total_crimes > 0 else 0
)

community_count = filtered_df[
    "community_code"
].nunique()

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Crimes",
    f"{total_crimes:,}"
)

col2.metric(
    "Total Arrests",
    f"{total_arrests:,}"
)

col3.metric(
    "Arrest Rate",
    f"{arrest_rate:.2f}%"
)

col4.metric(
    "Community Areas",
    community_count
)

st.divider()


if filtered_df.empty:

    st.warning(
        "No records match the selected filters. "
        "Please change your filters."
    )

    st.stop()


# =====================================================
# 8. YEARLY CRIME TREND
# =====================================================

st.header("1. Yearly Crime Trend")

yearly_data = (
    filtered_df
    .groupby("year")
    .size()
    .reset_index(name="crime_count")
    .sort_values("year")
)

fig_year = px.line(
    yearly_data,
    x="year",
    y="crime_count",
    markers=True,
    title="Number of Crimes by Year"
)

fig_year.update_layout(
    xaxis_title="Year",
    yaxis_title="Crime Count"
)

st.plotly_chart(
    fig_year,
    use_container_width=True
)


# =====================================================
# 9. TOP 10 CRIME CATEGORIES
# =====================================================

st.header("2. Top 10 Crime Categories")

category_data = (
    filtered_df["primary_type"]
    .value_counts()
    .head(10)
    .reset_index()
)

category_data.columns = [
    "primary_type",
    "crime_count"
]

category_data["percentage"] = (
    category_data["crime_count"]
    / total_crimes * 100
)

fig_category = px.bar(
    category_data,
    x="crime_count",
    y="primary_type",
    orientation="h",
    text="crime_count",
    title="Top 10 Crime Categories"
)

fig_category.update_layout(
    yaxis={"categoryorder": "total ascending"},
    xaxis_title="Crime Count",
    yaxis_title="Crime Category"
)

st.plotly_chart(
    fig_category,
    use_container_width=True
)

st.dataframe(
    category_data,
    use_container_width=True,
    hide_index=True
)


# =====================================================
# 10. ARREST DISTRIBUTION
# =====================================================

st.header("3. Arrest Analysis")

arrest_data = (
    filtered_df["arrest"]
    .value_counts()
    .reset_index()
)

arrest_data.columns = [
    "arrest",
    "count"
]

arrest_data["status"] = arrest_data["arrest"].map({
    1: "Arrested",
    0: "Not Arrested"
})

fig_arrest = px.pie(
    arrest_data,
    names="status",
    values="count",
    hole=0.4,
    title="Arrest vs No Arrest"
)

st.plotly_chart(
    fig_arrest,
    use_container_width=True
)


# =====================================================
# 11. MONTH AND WEEKDAY HEATMAP
# =====================================================

st.header("4. Monthly and Weekly Crime Distribution")

# Convert date to datetime
filtered_df["date"] = pd.to_datetime(
    filtered_df["date"],
    errors="coerce"
)

# Derive month and weekday directly from date
filtered_df["month_name"] = filtered_df["date"].dt.month_name()

filtered_df["weekday_name"] = filtered_df["date"].dt.day_name()

# Define correct order
month_order = [
    "January", "February", "March",
    "April", "May", "June",
    "July", "August", "September",
    "October", "November", "December"
]

weekday_order = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
]

# Calculate crime counts
heatmap_data = (
    filtered_df
    .groupby(["month_name", "weekday_name"])
    .size()
    .reset_index(name="crime_count")
)

# Create pivot table
heatmap_pivot = heatmap_data.pivot(
    index="month_name",
    columns="weekday_name",
    values="crime_count"
)

# Arrange months and weekdays
heatmap_pivot = heatmap_pivot.reindex(
    index=month_order,
    columns=weekday_order
).fillna(0)

# Generate heatmap
fig_heatmap = px.imshow(
    heatmap_pivot,
    text_auto=True,
    aspect="auto",
    color_continuous_scale="Reds",
    title="Crime Distribution by Month and Weekday",
    labels={
        "x": "Day of Week",
        "y": "Month",
        "color": "Crime Count"
    }
)

st.plotly_chart(
    fig_heatmap,
    use_container_width=True
)


# =====================================================
# 12. COMMUNITY AREA ANALYSIS
# =====================================================

st.header("5. Community Area Analysis")

community_crimes = (
    filtered_df
    .groupby("community_code")
    .size()
    .reset_index(name="crime_count")
)

community_crimes = community_crimes.merge(
    community_df,
    on="community_code",
    how="left"
)

top_communities = (
    community_crimes
    .sort_values(
        "crime_count",
        ascending=False
    )
    .head(10)
)

fig_community = px.bar(
    top_communities,
    x="crime_count",
    y="community_name",
    orientation="h",
    text="crime_count",
    title="Top 10 Community Areas by Crime Count"
)

fig_community.update_layout(
    yaxis={"categoryorder": "total ascending"}
)

st.plotly_chart(
    fig_community,
    use_container_width=True
)


# =====================================================
# 13. COMMUNITY STATISTICS
# =====================================================

st.header("6. Community Crime Statistics")

daily_community = (
    filtered_df
    .groupby(["community_code", "date"])
    .size()
    .reset_index(name="daily_crimes")
)

community_stats = (
    daily_community
    .groupby("community_code")
    .agg(
        total_crimes=("daily_crimes", "sum"),
        average_daily_crimes=("daily_crimes", "mean"),
        maximum_daily_crimes=("daily_crimes", "max")
    )
    .reset_index()
)

community_stats = community_stats.merge(
    community_df,
    on="community_code",
    how="left"
)

st.dataframe(
    community_stats.sort_values(
        "total_crimes",
        ascending=False
    ),
    use_container_width=True,
    hide_index=True
)


# =====================================================
# 14. IQR OUTLIER ANALYSIS
# =====================================================

st.header("7. Outlier Analysis")

st.markdown(
    """
    This analysis identifies community areas with unusually
    high crime counts using the Interquartile Range (IQR) method.
    """
)

# Calculate total crimes for each community area
community_counts = (
    filtered_df
    .groupby("community_code")
    .size()
    .reset_index(name="crime_count")
)

# Add community names
community_counts = community_counts.merge(
    community_df,
    on="community_code",
    how="left"
)

# Calculate quartiles
Q1 = community_counts["crime_count"].quantile(0.25)

Q3 = community_counts["crime_count"].quantile(0.75)

# Calculate IQR
IQR = Q3 - Q1

# Calculate outlier boundaries
lower_bound = Q1 - (1.5 * IQR)

upper_bound = Q3 + (1.5 * IQR)

# Identify outliers
outliers = community_counts[
    (community_counts["crime_count"] < lower_bound) |
    (community_counts["crime_count"] > upper_bound)
].copy()

# Sort outliers by crime count
outliers = outliers.sort_values(
    by="crime_count",
    ascending=False
)

# Display statistical values
col1, col2, col3 = st.columns(3)

col1.metric("Q1", f"{Q1:.2f}")

col2.metric("Q3", f"{Q3:.2f}")

col3.metric("IQR", f"{IQR:.2f}")

col4, col5 = st.columns(2)

col4.metric("Lower Bound", f"{lower_bound:.2f}")

col5.metric("Upper Bound", f"{upper_bound:.2f}")

# Create boxplot
fig_box = px.box(
    community_counts,
    y="crime_count",
    points="outliers",
    title="Crime Count Distribution Across Community Areas",
    labels={
        "crime_count": "Number of Crimes"
    }
)

fig_box.update_layout(
    yaxis_title="Crime Count",
    xaxis_title="Community Areas"
)

st.plotly_chart(
    fig_box,
    use_container_width=True
)

# Display outlier records
st.subheader("Identified Outlier Community Areas")

if not outliers.empty:

    st.dataframe(
        outliers[
            [
                "community_code",
                "community_name",
                "crime_count"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.warning(
        f"{len(outliers)} community areas have crime counts "
        f"above the upper IQR boundary of {upper_bound:.2f} "
        f"or below the lower boundary of {lower_bound:.2f}."
    )

else:

    st.success(
        "No outlier community areas were identified "
        "using the IQR method."
    )

# Analytical insight
st.subheader("Outlier Analysis Insight")

if not outliers.empty:

    highest_outlier = outliers.iloc[0]

    st.info(
        f"The community area with the highest crime count "
        f"among the identified outliers is "
        f"{highest_outlier['community_name']} "
        f"(Community Code: {int(highest_outlier['community_code'])}), "
        f"with {int(highest_outlier['crime_count'])} crimes. "
        f"The upper IQR boundary is {upper_bound:.2f} crimes. "
        f"These observations are statistically unusual and "
        f"do not necessarily indicate data errors."
    )


# =====================================================
# 15. CORRELATION ANALYSIS
# =====================================================

st.header("8. Correlation Analysis")

numeric_columns = [
    "arrest",
    "domestic",
    "year",
    "month",
    "latitude",
    "longitude"
]

numeric_df = filtered_df[
    numeric_columns
].apply(
    pd.to_numeric,
    errors="coerce"
)

correlation_matrix = numeric_df.corr()

fig_corr = px.imshow(
    correlation_matrix,
    text_auto=".2f",
    color_continuous_scale="RdBu_r",
    zmin=-1,
    zmax=1,
    title="Numeric Variable Correlation Heatmap"
)

st.plotly_chart(
    fig_corr,
    use_container_width=True
)


# =====================================================
# 16. AUTOMATED INSIGHTS
# =====================================================

st.header("9. Key Analytical Insights")

top_crime = filtered_df[
    "primary_type"
].value_counts()

if not top_crime.empty:

    most_common_crime = top_crime.index[0]

    most_common_count = top_crime.iloc[0]

    st.info(
        f"Most frequent crime category: "
        f"{most_common_crime} ({most_common_count} records)."
    )


if not yearly_data.empty:

    highest_year = yearly_data.loc[
        yearly_data["crime_count"].idxmax()
    ]

    st.info(
        f"Year with the highest number of records: "
        f"{int(highest_year['year'])} "
        f"({int(highest_year['crime_count'])} crimes)."
    )


if not top_communities.empty:

    highest_community = top_communities.iloc[0]

    st.info(
        f"Community area with the highest crime count: "
        f"{highest_community['community_name']} "
        f"({int(highest_community['crime_count'])} records)."
    )


if arrest_rate >= 0:

    st.info(
        f"Arrest rate in the selected dataset: "
        f"{arrest_rate:.2f}%."
    )


# =====================================================
# 17. DATASET PREVIEW
# =====================================================

with st.expander("View Filtered Crime Dataset"):

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )


# =====================================================
# 18. FOOTER
# =====================================================

st.divider()

st.caption(
    "Chicago Police Department Crime Analytics Capstone Project | "
    "Python | Pandas | Plotly | Streamlit | SQLite3"
)

# =====================================================
# 19. CRUD MANAGEMENT INTERFACE
# =====================================================

st.divider()

show_crud_interface()