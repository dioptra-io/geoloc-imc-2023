import numpy as np
import itertools
from math import radians,cos, sin, asin, sqrt


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
    circles_to_keep = set()
    for c_1, c_2 in itertools.combinations(circles, 2):
        lat_1, lon_1, rtt_1, d_1, r_1 = c_1
        if d_1 is None:
            d_1 = rtt_to_km(rtt_1, speed_threshold)
        if r_1 is None:
            r_1 = d_1 / 6371

        lat_2, lon_2, rtt_2, d_2, r_2 = c_2
        if d_2 is None:
            d_2 = rtt_to_km(rtt_2, speed_threshold)
        if r_2 is None:
            r_2 = d_2 / 6371

        remove, keep = check_circle_inclusion(
            (lat_1, lon_1, rtt_1, d_1, r_1), (lat_2, lon_2, rtt_2, d_2, r_2)
        )

        if remove:
            circles_to_ignore.add(remove)
            circles_to_keep.add(keep)
        else:
            circles_to_keep.add((lat_1, lon_1, rtt_1, d_1, r_1))
            circles_to_keep.add((lat_2, lon_2, rtt_2, d_2, r_2))

    return circles_to_keep - circles_to_ignore


def circle_intersections(circles, speed_threshold=None):
    intersect_points = []

    circles = circle_preprocessing(circles, speed_threshold=speed_threshold)

    if len(circles) <= 2:
        print(f"Not enough circles ({len(circles)}).")
        return []

    for c_1, c_2 in itertools.combinations(circles, 2):
        lat_1, lon_1, rtt_1, d_1, r_1 = c_1
        lat_2, lon_2, rtt_2, d_2, r_2 = c_2

        x1 = np.array(list(geo_to_cartesian(lat_1, lon_1)))
        x2 = np.array(list(geo_to_cartesian(lat_2, lon_2)))

        q = np.dot(x1, x2)

        a = (np.cos(r_1) - np.cos(r_2) * q) / (1 - (q ** 2))
        b = (np.cos(r_2) - np.cos(r_1) * q) / (1 - (q ** 2))

        x0 = a * x1 + b * x2

        n = np.cross(x1, x2)
        if (1 - np.dot(x0, x0)) / np.dot(n, n) <= 0:
            print("ANYCAST???", (lat_1, lon_1, rtt_1, d_1), (lat_2, lon_2, rtt_2, d_2))
            continue

        t = np.sqrt((1 - np.dot(x0, x0)) / np.dot(n, n))

        i1 = x0 + t * n
        i2 = x0 - t * n

        i_lon_1 = np.arctan(i1[1] / i1[0]) / (np.pi / 180)
        i_lat_1 = np.arctan(i1[2] / np.sqrt((i1[0] ** 2) + (i1[1] ** 2))) / (
            np.pi / 180
        )
        intersect_points.append((i_lat_1, i_lon_1))

        i_lon_2 = np.arctan(i2[1] / i2[0]) / (np.pi / 180)
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


def polygon_area(points):
    poly_area = 0

    count = len(points)
    j = count - 1

    if count < 3:
        return None

    for i in range(0, count):
        p1_x, p1_y = points[i]
        p2_x, p2_y = points[j]

        poly_area += p1_x * p2_y
        poly_area -= p1_y * p2_x
        j = i

    poly_area /= 2
    if np.isnan(poly_area):
        return None

    return abs(poly_area)


def polygon_centroid(points):
    f_total = 0
    x_total = 0
    y_total = 0

    count = len(points)
    j = count - 1

    if count < 3:
        return None

    for i in range(0, count):
        p1_x, p1_y = points[i]
        p2_x, p2_y = points[j]

        f_total = p1_x * p2_y - p2_x * p1_y
        x_total += (p1_x + p2_x) * f_total
        y_total += (p1_y + p2_y) * f_total
        j = i

    six_area = polygon_area(points) * 6
    if six_area is None:
        return None

    return x_total / six_area, y_total / six_area


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
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2

    c = 2 * asin(sqrt(a))

    r = 6371

    return(c * r)
