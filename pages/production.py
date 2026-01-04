import streamlit as st
import pandas as pd
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
coal_df = pd.read_csv("coal.csv")
material_df = pd.read_csv("material_ids.csv")

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

filtered = production_df[
    production_df["country"] == country
]

st.dataframe(
    filtered,
    use_container_width=True
)
