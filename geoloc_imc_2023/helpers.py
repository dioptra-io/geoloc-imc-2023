import itertools
from math import asin, cos, radians, sin, sqrt, pi

import numpy as np


def internet_speed(rtt, speed_threshold):
    if speed_threshold is not None:
        return speed_threshold

    if rtt >= 80:
        speed_threshold = 4 / 9
    if rtt >= 5 and rtt < 80:
        speed_threshold = 3 / 9
    if rtt >= 0 and rtt < 5:
        speed_threshold = 1 / 6

    return speed_threshold


def rtt_to_km(rtt, speed_threshold=None, c=300):
    return internet_speed(rtt, speed_threshold) * rtt * c / 2


def is_within_cirle(vp_geo, rtt, candidate_geo, speed_threshold=None):
    d = rtt_to_km(rtt, speed_threshold)
    d_vp_candidate = haversine(vp_geo, candidate_geo)
    if d < d_vp_candidate:
        return False
    else:
        return True


def geo_to_cartesian(lat, lon):
    lat *= np.pi / 180
    lon *= np.pi / 180

    x = np.cos(lon) * np.cos(lat)
    y = np.sin(lon) * np.cos(lat)
    z = np.sin(lat)

    return x, y, z


def check_circle_inclusion(c_1, c_2):
    lat_1, lon_1, rtt_1, d_1, r_1 = c_1
    lat_2, lon_2, rtt_2, d_2, r_2 = c_2
    d = haversine((lat_1, lon_1), (lat_2, lon_2))
    if d_1 > (d + d_2):
        return c_1, c_2
    elif d_2 > (d + d_1):
        return c_2, c_1
    return None, None


def circle_preprocessing(circles, speed_threshold=None):
    circles_to_ignore = set()

    circles_with_r_info = []
    for c in circles:
        lat, lon, rtt, d, r = c
        if d is None:
            d = rtt_to_km(rtt, speed_threshold)
        if r is None:
            r = d / 6371
        circles_with_r_info.append((lat, lon, rtt, d, r))

    for i in range(len(circles_with_r_info)):
        c_1 = circles_with_r_info[i]
        if c_1 in circles_to_ignore:
            continue
        lat_1, lon_1, rtt_1, d_1, r_1 = c_1
        for j in range(i + 1, len(circles_with_r_info)):
            c_2 = circles_with_r_info[j]
            if c_2 in circles_to_ignore:
                continue
            lat_2, lon_2, rtt_2, d_2, r_2 = c_2
            remove, keep = check_circle_inclusion(
                (lat_1, lon_1, rtt_1, d_1, r_1), (lat_2, lon_2, rtt_2, d_2, r_2)
            )
            if remove:
                circles_to_ignore.add(remove)

    circles_to_keep = set(circles_with_r_info) - circles_to_ignore

    return circles_to_keep


def get_points_on_circle(lat_c, lon_c, r_c, nb_points: int = 4):
    """from a circle, return a set of points"""
    circle_points = []
    for k in range(nb_points):
        # compute
        angle = pi * 2 * k / nb_points
        dx = r_c * 1000 * cos(angle)
        dy = r_c * 1000 * sin(angle)
        lat = lat_c + (180 / pi) * (dy / 6378137)
        lon = lon_c + (180 / pi) * (dx / 6378137) / cos(lat_c * pi / 180)

        circle_points.append((lat, lon))

    return circle_points


def circle_intersections(circles, speed_threshold=None):
    """
    Check out this link for more details about the maths:
    https://gis.stackexchange.com/questions/48937/calculating-intersection-of-two-circles
    """
    intersect_points = []

    circles = circle_preprocessing(circles, speed_threshold=speed_threshold)

    if len(circles) <= 2:
        if len(circles) == 1:
            single_circle = list(circles)[0]
            lat, lon, rtt, d, r = single_circle
            filtered_points = get_points_on_circle(lat, lon, d)
            return filtered_points

    for c_1, c_2 in itertools.combinations(circles, 2):
        lat_1, lon_1, rtt_1, d_1, r_1 = c_1
        lat_2, lon_2, rtt_2, d_2, r_2 = c_2

        x1 = np.array(list(geo_to_cartesian(lat_1, lon_1)))
        x2 = np.array(list(geo_to_cartesian(lat_2, lon_2)))

        q = np.dot(x1, x2)

        a = (np.cos(r_1) - np.cos(r_2) * q) / (1 - (q**2))
        b = (np.cos(r_2) - np.cos(r_1) * q) / (1 - (q**2))

        x0 = a * x1 + b * x2

        n = np.cross(x1, x2)
        if (1 - np.dot(x0, x0)) / np.dot(n, n) <= 0:
            # print("ANYCAST???", (lat_1, lon_1, rtt_1, d_1), (lat_2, lon_2, rtt_2, d_2))
            continue

        t = np.sqrt((1 - np.dot(x0, x0)) / np.dot(n, n))

        i1 = x0 + t * n
        i2 = x0 - t * n


        i_lon_1 = np.arctan2(i1[1], i1[0]) * (180 / np.pi)
        i_lat_1 = np.arctan(i1[2] / np.sqrt((i1[0] ** 2) + (i1[1] ** 2))) / (
            np.pi / 180
        )
        intersect_points.append((i_lat_1, i_lon_1))

        i_lon_2 = np.arctan2(i2[1], i2[0]) * (180 / np.pi)
        i_lat_2 = np.arctan(i2[2] / np.sqrt((i2[0] ** 2) + (i2[1] ** 2))) / (
            np.pi / 180
        )
        intersect_points.append((i_lat_2, i_lon_2))

    filtred_points = []
    for point_geo in intersect_points:
        for lat_c, long_c, rtt_c, d_c, r_c in circles:
            if not is_within_cirle((lat_c, long_c), rtt_c, point_geo, speed_threshold):
                break
        else:
            filtred_points.append(point_geo)

    return filtred_points


