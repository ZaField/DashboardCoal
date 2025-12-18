# pip install -r requirements.txt

import streamlit as st
import geopandas as gpd
import fiona
import folium
from streamlit_folium import st_folium

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="Facility GeoPackage Map",
    layout="wide"
)
st.title("🌍 Facility GeoPackage Map")

# =========================================================
# CONSTANT
# =========================================================
GPKG_FILE = "facilities.gpkg"
COUNTRY_COL = "country"
NAME_COL = "facility_name"
ID_COL = "facility_id"

# =========================================================
# LOAD GPKG
# =========================================================
try:
    layers = fiona.listlayers(GPKG_FILE)
except Exception as e:
    st.error(f"GPKG file not found or unreadable: {e}")
    st.stop()

layer = st.sidebar.selectbox("🗂️ Layer", layers)

# =========================================================
# LOAD DATA
# =========================================================
gdf = gpd.read_file(GPKG_FILE, layer=layer)

if gdf.empty:
    st.warning("Layer is empty")
    st.stop()

# =========================================================
# CRS FIX
# =========================================================
if gdf.crs and gdf.crs.to_epsg() != 4326:
    gdf = gdf.to_crs(epsg=4326)

# =========================================================
# CLEAN GEOMETRY
# =========================================================
gdf = gdf[gdf.geometry.notnull()]
gdf = gdf[~gdf.geometry.is_empty]

if gdf.empty:
    st.warning("No valid geometry")
    st.stop()

# =========================================================
# LAYOUT
# =========================================================
col1, col2 = st.columns([1, 2])

# =========================================================
# LEFT PANEL — FILTER BERTAHAP
# =========================================================
with col1:
    st.subheader("🔍 Filter Facilities")

    countries = sorted(gdf[COUNTRY_COL].dropna().unique())
    country = st.selectbox("🌎 Country", countries)

    gdf_country = gdf[gdf[COUNTRY_COL] == country].copy()

    def facility_label(row):
        if row[NAME_COL] and str(row[NAME_COL]).strip():
            return row[NAME_COL]
        return f"(Unnamed) {row[ID_COL]}"

    gdf_country["__label__"] = gdf_country.apply(facility_label, axis=1)

    selected_label = st.selectbox(
        "🏭 Facility",
        gdf_country["__label__"].tolist()
    )

    selected_row = gdf_country[
        gdf_country["__label__"] == selected_label
    ].iloc[0]

    with st.expander("📄 Facility Attributes"):
        st.dataframe(
            selected_row.drop(
                labels=["geometry", "__label__"],
                errors="ignore"
            ).to_frame("value")
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
