threshold_distances = [0, 40, 100, 500, 1000]
anchor_to_anchors_results_file = "resources/replicability/cbg_thresholds_anchors_to_anchors.json"
probes_to_anchors_results_file = "resources/replicability/cbg_thresholds_probes_to_anchors.json"
probes_to_anchors_single_results_file = "resources/replicability/cbg_thresholds_probes_to_anchors_single.json"
rtts_per_closest_probes_file = "resources/replicability/rtts_per_closest_probes.json"
n_vps_selection_algorithm = [1, 3, 10]
vp_selection_algorithms_results_files = [f"resources/replicability/vp_selection_algorithm_{n_vp}.json"
                                         for n_vp in n_vps_selection_algorithm]
vp_selection_algorithms_probes_results_files = [f"resources/replicability/vp_selection_algorithm_probes_{n_vp}.json"
                                                for n_vp in n_vps_selection_algorithm]
fixed_set_probes_one_per_city_file = "resources/replicability/cbg_thresholds_fixed_set_probes_one_per_city.json"
fixed_set_probes_one_per_city_asn_file = "resources/replicability/cbg_thresholds_fixed_set_probes_one_per_city_asn.json"

accuracy_vs_n_vps_file = "resources/replicability/accuracy_vs_n_vps.json"
accuracy_vs_n_vps_probes_file = "resources/replicability/accuracy_vs_n_vps_probes.json"

min_rtt_per_dst_file = "resources/replicability/min_rtt_per_dst.json"
removed_probes_file = "resources/replicability/removed_probes.json"

pairwise_distance_file = "resources/ripe/pairwise_distance_ripe_probes.json"

greedy_anchors_file = "resources/replicability/greedy_anchors.json"
greedy_probes_file = "resources/replicability/greedy_probes.json"

round_based_algorithm_file = "resources/replicability/round_based_algorithm_error_cdf.json"

