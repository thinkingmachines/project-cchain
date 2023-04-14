from typing import Union

from geopandas import GeoDataFrame
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.geometry.polygon import orient
from shapely.validation import explain_validity, make_valid


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
