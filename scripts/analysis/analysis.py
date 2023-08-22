import random
import numpy as np

from multiprocessing.pool import Pool
from clickhouse_driver import Client

from scripts.utils.file_utils import load_json
from scripts.utils.helpers import haversine, select_best_guess_centroid, is_within_cirle, polygon_centroid, circle_intersections
from scripts.utils.clickhouse_utils import get_min_rtt_per_src_dst_query_ping_table, get_min_rtt_per_src_dst_prefix_query_ping_table
from scripts.ripe_atlas.atlas_api import get_prefix_from_ip
from default import SPEED_OF_INTERNET, GEO_REPLICATION_DB, DB_HOST


########## MILLION SCALE ##########

def compute_geolocation_features_per_ip_impl(dst, rtt_per_src, vps_per_target,
                                             vp_coordinates_per_ip, vp_distance_matrix_dst,
                                             threshold_distances,
                                             distance_operator, max_vps,
                                             is_use_prefix):

    features = {}
    if is_use_prefix:
        dst_prefix = get_prefix_from_ip(dst)
        if dst_prefix not in vps_per_target:
            print(
                f"Error, prefix {dst_prefix} not in measurements for VP selection algorithm")
            return features
    else:
        if dst not in vps_per_target:
            print(
                f"Error, prefix {dst} not in measurements for VP selection algorithm")
            return features
    # Compute error with different configurations
    errors = []

    for threshold_distance in threshold_distances:
        if is_use_prefix:
            vp_per_target_allowed = vps_per_target[dst_prefix]
        else:
            vp_per_target_allowed = vps_per_target[dst]

        if distance_operator == ">":
            vp_coordinates_per_ip_filter = {vp: vp_coordinates_per_ip[vp]
                                            for vp in vp_coordinates_per_ip
                                            if (vp_distance_matrix_dst[vp] > threshold_distance
                                                and vp in vp_per_target_allowed)
                                            or vp == dst}

        elif distance_operator == "<=":
            vp_coordinates_per_ip_filter = {vp: vp_coordinates_per_ip[vp]
                                            for vp in vp_coordinates_per_ip
                                            if (vp_distance_matrix_dst[vp] <= threshold_distance
                                            and vp in vp_per_target_allowed)
                                            or vp == dst}
        else:
            raise Exception("Not a good operator. Please > or <= ")

        if len(vp_coordinates_per_ip_filter) > max_vps:
            vp_coordinates_per_ip_filter_no_dst = dict(
                vp_coordinates_per_ip_filter)
            del vp_coordinates_per_ip_filter_no_dst[dst]
            vp_coordinates_per_ip_filter_sample = dict(
                random.sample(list(vp_coordinates_per_ip_filter_no_dst.items()), max_vps))
            vp_coordinates_per_ip_filter_sample[dst] = vp_coordinates_per_ip_filter[dst]
        else:
            vp_coordinates_per_ip_filter_sample = vp_coordinates_per_ip_filter

        error, circles = compute_error(
            dst, vp_coordinates_per_ip_filter_sample, rtt_per_src)
        errors.append((error, circles))
        features.setdefault(threshold_distance, []).append(
            (dst, error, len(circles)))
    return features


def compute_geolocation_features_per_ip(rtt_per_srcs_dst, vp_coordinates_per_ip, threshold_distances,
                                        vps_per_target,
                                        distance_operator,
                                        max_vps,
                                        is_use_prefix,
                                        vp_distance_matrix,
                                        is_multiprocess=True):
    """
        Compute some features to get some scatter plots in functions of the accuracy
        Features are:
        Topological distance from the closest VP
        Geographical distance from the closest VP
        """
    features = {}
    args = []
    for dst, rtt_per_src in sorted(rtt_per_srcs_dst.items()):
        if dst not in vp_coordinates_per_ip:
            # We do not know the geolocation of the anchor.
            continue
        args.append((dst, rtt_per_src, vps_per_target, vp_coordinates_per_ip,
                     vp_distance_matrix[dst],
                     threshold_distances,
                     distance_operator, max_vps, is_use_prefix))
    if is_multiprocess:
        # with Pool(24) as p:
        with Pool(4) as p:
            features_all_process = p.starmap(
                compute_geolocation_features_per_ip_impl, args[:])
            for features_process in features_all_process:
                for threshold, dst_error_distances in features_process.items():
                    features.setdefault(threshold, []).extend(
                        dst_error_distances)
    else:
        for arg in args:
            dst, rtt_per_src, vps_per_target, vp_coordinates_per_ip, vp_distance_matrix_dst, \
                threshold_distances, \
                distance_operator, max_vps, is_use_prefix = arg

            features_process = compute_geolocation_features_per_ip_impl(dst, rtt_per_src, vps_per_target, vp_coordinates_per_ip,
                                                                        vp_distance_matrix_dst, threshold_distances,
                                                                        distance_operator, max_vps, is_use_prefix)
            for threshold, dst_error_distances in features_process.items():
                features.setdefault(threshold, []).extend(dst_error_distances)
    return features


