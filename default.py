from pathlib import Path


# constant
MAX_NUMBER_OF_VPS = 1_000
NB_MAX_CONCURRENT_MEASUREMENTS = 90
NB_PACKETS = 3
NB_TARGETS_PER_PREFIX = 3
THRESHOLD_DISTANCES = [0, 40, 100, 500, 1000]
N_VPS_SELECTION_ALGORITHM = [1, 3, 10]
SPEED_OF_LIGHT = 300000
SPEED_OF_INTERNET = SPEED_OF_LIGHT * 2/3
POPULATION_THRESHOLD = 100000


# Default path
DEFAULT_DIR: Path = Path(__file__).resolve().parent


# dir path
MEASUREMENTS_MILLION_SCALE_PATH: Path = DEFAULT_DIR / \
    "datasets/measurements/million_scale/"
MEASUREMENTS_STREET_LEVEL_PATH: Path = DEFAULT_DIR / \
    "datasets/measurements/street_level/"
PDF_PATH: Path = DEFAULT_DIR / "datasets/pdf/"
ANALYSIS_PATH: Path = DEFAULT_DIR / "datasets/analysis/"
MEASUREMENT_CONFIG_PATH: Path = DEFAULT_DIR / \
    "datasets/million_scale/measurement_config/"
ATLAS_PATH: Path = DEFAULT_DIR / \
    "datasets/atlas/"
GEOGRAPHIC_PATH: Path = DEFAULT_DIR / "datasets/geography/"
VARIOUS_PATH: Path = DEFAULT_DIR / "datasets/various/"


# atlas
ANCHORS_FILE: Path = ATLAS_PATH / "anchors.json"
PROBES_FILE: Path = ATLAS_PATH / "probes.json"
PROBES_AND_ANCHORS_FILE: Path = ATLAS_PATH / "probes_and_anchors.json"
REMOVED_PROBES_FILE: Path = ATLAS_PATH / "removed_probes.json"
GREEDY_PROBES_FILE: Path = ATLAS_PATH / "greedy_probes.json"


# geography
COUNTRIES_JSON_FILE: Path = GEOGRAPHIC_PATH / "countries.json"
COUNTRIES_TXT_FILE: Path = GEOGRAPHIC_PATH / "countries.txt"
COUNTRIES_CSV_FILE: Path = GEOGRAPHIC_PATH / "countries_iso_code_2.csv"

POPULATION_CITY_FILE: Path = GEOGRAPHIC_PATH / "population.json"
CITIES_500_FILE: Path = GEOGRAPHIC_PATH / "cities500.txt"


# various files
PAIRWISE_DISTANCE_ANCHOR_FILE = VARIOUS_PATH / \
    "pairwise_distance_ripe_anchors.json"
PAIRWISE_DISTANCE_PROBE_FILE = VARIOUS_PATH / \
    "pairwise_distance_ripe_probes.json"

HITLIST_FILE: Path = VARIOUS_PATH / "parsed_hitlist.json"
ADDRESS_FILE: Path = VARIOUS_PATH / \
    "internet_address_verfploeter_hitlist_it102w-20230125.fsdb"

IP_INFO_GEO_FILE: Path = VARIOUS_PATH / "ip_info_geo_anchors.json"
MAXMIND_GEO_FILE: Path = VARIOUS_PATH / "maxmind_free_geo_anchors.json"


# pdf files
GEO_DATABASE_FILE: Path = PDF_PATH / "geo_databases.pdf"
CBG_THRESHOLD_BASIC_FILE: Path = PDF_PATH / "cbg_thresholds.pdf"
CBG_THRESHOLD_CIRCLES_FILE: Path = PDF_PATH / "cbg_thresholds_circles.pdf"
CBG_THRESHOLD_PROBES_FILE: Path = PDF_PATH / "cbg_thresholds_probes.pdf"
CBG_THRESHOLD_ALL_FILE: Path = PDF_PATH / "cbg_thresholds_all.pdf"
CBG_THRESHOLD_VP_SELECTION_FILE: Path = PDF_PATH / \
    "cbg_thresholds_vp_selection.pdf"
CBG_THRESHOLD_FIXED_SET_FILE: Path = PDF_PATH / "cbg_thresholds_fixed_set.pdf"
CBG_THRESHOLD_CONTINENT_FILE: Path = PDF_PATH / "cbg_thresholds_continent.pdf"
RTTS_PDF_FILE: Path = PDF_PATH / "rtts_per_closest_probe.pdf"
RTTS_FIXED_SET_FILE: Path = PDF_PATH / "rtts_fixed_set.pdf"
ROUND_ALGORITHM_ERROR_FILE: Path = PDF_PATH / "round_algorithm_error.pdf"
ROUND_ALGORITHM_VPS_FILE: Path = PDF_PATH / "round_algorithm_vps.pdf"
CLOSE_LANDMARK_FILE: Path = PDF_PATH / "cdf_close_landmark_check.pdf"
CLOSE_LANDMARK_LOG_FILE: Path = PDF_PATH / \
    "cdf_close_landmark_check_log.pdf"
