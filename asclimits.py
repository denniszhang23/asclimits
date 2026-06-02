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

#below are the functions I have created

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

def gps_time_proj(df: pl.DataFrame) -> float:
    """Algorithm finds time taken to travel from one location to another.

    Takes in polars dataframe to find total time taken to travel through
    track data using only speed limits.

    Args:
        df (polars dataframe): input polars dataframe, df must have "Spd" and
        "Int" columns, pdf_parser_extract_table guarantees that these columns
        will be there given that the right page numbers are used. Columns will
        be cast as Float64 for calculation. Ensure columns have the same units.

    Returns:
        (float): returns estimate of time taken to travel through
        routebook pages using distance intervals and speed limits in those
        intervals.

    """
    df = df.with_columns(
        pl.col("Spd").cast(pl.Float64, strict=False).forward_fill()
    )
    df = df.with_columns(pl.col("Int").cast(pl.Float64, strict=False))

    return df.select(
        (pl.col("Int") / pl.col("Spd").replace(0, None)).sum()
    ).item()


def scale_time_proj(df: pl.DataFrame, time: float) -> pl.Series:
    """Algorithm to find car speeds at each interval specified by routebook.

    Takes in target time as a float and the routebook in the form of a polars
    dataframe and calculates the speed at which the car should travel in each
    interval to meet the target time by multiplying speed limits in each
    interval by a common scaling factor.

    Args:
        df (polars dataframe): input polars dataframe, df must have "Spd" and
        "Int" columns, pdf_parser_extract_table guarantees that these columns
        will be there given that the right page numbers are used. Columns will
        be cast as Float64 for calculation. Ensure columns have the same units.

        time (float): this is the time we want the car to take to travel through
        the designated distance interval. Make sure that the unit of input time
        is the same as the time specified in the rate given in the "Spd" column.

    Returns:
        (polars series): outputs column of speeds at which the car should travel
        at in each interval.

    """
    df = df.with_columns(
        pl.col("Spd").cast(pl.Float64, strict=False).forward_fill()
    )
    df = df.with_columns(pl.col("Int").replace("", None).cast(pl.Float64))

    return df.select(pl.col("Spd") * gps_time_proj(df) / time).to_series()