def compute_accuracy_vs_number_of_vps_impl(rtt_per_srcs_dst, vp_distance_matrix, available_vps, random_n_vp, vp_coordinates_per_ip,):

    random_vps = random.sample(available_vps, random_n_vp)
    vps_per_target = {x: list(set(random_vps)) for x in rtt_per_srcs_dst}
    features = compute_geolocation_features_per_ip(rtt_per_srcs_dst, vp_coordinates_per_ip,
                                                   [0],
                                                   vps_per_target=vps_per_target,
                                                   distance_operator=">", max_vps=100000,
                                                   is_use_prefix=False,
                                                   vp_distance_matrix=vp_distance_matrix,
                                                   is_multiprocess=True
                                                   )

    features = features[0]
    median_error = np.median([x[1] for x in features if x[1] is not None])
    return median_error


def compute_accuracy_vs_number_of_vps(available_vps, rtt_per_srcs_dst, vp_coordinates_per_ip,
                                      vp_distance_matrix, subset_sizes):
    random.seed(42)

    accuracy_vs_n_vps = {}
    for random_n_vp in subset_sizes:
        print(f"Starting computing for random VPs {random_n_vp}")
        median_error_cdf = []
        for trial in range(0, 100):
            median_error = compute_accuracy_vs_number_of_vps_impl(
                rtt_per_srcs_dst, vp_distance_matrix, available_vps, random_n_vp, vp_coordinates_per_ip)
            median_error_cdf.append(median_error)
        accuracy_vs_n_vps[random_n_vp] = median_error_cdf
    return accuracy_vs_n_vps


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
        else:
            allowed_dsts = set()
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

        if dst in removed_anchors or dst not in vp_distance_matrix:
            continue

        for probe, rtts in rtts_per_src.items():
            if probe in removed_anchors:
                continue
            min_rtt_probe = min(rtts)
            if probe not in vp_distance_matrix[dst]:
                continue
            max_theoretical_distance = (
                SPEED_OF_INTERNET * min_rtt_probe / 1000) / 2
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


def round_based_algorithm_impl(dst, rtt_per_src, vp_coordinates_per_ip, vps_per_target_greedy, asn_per_vp, threshold):
    # Only take the first n_vps
    vp_coordinates_per_ip_allowed = {x: vp_coordinates_per_ip[x] for x in vp_coordinates_per_ip if
                                     x in vps_per_target_greedy}
    guessed_geolocation_circles = select_best_guess_centroid(
        dst, vp_coordinates_per_ip_allowed, rtt_per_src)
    if guessed_geolocation_circles is None:
        return dst, None, None
    guessed_geolocation, circles = guessed_geolocation_circles
    # Then take one probe per AS, city in the zone
    probes_in_intersection = {}
    for probe, probe_coordinates in vp_coordinates_per_ip.items():
        is_in_intersection = True
        for circle in circles:
            lat_c, long_c, rtt_c, d_c, r_c = circle
            if not is_within_cirle((lat_c, long_c), rtt_c, probe_coordinates, speed_threshold=2/3):
                is_in_intersection = False
                break
        if is_in_intersection:
            probes_in_intersection[probe] = probe_coordinates

    # Now only take one probe per AS/city in the probes in intersection
    selected_probes_per_asn = {}
    for probe in probes_in_intersection:
        asn = asn_per_vp[probe]
        if asn not in selected_probes_per_asn:
            selected_probes_per_asn.setdefault(asn, []).append(probe)
            continue
        else:
            is_already_found_close = False
            for selected_probe in selected_probes_per_asn[asn]:
                distance = haversine(
                    vp_coordinates_per_ip[probe], vp_coordinates_per_ip[selected_probe])
                if distance < threshold:
                    is_already_found_close = True
                    break
            if not is_already_found_close:
                # Add this probe to the selected as we do not already have the same probe.
                selected_probes_per_asn[asn].append(probe)

    selected_probes = set()
    for _, probes in selected_probes_per_asn.items():
        selected_probes.update(probes)

    vp_coordinates_per_ip_tier2 = {x: vp_coordinates_per_ip[x]
                                   for x in vp_coordinates_per_ip
                                   if x in selected_probes}
    vp_coordinates_per_ip_tier2[dst] = vp_coordinates_per_ip[dst]
    # Now evaluate the error with this subset of probes
    error, circles = compute_error(
        dst, vp_coordinates_per_ip_tier2, rtt_per_src)
    return dst, error, len(selected_probes)


