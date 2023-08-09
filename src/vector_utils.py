from pathlib import Path
from typing import Union

import geopandas as gpd
from geopandas import GeoDataFrame
from geowrangler import distance_zonal_stats as dzs
from geowrangler import vector_zonal_stats as vzs
from loguru import logger
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.geometry.polygon import orient
from shapely.validation import explain_validity, make_valid

# Set directories
DATA_DIR = Path("../../../data/")
ADMIN_FPATH = DATA_DIR / "01-admin-bounds"
RAW_FPATH = DATA_DIR / "02-raw"
PROCESSED_FPATH = DATA_DIR / "03-processed"
OUTPUT_FPATH = DATA_DIR / "04-output"
GIS_FPATH = DATA_DIR / "05-gis"

# COASTAL BUFFER


def one_sided_poly_buffer(
    poly: Polygon, buffer_m: float
) -> Union[Polygon, MultiPolygon]:
    bound = poly.boundary

    # estimate how big the buffer zone will be
    poly_len = min(poly.length, buffer_m)
    buffer_area_estimate = buffer_m * poly_len

    # no need to buffer for small polygons
    if poly.area < buffer_area_estimate:
        buffered_bound = poly
    # buffer for sufficiently large polygons
    else:
        buffered_bound = bound.buffer(-buffer_m / 2, single_sided=True)

        # take the intersection to remove the outward spikes from a single sided buffer
        buffered_bound = buffered_bound.intersection(poly)

        # buffer it again to fill in inward spikes
        buffered_bound = buffered_bound.buffer(buffer_m / 2)
        # take intersection to remove outward spikes again
        buffered_bound = buffered_bound.intersection(poly)

    return buffered_bound


# GET POINT FEATURES


def add_osm_poi_features(
    aoi,
    country,
    year,
    osm_data_manager,
    poi_types,
    use_cache=True,
    metric_crs="epsg:3857",
    inplace=False,
    nearest_poi_max_distance=10000,
):
    """Generates features for the AOI based on OSM POI data (POIs, roads, etc)."""

    # Load-in the OSM POIs data
    osm = osm_data_manager.load_pois(country, year=year, use_cache=use_cache)

    # Create a copy of the AOI gdf if not inplace to avoid modifying the original gdf
    if not inplace:
        aoi = aoi.copy()

    aoi["osm_year"] = year
    aoi["osm_year"] = aoi["osm_year"].astype(int)

    # GeoWrangler: Count number of all POIs per tile
    aoi = vzs.create_zonal_stats(
        aoi,
        osm,
        overlap_method="intersects",
        aggregations=[{"func": "count", "output": "poi_count", "fillna": True}],
    )

    # Count specific aoi types
    for poi_type in poi_types:
        # GeoWrangler: Count with vector zonal stats
        aoi = vzs.create_zonal_stats(
            aoi,
            osm[osm["fclass"] == poi_type],
            overlap_method="intersects",
            aggregations=[
                {"func": "count", "output": f"osm_poi_{poi_type}_count", "fillna": True}
            ],
        )

        # GeoWrangler: Distance with distance zonal stats
        col_name = f"osm_poi_{poi_type}_nearest"
        aoi = dzs.create_distance_zonal_stats(
            aoi.to_crs(metric_crs),
            osm[osm["fclass"] == poi_type].to_crs(metric_crs),
            max_distance=nearest_poi_max_distance,
            aggregations=[],
            distance_col=col_name,
        ).to_crs("epsg:4326")

        # If no POI was found within the distance limit, set the distance to the max distance
        aoi[col_name] = aoi[col_name].fillna(value=nearest_poi_max_distance)

    return aoi


