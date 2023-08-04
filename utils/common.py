import os
import time
import logging

from clickhouse_driver import Client

from default import GEO_REPLICATION_DB, DB_HOST
from utils.clickhouse_query import get_min_rtt_per_src_dst_query_ping_table, get_min_rtt_per_src_dst_prefix_query_ping_table
from utils.helpers import distance, haversine, select_best_guess_centroid
from utils.measurement_utils import load_json, dump_json


speed_of_light = 300000
speed_of_internet = speed_of_light * 2/3


def compute_rtts_per_dst_src(table, filter, threshold, is_per_prefix=False):
    """
        Compute the guessed geolocation of the targets
        """
    # Compute the geolocation of the different IP addresses
    if not is_per_prefix:
        query = get_min_rtt_per_src_dst_query_ping_table(GEO_REPLICATION_DB, table,
                                                         filter=filter,
                                                         threshold=threshold)
    else:
        query = get_min_rtt_per_src_dst_prefix_query_ping_table(GEO_REPLICATION_DB, table,
                                                                filter=filter,
                                                                threshold=threshold)

    client = Client(DB_HOST)

    settings = {'max_block_size': 100000}
    rows = client.execute_iter(query, settings=settings)
    rtt_per_srcs_dst = {}
    for dst, src, min_rtt in rows:
        rtt_per_srcs_dst.setdefault(dst, {})[src] = [min_rtt]
    client.disconnect()
    return rtt_per_srcs_dst


def compute_geo_info(probes, serialized_file):
    country_per_vp_ip = {}
    asn_per_vp_ip = {}
    vp_coordinates_per_ip = {}
    ip_per_coordinates = {}
    anchors_per_ip_address = {}

    anchors = set()
    countries_anchors = set()
    countries_probes = set()
    ases_anchors = set()
    ases_probes = set()
    for probe in probes:
        if "address_v4" in probe and "geometry" in probe and "coordinates" in probe["geometry"]:
            ip_v4_address = probe["address_v4"]
            if ip_v4_address is None:
                continue
            anchors_per_ip_address[ip_v4_address] = probe
            long, lat = probe["geometry"]["coordinates"]
            country = probe["country_code"]
            country_per_vp_ip[ip_v4_address] = country
            asn_v4 = probe["asn_v4"]
            asn_per_vp_ip[ip_v4_address] = asn_v4
            vp_coordinates_per_ip[ip_v4_address] = lat, long
            ip_per_coordinates[lat, long] = ip_v4_address

            ases_probes.add(asn_v4)
            countries_probes.add(country)

            if "is_anchor" in probe and probe["is_anchor"]:
                anchors.add(ip_v4_address)
                ases_anchors.add(asn_v4)
                countries_anchors.add(country)

    if not os.path.exists(serialized_file):
        before = time.time()
        vp_distance_matrix = {}
        vp_coordinates_per_ip_l = sorted(
            vp_coordinates_per_ip.items(), key=lambda x: x[0])
        for i in range(len(vp_coordinates_per_ip_l)):
            if i % 100 == 0:
                print(i)
            vp_i, vp_i_coordinates = vp_coordinates_per_ip_l[i]
            if vp_i not in anchors:
                continue
            for j in range(len(vp_coordinates_per_ip)):
                vp_j, vp_j_coordinates = vp_coordinates_per_ip_l[j]
                distance = haversine(vp_i_coordinates, vp_j_coordinates)
                vp_distance_matrix.setdefault(vp_i, {})[vp_j] = distance
                vp_distance_matrix.setdefault(vp_j, {})[vp_i] = distance

        after = time.time()
        dump_json(vp_distance_matrix, serialized_file)
    else:
        vp_distance_matrix = load_json(serialized_file)

    return vp_coordinates_per_ip, ip_per_coordinates, country_per_vp_ip, asn_per_vp_ip, vp_distance_matrix, anchors_per_ip_address


def compute_error(dst, vp_coordinates_per_ip, rtt_per_src):
    error = None
    circles = []
    guessed_geolocation_circles = select_best_guess_centroid(
        dst, vp_coordinates_per_ip, rtt_per_src)
    if guessed_geolocation_circles is not None:
        guessed_geolocation, circles = guessed_geolocation_circles
        real_geolocation = vp_coordinates_per_ip[dst]
        error = haversine(guessed_geolocation, real_geolocation)
    return error, circles


