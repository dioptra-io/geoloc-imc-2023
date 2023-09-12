from scripts.utils.file_utils import load_json, dump_json

from scripts.analysis.analysis import *
from default import *


if __name__ == "__main__":
    # set to True to use your own datasets/measurements
    run_repro = True
    if run_repro:
        PROBES_FILE = REPRO_PROBES_FILE
        PROBES_AND_ANCHORS_FILE = REPRO_PROBES_AND_ANCHORS_FILE
        FILTERED_PROBES_FILE = REPRO_FILTERED_PROBES_FILE
        GREEDY_PROBES_FILE = REPRO_GREEDY_PROBES_FILE
        PAIRWISE_DISTANCE_FILE = REPRO_PAIRWISE_DISTANCE_FILE

        # TODO: separate user's results from measurement
        PROBES_TO_ANCHORS_RESULT_FILE = PROBES_TO_ANCHORS_RESULT_FILE
    else:
        PROBES_FILE = USER_PROBES_FILE
        PROBES_AND_ANCHORS_FILE = USER_PROBES_AND_ANCHORS_FILE
        FILTERED_PROBES_FILE = USER_FILTERED_PROBES_FILE
        GREEDY_PROBES_FILE = USER_GREEDY_PROBES_FILE
        PAIRWISE_DISTANCE_FILE = USER_PAIRWISE_DISTANCE_FILE

        PROBES_TO_ANCHORS_RESULT_FILE = PROBES_TO_ANCHORS_RESULT_FILE

    LIMIT = 1000

    filtered_probes = load_json(FILTERED_PROBES_FILE)

    filter = ""
    if len(filtered_probes) > 0:
        # Remove probes that are wrongly geolocated
        in_clause = f"".join([f",toIPv4('{p}')" for p in filtered_probes])[1:]
        filter += f"AND dst not in ({in_clause}) AND src not in ({in_clause}) "

    logger.info("Compute errors")

    all_probes = load_json(PROBES_AND_ANCHORS_FILE)
    (
        vp_coordinates_per_ip,
        ip_per_coordinates,
        country_per_vp,
        asn_per_vp,
        vp_distance_matrix,
        probes_per_ip,
    ) = compute_geo_info(all_probes, PAIRWISE_DISTANCE_FILE)

    rtt_per_srcs_dst = compute_rtts_per_dst_src(
        PROBES_TO_ANCHORS_PING_TABLE, filter, threshold=70
    )

    vps_per_target = {
        dst: set(vp_coordinates_per_ip.keys()) for dst in rtt_per_srcs_dst
    }
    features = compute_geolocation_features_per_ip(
        rtt_per_srcs_dst,
        vp_coordinates_per_ip,
        THRESHOLD_DISTANCES,
        vps_per_target=vps_per_target,
        distance_operator=">",
        max_vps=100000,
        is_use_prefix=False,
        vp_distance_matrix=vp_distance_matrix,
    )

    logger.info("Compute errors")

    dump_json(features, PROBES_TO_ANCHORS_RESULT_FILE)

    all_probes = load_json(PROBES_AND_ANCHORS_FILE)

    asn_per_vp_ip = {}
    vp_coordinates_per_ip = {}

    for probe in all_probes:
        if (
            "address_v4" in probe
            and "geometry" in probe
            and "coordinates" in probe["geometry"]
        ):
            ip_v4_address = probe["address_v4"]
            if ip_v4_address is None:
                continue
            long, lat = probe["geometry"]["coordinates"]
            asn_v4 = probe["asn_v4"]
            asn_per_vp_ip[ip_v4_address] = asn_v4
            vp_coordinates_per_ip[ip_v4_address] = lat, long

    # clickhouse is required here
    rtt_per_srcs_dst = compute_rtts_per_dst_src(
        PROBES_TO_ANCHORS_PING_TABLE, filter, threshold=100
    )
    vp_distance_matrix = load_json(PAIRWISE_DISTANCE_FILE)

    TIER1_VPS = [10, 100, 300, 500, 1000]
    greedy_probes = load_json(GREEDY_PROBES_FILE)
    error_cdf_per_tier1_vps = {}
    for tier1_vps in TIER1_VPS:
        print(f"Using {tier1_vps} tier1_vps")
        error_cdf = round_based_algorithm(
            greedy_probes,
            rtt_per_srcs_dst,
            vp_coordinates_per_ip,
            asn_per_vp_ip,
            tier1_vps,
            threshold=40,
        )
        error_cdf_per_tier1_vps[tier1_vps] = error_cdf

    dump_json(error_cdf_per_tier1_vps, ROUND_BASED_ALGORITHM_FILE)

    logger.info("Accuracy vs number of vps probes")
    logger.warning("this step might takes several hours")

    all_probes = load_json(PROBES_AND_ANCHORS_FILE)

    (
        vp_coordinates_per_ip,
        ip_per_coordinates,
        country_per_vp,
        asn_per_vp,
        vp_distance_matrix,
        probe_per_ip,
    ) = compute_geo_info(all_probes, serialized_file=PAIRWISE_DISTANCE_FILE)

    logger.info("Accuracy vs number of vps probes")

    subset_sizes = []
    subset_sizes.extend([i for i in range(100, 1000, 100)])
    subset_sizes.extend([i for i in range(1000, 10001, 1000)])

    rtt_per_srcs_dst = compute_rtts_per_dst_src(
        PROBES_TO_ANCHORS_PING_TABLE, filter, threshold=50
    )

    available_vps = list(vp_coordinates_per_ip.keys())
    accuracy_vs_nb_vps = compute_accuracy_vs_number_of_vps(
        available_vps,
        rtt_per_srcs_dst,
        vp_coordinates_per_ip,
        vp_distance_matrix,
        subset_sizes,
    )

    dump_json(accuracy_vs_nb_vps, ACCURACY_VS_N_VPS_PROBES_FILE)

    logger.info("vp selection algorithm")

    all_probes = load_json(PROBES_AND_ANCHORS_FILE)

    (
        vp_coordinates_per_ip,
        ip_per_coordinates,
        country_per_vp,
        asn_per_vp,
        vp_distance_matrix,
        probes_per_ip,
    ) = compute_geo_info(all_probes, PAIRWISE_DISTANCE_FILE)

    ping_table_prefix = PROBES_TO_PREFIX_TABLE
    ping_table = PROBES_TO_ANCHORS_PING_TABLE
    N_VPS_SELECTION_ALGORITHM = [1, 3, 10]
    results_files = [
        VP_SELECTION_ALGORITHM_PROBES_1_FILE,
        VP_SELECTION_ALGORITHM_PROBES_3_FILE,
        VP_SELECTION_ALGORITHM_PROBES_10_FILE,
    ]

    rtt_per_srcs_dst_prefix = compute_rtts_per_dst_src(
        ping_table_prefix, filter, threshold=100, is_per_prefix=True
    )
    rtt_per_srcs_dst = compute_rtts_per_dst_src(ping_table, filter, threshold=70)

    for i, n_vp in enumerate(N_VPS_SELECTION_ALGORITHM):
        vps_per_target, _ = compute_closest_rtt_probes(
            rtt_per_srcs_dst_prefix,
            vp_coordinates_per_ip,
            vp_distance_matrix,
            n_shortest=n_vp,
            is_prefix=True,
        )
        features = compute_geolocation_features_per_ip(
            rtt_per_srcs_dst,
            vp_coordinates_per_ip,
            [0],
            vps_per_target=vps_per_target,
            distance_operator=">",
            max_vps=100000,
            is_use_prefix=True,
            vp_distance_matrix=vp_distance_matrix,
            is_multiprocess=True,
        )

        ofile = results_files[i]
        dump_json(features, ofile)