def add_point_features(
    aoi,
    points_gdf,
    types_col,
    metric_crs="epsg:3857",
    inplace=False,
    nearest_poi_max_distance=10000,
):
    """Generates features for the AOI based on point data."""

    # Create a copy of the AOI gdf if not inplace to avoid modifying the original gdf
    if not inplace:
        aoi = aoi.copy()

    # GeoWrangler: Count number of all POIs per tile
    aoi = vzs.create_zonal_stats(
        aoi,
        points_gdf,
        overlap_method="intersects",
        aggregations=[{"func": "count", "output": "poi_count", "fillna": True}],
    )

    poi_types = points_gdf[types_col].unique().tolist()

    # Count specific aoi types
    for poi_type in poi_types:
        # GeoWrangler: Count with vector zonal stats
        aoi = vzs.create_zonal_stats(
            aoi,
            points_gdf[points_gdf[types_col] == poi_type],
            overlap_method="intersects",
            aggregations=[
                {"func": "count", "output": f"{poi_type}_count", "fillna": True}
            ],
        )

        # GeoWrangler: Distance with distance zonal stats
        col_name = f"{poi_type}_nearest"
        aoi = dzs.create_distance_zonal_stats(
            aoi.to_crs(metric_crs),
            points_gdf[points_gdf[types_col] == poi_type].to_crs(metric_crs),
            max_distance=nearest_poi_max_distance,
            aggregations=[],
            distance_col=col_name,
        ).to_crs("epsg:4326")

        # If no POI was found within the distance limit, set the distance to the max distance
        aoi[col_name] = aoi[col_name].fillna(value=nearest_poi_max_distance)

    return aoi


def add_osm_water_features(
    aoi,
    country,
    year,
    waterways=False,
    region_zip_file=RAW_FPATH / "osm" / "philippines-220101-free.shp.zip",
    metric_crs="epsg:3857",
    nearest_poi_max_distance=10000,
    inplace=False,
):
    """Generates features for the AOI based on OSM road data"""

    if waterways:
        osm_water_filepath = f"{region_zip_file}!gis_osm_waterways_free_1.shp"
    else:
        osm_water_filepath = f"{region_zip_file}!gis_osm_water_a_free_1.shp"

    if year is None:
        logger.debug(f"OSM Water for {country} being loaded from {region_zip_file}")
    else:
        logger.debug(
            f"OSM Water for {country} and year {year} being loaded from {region_zip_file}"
        )
    water_gdf = gpd.read_file(osm_water_filepath)

    assert aoi.crs == water_gdf.crs

    if not inplace:
        aoi = aoi.copy()

    aoi["osm_year"] = year
    aoi["osm_year"] = aoi["osm_year"].astype(int)

    poi_types = water_gdf["fclass"].unique().tolist()

    # Count specific aoi types
    for poi_type in poi_types:
        # GeoWrangler: Distance with distance zonal stats
        col_name = f"osm_{poi_type}_nearest"
        aoi = dzs.create_distance_zonal_stats(
            aoi.to_crs(metric_crs),
            water_gdf[water_gdf["fclass"] == poi_type].to_crs(metric_crs),
            max_distance=nearest_poi_max_distance,
            aggregations=[],
            distance_col=col_name,
        ).to_crs("epsg:4326")

        # If no POI was found within the distance limit, set the distance to the max distance
        aoi[col_name] = aoi[col_name].fillna(value=nearest_poi_max_distance)

    return aoi


def add_distance_to_shore(
    aoi,
    coastal_buffer_path=OUTPUT_FPATH / "ph_coasts_3000m.gpkg",
    metric_crs="epsg:3857",
    nearest_poi_max_distance=10000,
    inplace=False,
):
    """Generates features for the AOI based on OSM road data"""

    coast_gdf = gpd.read_file(coastal_buffer_path)
    coast_gdf = coast_gdf.to_crs("epsg:4326")

    assert aoi.crs == coast_gdf.crs

    if not inplace:
        aoi = aoi.copy()

    col_name = "distance_from_coast"
    aoi = dzs.create_distance_zonal_stats(
        aoi.to_crs(metric_crs),
        coast_gdf.to_crs(metric_crs),
        max_distance=nearest_poi_max_distance,
        aggregations=[],
        distance_col=col_name,
    ).to_crs("epsg:4326")

    # If no POI was found within the distance limit, set the distance to the max distance
    aoi[col_name] = aoi[col_name].fillna(value=nearest_poi_max_distance)

    return aoi
