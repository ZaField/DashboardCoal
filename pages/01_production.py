import streamlit as st
import pandas as pd
import altair as alt
from data_loader import load_facility_data

st.set_page_config(
    page_title="Production",
    layout="wide"
)

st.title("Production")

# =========================================================
# LOAD DATA
# =========================================================

# Facility from GPKG
facility_gdf, _ = load_facility_data()

# CSV tables
coal_df = pd.read_csv("dataset/coal.csv")
material_df = pd.read_csv("dataset/material_ids.csv")

# =========================================================
# NORMALIZE JOIN KEYS (CRITICAL)
# =========================================================
facility_gdf["facility_id"] = facility_gdf["facility_id"].astype(str)
coal_df["facility_id"] = coal_df["facility_id"].astype(str)
coal_df["material"] = coal_df["material"].astype(str)
material_df["material_id"] = material_df["material_id"].astype(str)

# =========================================================
# SQL-EQUIVALENT JOIN
# =========================================================
production_df = (
    coal_df
    .merge(
        facility_gdf.drop(columns="geometry"),
        on="facility_id",
        how="left"
    )
    .merge(
        material_df,
        left_on="material",
        right_on="material_id",
        how="left"
    )
)

# =========================================================
# SELECT + RENAME (MATCH SQL)
# =========================================================
production_df = production_df[[
    "facility_id",
    "facility_name",
    "facility_type",
    "primary_commodity",
    "commodities_products",
    "facility_equipment",
    "country",

    "year",
    "type",
    "material",
    "material_name",
    "material_category",
    "material_category_2",

    "value_tonnes",
    "amount_sold_tonnes"
]].rename(columns={
    "type": "coal_process_type",
    "material": "material_id"
})

production_df["coal_process_type"] = (
    production_df["coal_process_type"]
    .str.strip()
    .str.lower()
)

production_df = production_df.sort_values(
    ["facility_name", "year", "coal_process_type"]
)

production_df = production_df.reset_index(drop=True)
production_df.index = production_df.index + 1
production_df.index.name = "No"

countries = sorted(
    production_df["country"]
    .dropna()
    .unique()
)

country = st.selectbox("Country", countries)

filtered = (
    production_df[production_df["country"] == country]
    .reset_index(drop=True)
)

filtered.index = filtered.index + 1
filtered.index.name = "No"

# =========================================================
# CHART DATA — BAR (Coal mined by commodities_products)
# =========================================================

bar_df = (
    filtered[filtered["coal_process_type"] == "Coal mined"]
    .groupby("commodities_products", as_index=False)
    .agg(total_tonnes=("value_tonnes", "sum"))
    .sort_values("total_tonnes", ascending=False)
)

product_df = (
    filtered[filtered["coal_process_type"] == "coal mined"]
    .assign(
        commodity_product=lambda df:
            df["commodities_products"]
            .str.split(",")
    )
    .explode("commodity_product")
)

product_df["commodity_product"] = (
    product_df["commodity_product"]
    .str.strip()
)

bar_df = (
    product_df
    .groupby("commodity_product", as_index=False)
    .agg(
        facility_count=("facility_id", "nunique")
    )
    .sort_values("facility_count", ascending=False)
)


bar_chart = (
    alt.Chart(bar_df)
    .mark_bar()
    .encode(
        x=alt.X(
            "commodity_product:N",
            title="Commodity Product",
            sort="-y",
            axis=alt.Axis(labelAngle=-45, labelLimit=130, labelOverlap=False)
        ),
        y=alt.Y(
            "facility_count:Q",
            title="Number of Facilities"
        ),
        tooltip=[
            "commodity_product:N",
            "facility_count:Q"
        ]
    )
    .properties(
    title="Distribution of Coal Commodity Products"
    )
)


# =========================================================
# CHART DATA — SCATTER (Top 5 facilities)
# =========================================================

coal_type = st.radio(
    "Coal Process Type (Trend Chart)",
    options=["coal mined", "clean coal"],
    format_func=lambda x: x.title(),
    horizontal=True
)

scatter_source = filtered[
    filtered["coal_process_type"] == coal_type
]

# Guard: no data
if scatter_source.empty:
    st.warning(f"No data available for {coal_type}.")
else:
    top_facilities = (
        scatter_source
        .groupby("facility_name", as_index=False)
        .agg(total_tonnes=("value_tonnes", "sum"))
        .sort_values("total_tonnes", ascending=False)
        .head(5)["facility_name"]
    )

    scatter_df = (
        scatter_source[
            scatter_source["facility_name"].isin(top_facilities)
        ]
        .groupby(
            ["facility_name", "year"],
            as_index=False
        )
        .agg(
            value_tonnes=("value_tonnes", "sum")
        )
    )

# Base chart
base = (
    alt.Chart(scatter_df)
    .encode(
        x=alt.X(
            "year:O",
            title="Year",
            axis=alt.Axis(labelAngle=-45, labelOverlap=False)
        ),
        y=alt.Y(
            "value_tonnes:Q",
            title="Production (tonnes)"
        ),
        color=alt.Color(
            "facility_name:N",
            legend=alt.Legend(title="Facility")
        )
    )
)

scatter_chart = (
    base.mark_line() +
    base.mark_circle(size=70, opacity=0.7)
).properties(
    title=f"Top 5 Facilities – {coal_type.title()} Production Trend"
)

st.markdown("### Production Overview")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.altair_chart(bar_chart, use_container_width=True)

with chart_col2:
    if not scatter_source.empty:
        st.altair_chart(scatter_chart, use_container_width=True)

# st.dataframe(
#     filtered,
#     use_container_width=True
# )
