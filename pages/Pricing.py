import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(
    page_title="Pricing",
    layout="wide"
)

st.title("Coal Pricing")

# =========================================================
# LOAD DATA
# =========================================================

DATA_FILE = "dataset/Coal_01_02_26-01_03_22.csv"

df = pd.read_csv(DATA_FILE)

# =========================================================
# BASIC VALIDATION
# =========================================================

required_cols = ["Date", "Close"]
missing = [c for c in required_cols if c not in df.columns]

if missing:
    st.error(f"Missing required columns: {missing}")
    st.stop()

# =========================================================
# DATE PARSING (CRITICAL)
# =========================================================

df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df = df.dropna(subset=["Date", "Close"])

df["year"] = df["Date"].dt.year
df["month"] = df["Date"].dt.month
df["month_name"] = df["Date"].dt.strftime("%b")

# =========================================================
# YEAR FILTER
# =========================================================

years = sorted(df["year"].unique())
year = st.selectbox("Year", years)

filtered = df[df["year"] == year]

# =========================================================
# AGGREGATION — AVERAGE PRICE PER MONTH
# =========================================================

monthly_avg = (
    filtered
    .groupby(["year", "month", "month_name"], as_index=False)
    .agg(avg_close=("Close", "mean"))
    .sort_values("month")
)

# =========================================================
# LINE CHART
# =========================================================

line_chart = (
    alt.Chart(monthly_avg)
    .mark_line(point=True)
    .encode(
        x=alt.X(
            "month_name:N",
            title="Month",
            sort=[
                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
            ]
        ),
        y=alt.Y(
            "avg_close:Q",
            title="Average Close Price"
        ),
        tooltip=[
            alt.Tooltip("month_name:N", title="Month"),
            alt.Tooltip("avg_close:Q", title="Avg Price", format=".2f")
        ]
    )
    .properties(
        title=f"Average Monthly Coal Price — {year}"
    )
)

st.altair_chart(line_chart, use_container_width=True)

# =========================================================
# OPTIONAL: SHOW DATA
# =========================================================

with st.expander("Show aggregated data"):
    st.dataframe(
        monthly_avg,
        use_container_width=True
    )
