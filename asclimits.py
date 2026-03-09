#parse_gpx and discretize were both pre-made functions, not made by me, but used in my function cumulative_dist and running the code

from itertools import chain
import geopandas as gpd
import shapely
import shapely.geometry as geom
import numpy as np
import array

def parse_gpx(file_path: str) -> gpd.GeoSeries:
    """Turn GPX file into GeoSeries of points.

    Args:
        file_path (str): File path string.

    Returns:
        out (gpd.GeoSeries): Points from GPX file in EPSG 4326.
    """
    route = gpd.read_file(file_path, layer="track_points")
    segments = route.groupby(["track_seg_id"])
    lines = segments.aggregate({"geometry": list})["geometry"].apply(
        lambda p: geom.LineString(p)
    )
    segments = gpd.GeoDataFrame(lines)
    all_points = list(
        chain(
            *[
                [geom.Point(p) for p in seg.coords]
                for seg in segments["geometry"].array
            ]
        )
    )
    points = gpd.GeoSeries(all_points, crs="EPSG:4326").drop_duplicates()
    return points


def discretize(series: gpd.GeoSeries, length: float) -> gpd.GeoSeries:
    """Ensures points in GeoSeries are at least length apart.

    Args:
        series (gpd.GeoSeries): GeoSeries of shapely.Point objects.
        length (float): distance to ensure points are a maximum of length in
        meters apart.

    Returns:
        gpd.GeoSeries: Spaced out points
    """
    series_proj = series.to_crs(epsg=5071)
    out = shapely.segmentize(geom.LineString(series_proj.geometry), length)
    return gpd.GeoSeries([geom.Point(p) for p in out.coords])


def cumulative_dist(series: gpd.GeoSeries, units: str) -> float:
    projSeries = series.to_crs(epsg=5071)
    pointsArray = projSeries.geometry.to_numpy()
    cumDist = np.zeros(len(pointsArray))
    for i in range(1, len(pointsArray)):
        tempDist = pointsArray[i - 1].distance(pointsArray[i])
        cumDist[i] = cumDist[i - 1] + tempDist
    #pointsArray is an array
    #return array of cum. dist at each pt so far, with 0 being the first pt and the cum. dist being the last index
    currentDist = sum(pointsArray[i].distance(pointsArray[i + 1]) for i in range(len(pointsArray) - 1))
    if not (units == "meters" or units == "kilometers" or units == "miles"):
        raise ValueError("Valid units are meters, kilometers, and miles")
    if units == "meters" or units == "Meters":
        print("Cumulative distance at each index:", cumDist, "meters")
        print("Total distance:", currentDist, "meters")
    if units == "kilometers" or units == "Kilometers":
        print("Cumulative distance at each index:", cumDist / 1000, "kilometers")
        print("Total distance:", currentDist / 1000, "kilometers")
    if units == "miles" or units == "Miles":
        print("Cumulative distance at each index:", cumDist * 0.000621371, "miles")
        print("Total distance:", currentDist * 0.000621371, "miles")

#two trial calls
cumulative_dist(parse_gpx(r'C:\Users\admin\Downloads\1BL_EdwardsvilleLoop.gpx'), "kilometers")
cumulative_dist(parse_gpx(r'C:\Users\admin\Downloads\1A_NashvilleToPaducah.gpx'), "meters")
#cumulative_dist(parse_gpx(r'C:\Users\admin\Downloads\1A_NashvilleToPaducah.gpx'), "feet")
