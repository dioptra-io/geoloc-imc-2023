import os
import math
import numpy as np
from database.globals import GEO_REPLICATION_DB, DB_HOST, PROBES_TO_ANCHORS_PING_TABLE, ANCHORS_MESHED_PING_TABLE

from replicability.common import compute_rtts_per_dst_src, compute_geo_info, compute_error
from replicability.ripe_utils import download_ripe_probes
from replicability.globals import  *

from utils.utils import load_json, dump_json
from multiprocessing import Pool
from geohelp.helpers import select_best_guess_centroid, haversine, is_within_cirle

def greedy_selection_probes_impl(probe, distance_per_probe, selected_probes):

    distances_log = [math.log(distance_per_probe[p]) for p in selected_probes
                     if p in distance_per_probe and distance_per_probe[p] > 0]
    total_distance = sum(distances_log)
    return probe, total_distance

def greedy_selection_probes(vp_distance_matrix, removed_probes, country_per_vp, limit):


    # First of all remove entries with removed probes
    for probe in removed_probes:
        if probe in vp_distance_matrix:
            del vp_distance_matrix[probe]

    for probe, distance_per_probe in vp_distance_matrix.items():
        for removed_probe in removed_probes:
            if removed_probe in distance_per_probe:
                del distance_per_probe[removed_probe]

    print("Starting greedy algorithm")
    selected_probes = []
    remaining_probes = set(vp_distance_matrix.keys())
    with Pool(12) as p:
        while len(remaining_probes) > 0 and len(selected_probes) < limit:
            print(len(remaining_probes))
            args = []
            for probe in remaining_probes:
                args.append((probe, vp_distance_matrix[probe], selected_probes))

            results = p.starmap(greedy_selection_probes_impl, args)

            furthest_probe_from_selected, _ = max(results, key=lambda x:x[1])
            print(country_per_vp[furthest_probe_from_selected])
            selected_probes.append(furthest_probe_from_selected)
            remaining_probes.remove(furthest_probe_from_selected)

    return selected_probes

def round_based_algorithm_impl(dst, rtt_per_src, vp_coordinates_per_ip, vps_per_target_greedy, asn_per_vp, threshold):
    # Only take the first n_vps
    vp_coordinates_per_ip_allowed = {x: vp_coordinates_per_ip[x] for x in vp_coordinates_per_ip if
                                     x in vps_per_target_greedy}
    guessed_geolocation_circles = select_best_guess_centroid(dst, vp_coordinates_per_ip_allowed, rtt_per_src)
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
                distance = haversine(vp_coordinates_per_ip[probe], vp_coordinates_per_ip[selected_probe])
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
    error, circles = compute_error(dst, vp_coordinates_per_ip_tier2, rtt_per_src)
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
        args.append((dst, rtt_per_src, vp_coordinates_per_ip, vps_per_target_greedy, asn_per_vp, threshold))

    with Pool(24) as p:
        results = p.starmap(round_based_algorithm_impl, args)
        for result in results:
            print(result)
        return results


def evaluate():
    anchors, probes, all_probes = download_ripe_probes()

    is_compute_round_algorithm = True

    is_only_anchors_matrix = False
    if not is_only_anchors_matrix:
        vp_coordinates_per_ip, ip_per_coordinates, country_per_vp, asn_per_vp, \
        vp_distance_matrix, probe_per_ip = compute_geo_info(
            all_probes, serialized_file="resources/ripe/pairwise_distance_ripe_probes.json")

    else:
        vp_coordinates_per_ip, ip_per_coordinates, country_per_vp, asn_per_vp, \
        vp_distance_matrix, probe_per_ip = compute_geo_info(
            anchors, serialized_file="resources/ripe/pairwise_distance_anchors.json")
        # greedy_probes = load_json(greedy_probes_file)
        # for probe in greedy_probes:
        #     print(country_per_vp[probe])

    if os.path.exists(removed_probes_file):
        removed_probes = set(load_json(removed_probes_file))
    else:
        removed_probes = set()


    if is_compute_round_algorithm:

        # Greedily compute the probe with the greatest distance to other probes
        if not os.path.exists(greedy_probes_file):
            greedy_probes = greedy_selection_probes(vp_distance_matrix, removed_probes, country_per_vp, limit=1000)
            dump_json(greedy_probes, greedy_probes_file)
        else:
            greedy_probes = load_json(greedy_probes_file)

        filter = ""
        rtt_per_srcs_dst = compute_rtts_per_dst_src(PROBES_TO_ANCHORS_PING_TABLE, filter, threshold=100)
        tier1_vps_l = [10, 100, 300, 500, 1000]
        error_cdf_per_tier1_vps = {}
        if os.path.exists(round_based_algorithm_file):
            error_cdf_per_tier1_vps = load_json(round_based_algorithm_file)
            error_cdf_per_tier1_vps = {int(x) : error_cdf_per_tier1_vps[x] for x in error_cdf_per_tier1_vps}

        for tier1_vps in tier1_vps_l:
            # if tier1_vps in error_cdf_per_tier1_vps:
            #     continue
            print(f"Using {tier1_vps} tier1_vps")
            error_cdf = round_based_algorithm(greedy_probes, rtt_per_srcs_dst, vp_coordinates_per_ip,
                                              asn_per_vp,
                                              tier1_vps,
                                              threshold=40)
            error_cdf_per_tier1_vps[tier1_vps] = error_cdf
        dump_json(error_cdf_per_tier1_vps, round_based_algorithm_file)

if __name__ == "__main__":
    evaluate()