def polygon_centroid(points):
    """
    Compute polygon centroid using Finit Set of point method.
    (see https://en.wikipedia.org/wiki/Centroid#Of_a_finite_set_of_points)
    """
    x = 0
    y = 0
    for point in points:
        x += point[0]
        y += point[1]
    return x / len(points), y / len(points)


def haversine(input_location, block_location):
    """Distance between two locations in earth."""
    in_lat, in_lon, block_lat, block_lon = map(
        np.radians, [*input_location, *block_location]
    )

    dlat = block_lat - in_lat
    dlon = block_lon - in_lon

    distances = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(in_lat) * np.cos(block_lat) * np.sin(dlon / 2.0) ** 2
    )

    return 6367 * 2 * np.arcsin(np.sqrt(distances))


def distance(lat1, lat2, lon1, lon2):
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2

    c = 2 * asin(sqrt(a))

    r = 6371

    return c * r


def get_middle_intersection(intersections):
    """in case of only two intersection points, return the middle segment"""
    (lat1, lon1) = intersections[0]
    (lat2, lon2) = intersections[1]

    # convert to radians
    lon1 = radians(lon1)
    lon2 = radians(lon2)
    lat1 = radians(lat1)
    lat2 = radians(lat2)

    # calculate the middle of two points
    Bx = np.cos(lat2) * np.cos(lon2 - lon1)
    By = np.cos(lat2) * np.sin(lon2 - lon1)
    latMid = np.arctan2(
        np.sin(lat1) + np.sin(lat2),
        np.sqrt((np.cos(lat1) + Bx) * (np.cos(lat1) + Bx) + By * By),
    )
    lonMid = lon1 + np.arctan2(By, np.cos(lat1) + Bx)

    # convert back to degrees
    latMid = latMid * (180 / pi)
    lonMid = lonMid * (180 / pi)

    return latMid, lonMid


def get_closest_vp(measurement_set: dict) -> tuple:
    """return the position of the vantage point with shortest ping measurement"""
    shortest_ping = float("inf")
    closest_vp = None
    for vp, result in measurement_set.items():
        if shortest_ping > result["min_rtt"]:
            shortest_ping = result["min_rtt"]
            closest_vp = vp

    return closest_vp


def select_best_guess_centroid(measurement_results: dict, vp_dataset: dict) -> tuple:
    """
    Find the best guess
    that is the location of the vantage point closest to the centroid.
    """
    probe_circles = {}
    for vp_addr, result in measurement_results.items():
        try:
            lat = vp_dataset[vp_addr]["latitude"]
            lon = vp_dataset[vp_addr]["longitude"]
            min_rtt = result["min_rtt"]
        except KeyError:
            continue

        if isinstance(min_rtt, float):
            probe_circles[vp_addr] = (
                lat,
                lon,
                min_rtt,
                None,
                None,
            )

    circles = list(probe_circles.values())
    intersections = circle_intersections(circles, speed_threshold=2 / 3)

    centroid = None
    if len(intersections) > 2:
        centroid = polygon_centroid(intersections)
    elif len(intersections) == 2:
        # only two circles intersection, centroid is middle of the segment
        centroid = get_middle_intersection(intersections)
    else:
        closest_vp = get_closest_vp(measurement_results)
        centroid = (
            vp_dataset[closest_vp]["latitude"],
            vp_dataset[closest_vp]["longitude"],
        )

    return intersections, centroid