def round_based_algorithm(greedy_probes, rtt_per_srcs_dst, vp_coordinates_per_ip,
                          asn_per_vp, n_vps,
                          threshold):
    """
    First is to use a subset of greedy probes, and then take 1 probe/AS in the given CBG area
    :param greedy_probes:
    :return:
    """

    vps_per_target_greedy = set(greedy_probes[:n_vps])

    args = []
    for i, (dst, rtt_per_src) in enumerate(sorted(rtt_per_srcs_dst.items())):
        if dst not in vp_coordinates_per_ip:
            continue
        args.append((dst, rtt_per_src, vp_coordinates_per_ip,
                    vps_per_target_greedy, asn_per_vp, threshold))
    with Pool(24) as p:
        results = p.starmap(round_based_algorithm_impl, args)
        return results


########## STREET LEVEL ##########

def every_tier_result(data):
    # data of one target if one tier is not succesful we take the previous one
    # for t1 we take cbg center, t2 the center of intercection cercles from the landmarks, t3 "closest" landmarks, t4 best landmark
    lat = 0
    lon = 0
    res = {'lat1': 0, 'lon1': 0, 'lat2': 0, 'lon2': 0,
           'lat3': 0, 'lon3': 0, 'lat4': 0, 'lon4': 0}
    if not data['tier1:done']:
        print("Tier1 Failed")
        return res
    lat = data['tier1:lat']
    lon = data['tier1:lon']
    res['lat1'] = lat
    res['lon1'] = lon

    best_dist = 50000
    best_correct_lat = None
    best_correct_lon = None
    for f in ['tier2:landmarks', 'tier3:landmarks']:
        if f in data:
            for _, _, l_lat, l_lon in data[f]:
                dist = haversine(
                    (l_lat, l_lon), (data['lat_c'], data['lon_c']))
                if dist < best_dist:
                    best_dist = dist
                    best_correct_lat = l_lat
                    best_correct_lon = l_lon

    if best_correct_lat != None and best_correct_lon != None:
        res['lat4'] = best_correct_lat
        res['lon4'] = best_correct_lon

    best_dist = 50000
    chosen_lat = None
    chosen_lon = None
    for f in ['tier2:traceroutes', 'tier3:traceroutes']:
        if f in data:
            for _, _, _, _, rtt, l_lat, l_lon, _ in data[f]:
                if rtt < 0:
                    continue
                if rtt < best_dist:
                    best_dist = rtt
                    chosen_lat = l_lat
                    chosen_lon = l_lon

    if chosen_lat != None and chosen_lon != None:
        res['lat3'] = chosen_lat
        res['lon3'] = chosen_lon

    if not data['tier2:done']:
        res['lat2'] = res['lat1']
        res['lon2'] = res['lon1']
        if chosen_lat == None or chosen_lon == None:
            res['lat3'] = res['lat1']
            res['lon3'] = res['lon1']
        if best_correct_lat == None or best_correct_lon == None:
            res['lat4'] = res['lat1']
            res['lon4'] = res['lon1']
        return res

    points = circle_intersections(
        data['tier2:final_circles'], data['speed_threshold'])
    if len(points) > 0:
        lat, lon = polygon_centroid(points)
        res['lat2'] = lat
        res['lon2'] = lon
    else:
        res['lat2'] = res['lat1']
        res['lon2'] = res['lon1']

    if not data['tier3:done']:
        if chosen_lat == None or chosen_lon == None:
            res['lat3'] = res['lat2']
            res['lon3'] = res['lon2']
        else:
            res['lat3'] = chosen_lat
            res['lon3'] = chosen_lon
        if best_correct_lon == None or best_correct_lat == None:
            res['lat4'] = res['lat1']
            res['lon4'] = res['lon1']
        return res

    if best_correct_lon != None and best_correct_lat != None:
        res['lat4'] = best_correct_lat
        res['lon4'] = best_correct_lon
    else:
        res['lat4'] = res['lat1']
        res['lon4'] = res['lon1']

    return res


def every_tier_result_and_errors(data):
    res = every_tier_result(data)
    res['error1'] = haversine(
        (res['lat1'], res['lon1']), (data['lat_c'], data['lon_c']))
    res['error2'] = haversine(
        (res['lat2'], res['lon2']), (data['lat_c'], data['lon_c']))
    res['error3'] = haversine(
        (res['lat3'], res['lon3']), (data['lat_c'], data['lon_c']))
    res['error4'] = haversine(
        (res['lat4'], res['lon4']), (data['lat_c'], data['lon_c']))
    return res
