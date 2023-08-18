import ipaddress
import numpy as np
import random
import os.path

from multiprocessing.pool import Pool

from utils.file_utils import load_json, dump_json
from utils.common import compute_error, get_prefix_from_ip
from default import SPEED_OF_INTERNET


def compute_geolocation_features_per_ip_impl(dst, rtt_per_src, vps_per_target,
                                             vp_coordinates_per_ip, vp_distance_matrix_dst,
                                             threshold_distances,
                                             distance_operator, max_vps,
                                             is_use_prefix):
    # Debug
    # if dst != "102.222.106.178":
    #     continue
    features = {}

    if is_use_prefix:
        dst_prefix = get_prefix_from_ip(int(ipaddress.ip_address(dst)))
        dst_prefix = str(ipaddress.ip_address(dst_prefix))
        if dst_prefix not in vps_per_target:
            print(
                f"Error, prefix {dst_prefix} not in measurements for VP selection algorithm")
            return features
    else:
        if dst not in vps_per_target:
            return features
    # Compute error with different configurations
    errors = []

    for threshold_distance in threshold_distances:
        if is_use_prefix:
            vp_per_target_allowed = vps_per_target[dst_prefix]
        else:
            print(dst)
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
        # error, circles = 0, []
        errors.append((error, circles))
        features.setdefault(threshold_distance, []).append(
            (dst, error, len(circles)))

        # Debug
        # circle = list(circles_no_country)[0]
        # print(anchor_per_ip[ip_per_coordinates[circle[0], circle[1]]])

        if False:
            geographical_distances = [vp_distance_matrix[dst][s]
                                      for s in vp_distance_matrix[dst] if s != dst]
            min_geographical_distance = min(geographical_distances)
            min_rtts_l = [min(rtt_per_src[x])
                          for x in rtt_per_src if x in vp_coordinates_per_ip and x != dst]
            if len(min_rtts_l) > 0:
                min_rtt = min(min_rtts_l)
            else:
                min_rtt = None
            # min_topological_distance =
            features_ = [dst]
            for error, circles in errors:
                features_.append((error, len(circles)))
            features_.extend([min_geographical_distance, min_rtt])

            # print(features_)
    return features


def compute_geolocation_features_per_ip(rtt_per_srcs_dst, vp_coordinates_per_ip, threshold_distances,
                                        vps_per_target,
                                        distance_operator,
                                        max_vps,
                                        is_use_prefix,
                                        ip_per_coordinates, country_per_vp, vp_distance_matrix,
                                        anchor_per_ip,
                                        is_multiprocess=True):
    """
        Compute some features to get some scatter plots in functions of the accuracy
        Features are:
        Topological distance from the closest VP
        Geographical distance from the closest VP
        """
    features = {}
    args = []
    print("on est la")
    for dst, rtt_per_src in sorted(rtt_per_srcs_dst.items()):
        if dst not in vp_coordinates_per_ip:
            # We do not know the geolocation of the anchor.
            continue
        args.append((dst, rtt_per_src, vps_per_target, vp_coordinates_per_ip,
                     vp_distance_matrix[dst],
                     threshold_distances,
                     distance_operator, max_vps, is_use_prefix))
    print(len(args))
    # if len(batch) > 0:
    #     args.append((batch, vps_per_target, vp_coordinates_per_ip, vp_distance_matrix,
    #                  threshold_distances,
    #                  distance_operator, max_vps, is_use_prefix))

    if is_multiprocess:
        print("multi")
        with Pool(24) as p:
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