CLOSE_LANDMARK_FILE_2: Path = PDF_PATH / "cdf_close_landmark_check_2.pdf"
CLOSE_LANDMARK_LOG_FILE_2: Path = PDF_PATH / \
    "cdf_close_landmark_check_2_log.pdf"

# important results
FIG_3A_FILE: Path = PDF_PATH / "accuracy_vs_n_vps_probes_3a.pdf"
FIG_3B_FILE: Path = PDF_PATH / "accuracy_vs_n_vps_probes_3b.pdf"


# result files
TARGET_ANCHOR_VP: Path = MEASUREMENTS_MILLION_SCALE_PATH / \
    "target_anchor_vp_test.json"
TARGET_PROBE_VP: Path = MEASUREMENTS_MILLION_SCALE_PATH / "target_probe_vp_test.json"
PREFIX_ANCHOR_VP: Path = MEASUREMENTS_MILLION_SCALE_PATH / \
    "prefix_anchor_vp_test.json"
PREFIX_PROBE_VP: Path = MEASUREMENTS_MILLION_SCALE_PATH / "prefix_probe_vp_test.json"
TARGET_ALL_VP: Path = MEASUREMENTS_MILLION_SCALE_PATH / "target_all_vp_test.json"

BASIC_ANALYSABLE_FILE: Path = MEASUREMENTS_STREET_LEVEL_PATH / "all_res.json"
FINAL_ANALYSABLE_FILE: Path = MEASUREMENTS_STREET_LEVEL_PATH / "final_all_res.json"


# pas top pour l'instant
ANCHORS_TO_ANCHORS_RESULT_FILE: Path = ANALYSIS_PATH / \
    "cbg_thresholds_anchors_to_anchors.json"
PROBES_TO_ANCHORS_RESULT_FILE: Path = ANALYSIS_PATH / \
    "cbg_thresholds_probes_to_anchors.json"

FIXED_SET_ONE_PROBE_PER_CITY_FILE: Path = ANALYSIS_PATH / \
    "cbg_thresholds_fixed_set_probes_one_per_city.json"
FIXED_SET_ONE_PROBE_PER_CITY_ASN_FILE: Path = ANALYSIS_PATH / \
    "cbg_thresholds_fixed_set_probes_one_per_city_asn.json"

VP_SELECTION_ALGORITHM_1_FILE: Path = ANALYSIS_PATH / \
    "vp_selection_algorithm_1.json"
VP_SELECTION_ALGORITHM_3_FILES: Path = ANALYSIS_PATH / \
    "vp_selection_algorithm_3.json"
VP_SELECTION_ALGORITHM_10_FILES: Path = ANALYSIS_PATH / \
    "vp_selection_algorithm_10.json"

VP_SELECTION_ALGORITHM_PROBES_1_FILE: Path = ANALYSIS_PATH / \
    "vp_selection_algorithm_probes_1.json"
VP_SELECTION_ALGORITHM_PROBES_3_FILE: Path = ANALYSIS_PATH / \
    "vp_selection_algorithm_probes_3.json"
VP_SELECTION_ALGORITHM_PROBES_10_FILE: Path = ANALYSIS_PATH / \
    "vp_selection_algorithm_probes_10.json"


RTTS_PER_CLOSEST_PROBES_FILE: Path = ANALYSIS_PATH / \
    "rtts_per_closest_probes.json"
MIN_RTT_PER_DIST_FILE: Path = ANALYSIS_PATH / "rmin_rtt_per_dst.json"
ACCURACY_VS_N_VPS_FILE = "accuracy_vs_n_vps.json"
ACCURACY_VS_N_VPS_PROBES_FILE: Path = ANALYSIS_PATH / \
    "accuracy_vs_n_vps_probes.json"
ROUND_BASED_ALGORITHM_FILE: Path = ANALYSIS_PATH / \
    "round_based_algorithm_error_cdf.json"

# clickhouse
DB_HOST = "localhost"
GEO_REPLICATION_DB = "geolocation_replication"
ANCHORS_MESHED_PING_TABLE = f"anchors_meshed_pings"
PROBES_TO_ANCHORS_PING_TABLE = f"ping_10k_to_anchors"
ANCHORS_TO_PREFIX_TABLE = f"anchors_to_prefix_pings"
PROBES_TO_PREFIX_TABLE = f"probes_to_prefix_pings"


# RIPE atlas credentials
RIPE_CREDENTIALS = {
    "username": "timur.friedman@sorbonne-universite.fr",
    "key": "b3d3d4fc-724e-4505-befe-1ad16a70dc87",
}


# Omar à régler
CACHED_WEBSITES_FILE: Path = 'websites.json'
TMP_GEOLOC_INFO_ONE_TARGET_FILE: Path = 'all_info_geoloc.json'


IP_TO_ASN_FILE: Path = '/srv/kevin/internet-measurements-metadata/resources/ip2as/routeviews/2022-03-28.dat'
# IP_TO_ASN_FILE: Path = '/home/kvermeulen/street_lvl/street_lvl/2022-03-28.dat'
