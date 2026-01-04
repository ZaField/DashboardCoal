# pip install -r requirements.txt

import streamlit as st
import geopandas as gpd
import pandas as pd
import fiona
import folium
from streamlit_folium import st_folium
from data_loader import load_facility_data

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="Facility GeoPackage Map",
    layout="wide"
)
st.title("Facility GeoPackage Map")

# =========================================================
# CONSTANT
# =========================================================
GPKG_FILE = "facilities.gpkg"
COUNTRY_COL = "country"
NAME_COL = "facility_name"
ID_COL = "facility_id"

EXCLUDE_ATTR_COLS = [
    "GID_0", "GID_1", "GID_2", "GID_3", "GID_4", "source_id", "comment", "production_start", "production_end", "activity_status", "activity_status_year", "surface_area_sq_km", "concession_area_sq_km", "sub_site_other_names", "sub_site_name", "facility_other_names"
]

# =========================================================
# LOAD DATA (SINGLE DEFAULT LAYER)
# =========================================================
gdf, _ = load_facility_data()

if gdf.empty:
    st.warning("Layer is empty")
    st.stop()
    
# =========================================================
# LAYOUT
# =========================================================
col1, col2 = st.columns([1, 2])

# =========================================================
# LEFT PANEL — FILTER BERTAHAP
# =========================================================
with col1:
    st.subheader("Filter Facilities")

    countries = sorted(gdf[COUNTRY_COL].dropna().unique())
    country = st.selectbox("Country", countries)

    gdf_country = gdf[gdf[COUNTRY_COL] == country].copy()

    def facility_label(row):
        if row[NAME_COL] and str(row[NAME_COL]).strip():
            return row[NAME_COL]
        return f"(Unnamed) {row[ID_COL]}"

    gdf_country["__label__"] = gdf_country.apply(facility_label, axis=1)

    selected_label = st.selectbox(
        "Facility",
        gdf_country["__label__"].tolist()
    )

    selected_row = gdf_country[
        gdf_country["__label__"] == selected_label
    ].iloc[0]

    with st.expander("Facility Attributes"):
        hidden_cols = ["geometry", "__label__"] + EXCLUDE_ATTR_COLS

        display_row = (
            selected_row
            .drop(labels=hidden_cols, errors="ignore")
        )

        st.dataframe(
            display_row.to_frame("value")
        )

# =========================================================
# RIGHT PANEL — MAP
# =========================================================
with col2:

    # -------- SELECTED POINT (SAFE) --------
    sel_geom = selected_row.geometry
    sel_point = sel_geom if sel_geom.geom_type == "Point" else sel_geom.centroid
    sel_lat, sel_lon = sel_point.y, sel_point.x

    # -------- MAP INIT --------
    m = folium.Map(
        location=[sel_lat, sel_lon],
        zoom_start=11,
        tiles="OpenStreetMap"
    )

    # =====================================================
    # ALL FACILITIES (BACKGROUND PINS)
    # =====================================================
    for _, r in gdf_country.iterrows():
        geom = r.geometry
        pt = geom if geom.geom_type == "Point" else geom.centroid

        folium.CircleMarker(
            location=[pt.y, pt.x],
            radius=4,
            color="#4A90E2",        # soft blue
            fill=True,
            fill_opacity=0.6,
            weight=1,
            tooltip=r["__label__"]
        ).add_to(m)

    # =====================================================
    # SELECTED FACILITY (HIGHLIGHT PIN)
    # =====================================================
    folium.Marker(
        location=[sel_lat, sel_lon],
        tooltip=selected_label,
        popup=selected_label,
        icon=folium.Icon(
            color="red",
            icon="map-marker",
            prefix="fa"
        )
    ).add_to(m)

    st_folium(
        m,
        use_container_width=True,
        height=700
    )
