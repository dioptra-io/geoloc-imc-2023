from pathlib import Path


# Default path
DEFAULT_DIR: Path = Path(__file__).resolve().parent


# dir path
RESULT_MILLION_SCALE_PATH: Path = DEFAULT_DIR / \
    "datasets/measurements/million_scale/"
RESULT_STREET_LEVEL_PATH: Path = DEFAULT_DIR / \
    "datasets/measurements/street_level/"
MEASUREMENT_CONFIG_PATH: Path = DEFAULT_DIR / \
    "datasets/million_scale/measurement_config/"
ATLAS_PATH: Path = DEFAULT_DIR / \
    "datasets/atlas/"
GEOGRAPHIC_PATH: Path = DEFAULT_DIR / "datasets/geography/"
VARIOUS_PATH: Path = DEFAULT_DIR / "datasets/various/"
FIGURE_PATH: Path = DEFAULT_DIR / "analysis/figures/"


# datasets files
# atlas
ANCHORS_FILE: Path = ATLAS_PATH / "anchors.json"
PROBES_FILE: Path = ATLAS_PATH / "probes.json"
PROBES_AND_ANCHORS_FILE: Path = ATLAS_PATH / "probes_and_anchors.json"
REMOVED_PROBES_FILE: Path = ATLAS_PATH / "removed_probes.json"
GOOD_ANCHORS_FILE: Path = ATLAS_PATH / "good_anchors.json"
BAD_ANCHORS_FILE: Path = ATLAS_PATH / "bad_anchors.json"

# geography
COUNTRIES_JSON_FILE: Path = GEOGRAPHIC_PATH / "countries.json"
COUNTRIES_TXT_FILE: Path = GEOGRAPHIC_PATH / "countries.txt"

POPULATION_CITY_FILE: Path = GEOGRAPHIC_PATH / "population.json"
CITIES_500_FILE: Path = GEOGRAPHIC_PATH / "cities500.txt"

# various files
PAIRWISE_DISTANCE_FILE = VARIOUS_PATH / "pairwise_distance_ripe_probes.json"
HITLIST_FILE: Path = VARIOUS_PATH / "parsed_hitlist.json"
ADDRESS_FILE: Path = VARIOUS_PATH / \
    "internet_address_verfploeter_hitlist_it102w-20230125.fsdb"


# result files
TARGET_ANCHOR_VP: Path = RESULT_MILLION_SCALE_PATH / "target_anchor_vp_test.json"
TARGET_PROBE_VP: Path = RESULT_MILLION_SCALE_PATH / "target_probe_vp_test.json"
PREFIX_ANCHOR_VP: Path = RESULT_MILLION_SCALE_PATH / "prefix_anchor_vp_test.json"
PREFIX_PROBE_VP: Path = RESULT_MILLION_SCALE_PATH / "prefix_probe_vp_test.json"
TARGET_ALL_VP: Path = RESULT_MILLION_SCALE_PATH / "target_all_vp_test.json"

LOCAL_SERVER_GEOLOC_BATCH_RESULTS_FILE: Path = RESULT_STREET_LEVEL_PATH / "all_res.json"
DIST_SERVER_GEOLOC_BATCH_RESULTS_FILE: Path = RESULT_STREET_LEVEL_PATH / "all_res2.json"
FINAL_ANALYSABLE_FILE: Path = RESULT_STREET_LEVEL_PATH / "final_all_res.json"
OLD_ANALYSABLE_FILE: Path = RESULT_STREET_LEVEL_PATH / "final_all_res_before_58.json"


# clickhouse
DB_HOST = "localhost"
GEO_REPLICATION_DB = "geolocation_replication"
ANCHORS_MESHED_PING_TABLE = f"anchors_meshed_pings"
PROBES_TO_ANCHORS_PING_TABLE = f"ping_10k_to_anchors"


# constant
MAX_NUMBER_OF_VPS = 1_000
NB_MAX_CONCURRENT_MEASUREMENTS = 90
NB_PACKETS = 3
NB_TARGETS_PER_PREFIX = 3
THRESHOLD_DISTANCES = [0, 40, 100, 500, 1000]
NB_VPS_SELECTION_ALGORITHM = [1, 3, 10]


# RIPE atlas credentials
RIPE_CREDENTIALS = {
    "username": "timur.friedman@sorbonne-universite.fr",
    "key": "b3d3d4fc-724e-4505-befe-1ad16a70dc87",
}


# Omar à régler

MISSING_TRACEROUTES_IDS_FILE: Path = 'traceroutes_ids_to_get.json'
CACHED_WEBSITES_FILE: Path = 'websites.json'
TMP_GEOLOC_INFO_ONE_TARGET_FILE: Path = 'all_info_geoloc.json'


IP_TO_ASN_FILE: Path = '/srv/kevin/internet-measurements-metadata/resources/ip2as/routeviews/2022-03-28.dat'
# IP_TO_ASN_FILE: Path = '/home/kvermeulen/street_lvl/street_lvl/2022-03-28.dat'


# Kevin à régler

anchor_to_anchors_results_file = "resources/replicability/cbg_thresholds_anchors_to_anchors.json"
probes_to_anchors_results_file = "resources/replicability/cbg_thresholds_probes_to_anchors.json"
probes_to_anchors_single_results_file = "resources/replicability/cbg_thresholds_probes_to_anchors_single.json"

rtts_per_closest_probes_file = "resources/replicability/rtts_per_closest_probes.json"

vp_selection_algorithms_results_files = [f"resources/replicability/vp_selection_algorithm_{n_vp}.json"
                                         for n_vp in NB_VPS_SELECTION_ALGORITHM]
vp_selection_algorithms_probes_results_files = [f"resources/replicability/vp_selection_algorithm_probes_{n_vp}.json"
                                                for n_vp in NB_VPS_SELECTION_ALGORITHM]

fixed_set_probes_one_per_city_file = "resources/replicability/cbg_thresholds_fixed_set_probes_one_per_city.json"
fixed_set_probes_one_per_city_asn_file = "resources/replicability/cbg_thresholds_fixed_set_probes_one_per_city_asn.json"

accuracy_vs_n_vps_file = "resources/replicability/accuracy_vs_n_vps.json"
accuracy_vs_n_vps_probes_file = "resources/replicability/accuracy_vs_n_vps_probes.json"

min_rtt_per_dst_file = "resources/replicability/min_rtt_per_dst.json"

pairwise_distance_file = "resources/ripe/pairwise_distance_ripe_probes.json"

greedy_anchors_file = "resources/replicability/greedy_anchors.json"
greedy_probes_file = "resources/replicability/greedy_probes.json"

round_based_algorithm_file = "resources/replicability/round_based_algorithm_error_cdf.json"