def compute_fixed_set_of_probes(rtt_per_srcs_dst, vp_coordinates_per_ip, vp_distance_matrix,
                                n_vps_per_granularity,
                                threshold,
                                is_with_as,
                                asn_per_vp):
    """

    :param rtt_per_srcs_dst:
    :param vp_coordinates_per_ip:
    :param vp_distance_matrix:
    :param threshold:
    :return:
    """

    vps_per_target = {}  # one per city
    min_rtt_per_target = {}
    for dst, rtt_per_src in rtt_per_srcs_dst.items():
        if dst not in vp_coordinates_per_ip:
            continue
        # Look if we already got one probe for this city
        is_already_found_close = False
        for _, target_vps in vps_per_target.items():
            for probe in target_vps:
                if probe in rtt_per_src:
                    if vp_distance_matrix[dst][probe] < threshold:
                        is_already_found_close = True
                        vps_per_target.setdefault(dst, []).append(probe)
                        min_rtt_per_target.setdefault(
                            dst, []).append(min(rtt_per_src[probe]))

            if is_already_found_close:
                break
        if is_already_found_close:
            continue
        # Otherwise find one in terms of distance
        closest_probes = {vp: vp_distance_matrix[dst][vp] for vp in vp_distance_matrix[dst]
                          if vp_distance_matrix[dst][vp] < threshold
                          and vp in vp_coordinates_per_ip
                          and vp in rtt_per_src}

        if len(closest_probes) > 0:
            if is_with_as:
                # Take all the probes with different ASes and distance
                closest_probes_per_asn = {}
                for vp in closest_probes:
                    asn = asn_per_vp[vp]
                    if asn is not None:
                        closest_probes_per_asn.setdefault(asn, []).append(vp)
                for asn in closest_probes_per_asn:
                    random_probes = random.sample(closest_probes_per_asn[asn], min(
                        n_vps_per_granularity, len(closest_probes_per_asn[asn])))
                    vps_per_target.setdefault(dst, []).extend(random_probes)
                    min_rtt_per_target.setdefault(dst, []).extend([min(rtt_per_src[random_probe])
                                                                   for random_probe in random_probes])
            else:
                # Take a random probe amongst the available ones
                random_probes = random.sample(list(closest_probes), min(
                    n_vps_per_granularity, len(closest_probes)))
                vps_per_target[dst] = random_probes
                min_rtt_per_target[dst] = [
                    min(rtt_per_src[random_probe]) for random_probe in random_probes]

    return vps_per_target, min_rtt_per_target


def compute_closest_probes(rtt_per_srcs_dst, vp_coordinates_per_ip, vp_distance_matrix, threshold, probes):
    """

    :param rtt_per_srcs_dst:
    :param vp_coordinates_per_ip:
    :param vp_distance_matrix:
    :return:
    """
    closest_probes_per_vp = {}

    for dst, rtt_per_src in rtt_per_srcs_dst.items():
        if dst not in vp_coordinates_per_ip:
            continue
        # Compute the closest in terms of distance
        closest_probes = {vp: vp_distance_matrix[dst][vp] for vp in vp_distance_matrix[dst]
                          if vp_distance_matrix[dst][vp] < threshold and vp in vp_coordinates_per_ip}
        closest_probes_per_vp[dst] = closest_probes
        # Look at the RTTs of those probes
        # rtts_dist = [(vp, probe_per_ip[vp]["asn_v4"], min(rtt_per_src[vp])) for vp in closest_probes if vp in rtt_per_src]
        # if len(rtts_dist) == 0:
        #     continue

    return closest_probes_per_vp


def compute_redundancy_probes(rtt_per_srcs_dst, vp_coordinates_per_ip, closest_probes_per_dst):
    """

    :param rtt_per_srcs_dst:
    :param vp_coordinates_per_ip:
    :return:
    """
    redundant_probes = set()
    rtts_per_src = {}
    for dst, rtt_srcs in rtt_per_srcs_dst.items():
        if dst not in vp_coordinates_per_ip or dst not in closest_probes_per_dst:
            continue
        for src, rtts in rtt_srcs.items():
            rtts_per_src.setdefault(src, {})[dst] = rtts

    # Precompute which VPs should be compared
    to_compare_per_src = {}
    for dst, closest_probes in closest_probes_per_dst.items():
        for probe in closest_probes:
            to_compare_per_src.setdefault(probe, set()).update(closest_probes)

    rtts_per_src_l = list(rtts_per_src.items())
    # Check if one probe is always worse than another
    for i in range(len(rtts_per_src_l)):
        if i % 100 == 0:
            print(i)
        src_i, rtts_per_dst_i = rtts_per_src_l[i]
        if src_i not in to_compare_per_src:
            continue
        for j in range(i+1, len(rtts_per_src_l)):
            src_j, rtts_per_dst_j = rtts_per_src_l[j]
            if src_j not in to_compare_per_src[src_i]:
                continue
            # Compare them
            always_worse = True
            for dst in rtts_per_dst_i:
                if dst not in closest_probes_per_dst:
                    continue
                if not (src_i in closest_probes_per_dst[dst] and src_j in closest_probes_per_dst[dst]):
                    # Not a destination close to the two VPs
                    continue
                if dst in rtts_per_dst_j:
                    if rtts_per_dst_i[dst] < rtts_per_dst_j[dst]:
                        always_worse = False
                        break
                else:
                    always_worse = False
                    break

            if always_worse:
                # Remove the probe from the dataset
                redundant_probes.add(src_i)
                break

    return redundant_probes


