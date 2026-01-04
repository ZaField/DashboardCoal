import geopandas as gpd
import pandas as pd
import fiona

GPKG_FILE = "facilities.gpkg"
OWNERSHIP_FILE = "ownership.csv"

def load_facility_data(layer=None):
    layers = fiona.listlayers(GPKG_FILE)
    if layer is None:
        layer = layers[0]

    gdf = gpd.read_file(GPKG_FILE, layer=layer)

    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    gdf = gdf[gdf.geometry.notnull()]
    gdf = gdf[~gdf.geometry.is_empty]

    ownership_df = pd.read_csv(OWNERSHIP_FILE)

    latest_ownership = (
        ownership_df
        .sort_values("year", ascending=False)
        .groupby("facility_id", as_index=False)
        .first()
    )

    gdf = gdf.merge(
        latest_ownership[["facility_id", "owners", "year"]],
        on="facility_id",
        how="left"
    ).rename(columns={"year": "ownership_year"})

    return gdf, layers