def compute_error_threshold_cdfs(errors_threshold, filter_dsts=None):

    error_threshold_cdfs = []
    circles_threshold_cdfs = []
    error_per_ip = {}
    for threshold, errors in sorted(errors_threshold.items(), key=lambda x: int(x[0])):
        if filter_dsts is not None and threshold in filter_dsts:
            allowed_dsts = set(
                x[0] for x in filter_dsts[threshold] if x[1] is not None)
        threshold_i = int(threshold)
        error_threshold_cdf = []
        circles_threshold_cdf = []
        n_no_geolocation = 0
        for dst, error, circles in errors:
            if filter_dsts is not None and dst not in allowed_dsts:
                continue
            if error is not None:
                if threshold_i == 0:
                    error_per_ip[dst] = error
                error_threshold_cdf.append(error)
                circles_threshold_cdf.append(circles)
            else:
                n_no_geolocation += 1
        error_threshold_cdfs.append(error_threshold_cdf)
        circles_threshold_cdfs.append(circles_threshold_cdf)

        print(f"Threshold {threshold} no geolocation {n_no_geolocation}")

    return error_threshold_cdfs, circles_threshold_cdfs, error_per_ip


def compute_remove_wrongly_geolocated_probes(rtts_per_srcs_dst, vp_coordinates_per_ip, vp_distance_matrix, removed_anchors):
    """

    :param rtts_per_srcs_dst:
    :param vp_coordinates_per_ip:
    :param vp_distance_matrix:
    :return:
    """

    speed_of_internet_violations_per_ip = {}

    for dst, rtts_per_src in rtts_per_srcs_dst.items():
        if dst not in vp_coordinates_per_ip:
            continue

        if dst in removed_anchors:
            continue

        for probe, rtts in rtts_per_src.items():
            if probe in removed_anchors:
                continue
            min_rtt_probe = min(rtts)
            if probe not in vp_distance_matrix[dst]:
                continue
            max_theoretical_distance = (
                speed_of_internet * min_rtt_probe / 1000) / 2
            if vp_distance_matrix[dst][probe] > max_theoretical_distance:
                # Impossible distance
                speed_of_internet_violations_per_ip.setdefault(
                    dst, set()).add(probe)
                speed_of_internet_violations_per_ip.setdefault(
                    probe, set()).add(dst)

    # Greedily remove the IP address with the more SOI violations
    n_violations = sum([len(x)
                       for x in speed_of_internet_violations_per_ip.values()])
    removed_probes = set()
    while n_violations > 0:
        print("Violations:", n_violations)
        # Remove the IP address with the highest number of SOI violations
        worse_ip, speed_of_internet_violations = max(
            speed_of_internet_violations_per_ip.items(), key=lambda x: len(x[1]))
        for ip, speed_of_internet_violations in speed_of_internet_violations_per_ip.items():
            speed_of_internet_violations.discard(worse_ip)
        del speed_of_internet_violations_per_ip[worse_ip]
        removed_probes.add(worse_ip)
        n_violations = sum(
            [len(x) for x in speed_of_internet_violations_per_ip.values()])
    print(len(removed_probes))
    return removed_probes


def country_filtering(probes: list, countries: dict) -> list:
    filtered_probes = []
    for probe in probes:

        # check if probe coordinates are close to default location
        try:
            country_geo = countries[probe["country_code"]]
        except KeyError as e:
            logging.info(
                f"error country code {probe['country_code']} is unknown")
            continue

        # if the country code is unknown, remove probe from dataset
        country_lat = float(country_geo["latitude"])
        country_lon = float(country_geo["longitude"])

        probe_lat = float(probe["geometry"]["coordinates"][1])
        probe_lon = float(probe["geometry"]["coordinates"][0])

        dist = distance(country_lat, probe_lat, country_lon, probe_lon)

        if dist > 5:
            filtered_probes.append(probe)

    return filtered_probes
