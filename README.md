# Chicago Crime Analytics Capstone (SQLite)

This project uses **SQLite3**, not MySQL. It implements a Python ETL pipeline, a SQLite analytical database, a Streamlit dashboard, and a FastAPI CRUD service for the five dimension tables.

## 1. Project structure

```text
chicago_crime_capstone/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── etl.py
│   ├── analytics.py
│   └── api.py
│
├── data/
│   └── raw/
│       ├── chicago_crime_dataset.csv
│       ├── chicago_city_community.csv
│       ├── chicago_district_ps_info.csv
│       ├── chicago_police_beat_info.csv
│       ├── chicago_ward_offices.csv
│       └── iucr_codes.csv
│
├── reports/
├── dashboard.py
├── requirements.txt
├── README.md
└── .gitignore
```

The master crime file is the fact source. The other five CSVs are dimensions: community, police district, police beat, ward office, and IUCR code.

## Jupyter notebooks

The `notebooks/` folder contains the step-by-step analytical notebooks. Start with
`notebooks/01_data_exploration.ipynb`. In VS Code, install/enable the Microsoft
Jupyter extension, open the notebook, select your Python environment as the kernel,
and run cells from top to bottom.

## 2. Open in VS Code

1. Extract the ZIP file.
2. In VS Code choose **File → Open Folder** and select `chicago_crime_capstone`.
3. Open Terminal → New Terminal.
4. Create and activate a virtual environment:

### Windows PowerShell
```powershell
py -m venv .venv
.venv\\Scripts\\Activate.ps1
```

If PowerShell blocks activation, use:
```powershell
.venv\\Scripts\\activate.bat
```

5. Install dependencies:
```bash
python -m pip install -r requirements.txt
```

## 3. Run the data pipeline (Use Case 1 and 4)

Run from the project root (the folder containing `dashboard.py`):
```bash
python -m app.etl
```

This creates `chicago_crime.db` in the project root and loads:
- `dim_community`
- `dim_district`
- `dim_beat`
- `dim_ward`
- `dim_iucr`
- `fact_crime`

The pipeline standardizes column names and text whitespace, parses dates, converts arrest/domestic flags to 1/0, creates `year`, `month`, `day_of_week`, and `hour`, and reports missingness. It repairs unclosed quotation marks in the final location values of the supplied crime CSV before parsing.

**Important:** The uploaded crime CSV contains a malformed quote in its last rows. The ETL loader attempts to repair an odd number of quote characters on each line so those records are not silently dropped. Inspect the ETL output and compare the source row count with the loaded `fact_crime` count.

## 4. Start the Streamlit dashboard (Use Cases 2, 3, 4 and dashboard)

Open a second terminal:
```bash
streamlit run dashboard.py
```

Streamlit will print a local address, normally `http://localhost:8501`.

The dashboard includes:
- Total crime records and overall arrest rate
- Crime count by year
- Top 10 primary crime categories
- Arrest rate by year
- Month × weekday heatmap
- Top 10 community areas
- Hourly crime distribution
- Top FBI codes and monthly counts
- Community-area IQR outlier screening
- Numeric correlation heatmap
- Missing-value summary

The dashboard is a historical analysis of the uploaded data. It is not a live crime feed.

## 5. Start the FastAPI CRUD service

Open a third terminal:
```bash
uvicorn app.api:app --reload
```

Open `http://127.0.0.1:8000/docs` in your browser. Swagger UI lets you test the API.

Supported CRUD endpoints:
- `GET /api/dimensions` — list dimension tables
- `GET /api/dimensions/{table_name}` — read rows
- `POST /api/dimensions/{table_name}` — insert a row
- `PATCH /api/dimensions/{table_name}/{record_id}` — update a row
- `DELETE /api/dimensions/{table_name}/{record_id}` — delete a row

Allowed table names:
`dim_community`, `dim_district`, `dim_beat`, `dim_ward`, `dim_iucr`.

Example POST body for `dim_community`:
```json
{
  "community_code": 999,
  "community_name": "Demo Community",
  "population": "10000",
  "area_sqmile": 1.0,
  "area_sqkm": 2.59,
  "density_per_sqmi": 10000,
  "density_per_sqkm": 3861
}
```

For PATCH and DELETE, the record ID is the dimension primary key:
- community: `community_code`
- district: `district_code`
- beat: `beat_num`
- ward: `ward_no`
- IUCR: `iucr`

## 6. Mapping to the assignment

| Assignment requirement | Project implementation |
|---|---|
| UC1: inspect, clean, engineer features, missingness | `app/etl.py` |
| UC2: trends, categories, arrests, heatmap, communities | `app/analytics.py`, `dashboard.py` |
| UC3: hourly distribution, IQR outliers, correlations | `app/analytics.py`, `dashboard.py` |
| UC4: SQLite tables, SQL aggregation, views/reporting | fact/dimension tables and SQL queries in `app/analytics.py` |
| Teacher note: SQLite3 instead of MySQL | SQLite database `chicago_crime.db` |
| Teacher note: POST, PATCH, DELETE for dimension tables | `app/api.py` |
| Teacher note: dashboard graphs and insights | `dashboard.py` |

The source PDF contains four numbered use cases. The handwritten instruction also mentions Use Case 5, but no separate Use Case 5 specification was present in the supplied PDF. The CRUD API and expanded dashboard are included to cover the additional handwritten requirements.

## 7. Submission checklist

Before submitting:
1. Run the ETL successfully.
2. Run Streamlit and capture screenshots of the dashboard.
3. Run FastAPI `/docs` and capture successful GET, POST, PATCH, and DELETE examples.
4. Keep `chicago_crime.db` after ETL; it is the SQLite database deliverable.
5. Include all `.py` files and all six source CSVs.
6. In your Word report, include project overview, schema, ETL steps, use-case questions, charts, findings, limitations, and screenshots.

## 8. Important interpretation limitation

The uploaded crime CSV is a small extract (not the full multi-year Chicago crime dataset described in the assignment). The visible sample is heavily concentrated in 2016, so year-to-year trends and arrest-rate comparisons may not be statistically representative of Chicago as a whole. State this limitation in the report and do not describe the dashboard as real-time.