def compute_closest_rtt_probes(rtts_per_dst_prefix, vp_coordinates_per_ip, vp_distance_matrix, is_prefix, n_shortest=10):

    vps_per_prefix = {}
    min_rtt_per_target = {}
    for dst, src_min_rtt in rtts_per_dst_prefix.items():
        if not is_prefix:
            if dst not in vp_coordinates_per_ip:
                continue
        sorted_probes = sorted(src_min_rtt.items(), key=lambda x: x[1][0])

        n_shortest_probes = dict(sorted_probes[:n_shortest])
        # Check if the shortest probes respect the speed of Internet
        n_shortest_probes_checked = {}
        min_rtt_probe, min_rtt = None, 1000
        if not is_prefix:
            for probe, rtts in n_shortest_probes.items():
                min_rtt_probe = min(rtts)
                if probe not in vp_distance_matrix[dst]:
                    continue
                max_theoretical_distance = (
                    SPEED_OF_INTERNET * min_rtt_probe/1000) / 2
                if vp_distance_matrix[dst][probe] > max_theoretical_distance:
                    # Impossible distance
                    continue
                n_shortest_probes_checked[probe] = n_shortest_probes[probe]
                if min_rtt_probe < min_rtt:
                    min_rtt_probe, min_rtt = probe, min_rtt_probe
            min_rtt_per_target[dst] = min_rtt
        else:
            n_shortest_probes_checked = n_shortest_probes
            min_rtt_per_target[dst] = min(sorted_probes[0][1])

        vps_per_prefix[dst] = n_shortest_probes_checked

    return vps_per_prefix, min_rtt_per_target


def compute_accuracy_vs_number_of_vps_impl(rtt_per_srcs_dst, vp_distance_matrix, available_vps, random_n_vp, vp_coordinates_per_ip,
                                           ip_per_coordinates, country_per_vp, probe_per_ip):
    # def compute_accuracy_vs_number_of_vps_impl(random_n_vp):
    #     rtt_per_srcs_dst = load_json(rtt_per_srcs_dst_tmp_file)
    #     vp_distance_matrix = load_json(vp_distance_matrix_tmp_file)
    print(f"Starting computing for random VPs {random_n_vp}")
    random_vps = random.sample(list(available_vps), random_n_vp)
    vps_per_target = {x: set(random_vps) for x in rtt_per_srcs_dst}
    features = compute_geolocation_features_per_ip(rtt_per_srcs_dst, vp_coordinates_per_ip,
                                                   [0],
                                                   vps_per_target=vps_per_target,
                                                   distance_operator=">", max_vps=100000,
                                                   is_use_prefix=False,
                                                   ip_per_coordinates=ip_per_coordinates,
                                                   country_per_vp=country_per_vp,
                                                   vp_distance_matrix=vp_distance_matrix,
                                                   anchor_per_ip=probe_per_ip,
                                                   is_multiprocess=True
                                                   )
    #
    features = features[0]
    median_error = np.median([x[1] for x in features if x[1] is not None])
    print("Median error", median_error)
    return median_error


def compute_accuracy_vs_number_of_vps(available_vps, rtt_per_srcs_dst, vp_coordinates_per_ip,
                                      ip_per_coordinates, country_per_vp,
                                      vp_distance_matrix, probe_per_ip, subset_sizes, ofile):

    random.seed(42)
    # available_vps = [vp for vp in rtt_per_srcs_dst.keys() if vp in vp_coordinates_per_ip]

    if os.path.exists(ofile):
        accuracy_vs_n_vps = load_json(ofile)
    else:
        accuracy_vs_n_vps = {}

    for random_n_vp in subset_sizes:
        # if str(random_n_vp) in accuracy_vs_n_vps:
        #     continue
        args = []
        # dump_json(rtt_per_srcs_dst, rtt_per_srcs_dst_tmp_file)
        # dump_json(vp_distance_matrix, vp_distance_matrix_tmp_file)
        median_error_cdf = []
        for trial in range(0, 100):
            # args.append((available_vps, random_n_vp, rtt_per_srcs_dst, vp_coordinates_per_ip,
            #              ip_per_coordinates, country_per_vp, vp_distance_matrix, probe_per_ip))
            args.append((available_vps, random_n_vp, vp_coordinates_per_ip,
                         ip_per_coordinates, country_per_vp, probe_per_ip))
            median_error = compute_accuracy_vs_number_of_vps_impl(rtt_per_srcs_dst, vp_distance_matrix, available_vps, random_n_vp, vp_coordinates_per_ip,
                                                                  ip_per_coordinates, country_per_vp, probe_per_ip)
            median_error_cdf.append(median_error)
            # args.append(random_n_vp)
        # with ThreadPool(8) as p:
        #     median_errors_cdf = p.starmap(compute_accuracy_vs_number_of_vps_impl, args)
            # Select a random set of VPs
        accuracy_vs_n_vps[random_n_vp] = median_error_cdf
        dump_json(accuracy_vs_n_vps, ofile)
