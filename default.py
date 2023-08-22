from pathlib import Path


# constant
THRESHOLD_DISTANCES = [0, 40, 100, 500, 1000]
SPEED_OF_LIGHT = 300000
SPEED_OF_INTERNET = SPEED_OF_LIGHT * 2/3


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


# Default path
DEFAULT_DIR: Path = Path(__file__).resolve().parent


# Atlas path
ATLAS_PATH: Path = DEFAULT_DIR / \
    "datasets/atlas/"

# files
ANCHORS_FILE: Path = ATLAS_PATH / "anchors.json"
PROBES_FILE: Path = ATLAS_PATH / "probes.json"
PROBES_AND_ANCHORS_FILE: Path = ATLAS_PATH / "probes_and_anchors.json"
REMOVED_PROBES_FILE: Path = ATLAS_PATH / "removed_probes.json"
FILTERED_PROBES_FILE: Path = ATLAS_PATH / "filtered_probes.json"
GREEDY_PROBES_FILE: Path = ATLAS_PATH / "greedy_probes.json"


# Georgraphic path
GEOGRAPHIC_PATH: Path = DEFAULT_DIR / "datasets/geography/"

# files
COUNTRIES_JSON_FILE: Path = GEOGRAPHIC_PATH / "countries.json"
COUNTRIES_TXT_FILE: Path = GEOGRAPHIC_PATH / "countries.txt"
COUNTRIES_CSV_FILE: Path = GEOGRAPHIC_PATH / "iso_code_2.csv"
POPULATION_CITY_FILE: Path = GEOGRAPHIC_PATH / "population.json"
CITIES_500_FILE: Path = GEOGRAPHIC_PATH / "cities500.txt"
POPULATION_DENSITY_FILE: Path = GEOGRAPHIC_PATH / \
    "gpw_v4_population_density_rev11_2020_30_sec.tif"


# Various path
VARIOUS_PATH: Path = DEFAULT_DIR / "datasets/various/"

# files
PAIRWISE_DISTANCE_FILE = VARIOUS_PATH / \
    "pairwise_distance_ripe_probes.json"
HITLIST_FILE: Path = VARIOUS_PATH / "parsed_hitlist.json"
ADDRESS_FILE: Path = VARIOUS_PATH / \
    "internet_address_verfploeter_hitlist_it102w-20230125.fsdb"
GEOLITE_FILE: Path = VARIOUS_PATH / "GeoLite2-City-Blocks-IPv4_20230516.tree"
IP_INFO_GEO_FILE: Path = VARIOUS_PATH / "ip_info_geo_anchors.json"
MAXMIND_GEO_FILE: Path = VARIOUS_PATH / "maxmind_free_geo_anchors.json"
GEOPAPIFY_1_FILE: Path = VARIOUS_PATH / \
    "geocoded_by_geoapify-10_05_2023_0_500.csv"
GEOPAPIFY_2_FILE: Path = VARIOUS_PATH / \
    "geocoded_by_geoapify-10_05_2023_500_last.csv"
IP_TO_ASN_FILE: Path = VARIOUS_PATH / "2022-03-28.dat"
ANCHORS_SECOND_PAPER_FILE: Path = VARIOUS_PATH / "anchors_ip_list.json"


# Measurements paths
MEASUREMENTS_MILLION_SCALE_PATH: Path = DEFAULT_DIR / \
    "datasets/measurements/million_scale/"
MEASUREMENTS_STREET_LEVEL_PATH: Path = DEFAULT_DIR / \
    "datasets/measurements/street_level/"
MEASUREMENT_CONFIG_PATH: Path = DEFAULT_DIR / \
    "datasets/million_scale/measurement_config/"

# Million scale files
TARGET_ANCHOR_VP: Path = MEASUREMENTS_MILLION_SCALE_PATH / \
    "target_anchor_vp_test.json"
TARGET_PROBE_VP: Path = MEASUREMENTS_MILLION_SCALE_PATH / "target_probe_vp_test.json"
PREFIX_ANCHOR_VP: Path = MEASUREMENTS_MILLION_SCALE_PATH / \
    "prefix_anchor_vp_test.json"
PREFIX_PROBE_VP: Path = MEASUREMENTS_MILLION_SCALE_PATH / "prefix_probe_vp_test.json"
TARGET_ALL_VP: Path = MEASUREMENTS_MILLION_SCALE_PATH / "target_all_vp_test.json"

# Street level file
BASIC_ANALYSABLE_FILE: Path = MEASUREMENTS_STREET_LEVEL_PATH / "all_res.json"
FINAL_ANALYSABLE_FILE: Path = MEASUREMENTS_STREET_LEVEL_PATH / "final_all_res.json"


# Analysis path
ANALYSIS_PATH: Path = DEFAULT_DIR / "datasets/analysis/"

# files
PROBES_TO_ANCHORS_RESULT_FILE: Path = ANALYSIS_PATH / \
    "cbg_thresholds_probes_to_anchors.json"

VP_SELECTION_ALGORITHM_PROBES_1_FILE: Path = ANALYSIS_PATH / \
    "vp_selection_algorithm_probes_1.json"
VP_SELECTION_ALGORITHM_PROBES_3_FILE: Path = ANALYSIS_PATH / \
    "vp_selection_algorithm_probes_3.json"
VP_SELECTION_ALGORITHM_PROBES_10_FILE: Path = ANALYSIS_PATH / \
    "vp_selection_algorithm_probes_10.json"
ACCURACY_VS_N_VPS_PROBES_FILE: Path = ANALYSIS_PATH / \
    "accuracy_vs_n_vps_probes.json"
ROUND_BASED_ALGORITHM_FILE: Path = ANALYSIS_PATH / \
    "round_based_algorithm_error_cdf.json"


# Pdf path
PDF_PATH: Path = DEFAULT_DIR / "plot/pdf/"

# files
GEO_DATABASE_FILE: Path = PDF_PATH / "geo_databases.pdf"
FIG_3A_FILE: Path = PDF_PATH / "accuracy_vs_n_vps_probes_3a.pdf"
FIG_3B_FILE: Path = PDF_PATH / "accuracy_vs_n_vps_probes_3b.pdf"
CBG_THRESHOLD_BASIC_FILE: Path = PDF_PATH / "cbg_thresholds.pdf"
CBG_THRESHOLD_PROBES_FILE: Path = PDF_PATH / "cbg_thresholds_probes.pdf"
CBG_THRESHOLD_VP_SELECTION_FILE: Path = PDF_PATH / \
    "cbg_thresholds_vp_selection.pdf"
CBG_THRESHOLD_CONTINENT_FILE: Path = PDF_PATH / "cbg_thresholds_continent.pdf"
ROUND_ALGORITHM_ERROR_FILE: Path = PDF_PATH / "round_algorithm_error.pdf"
CLOSE_LANDMARK_FILE: Path = PDF_PATH / "cdf_close_landmark_check.pdf"
CLOSE_LANDMARK_LOG_FILE: Path = PDF_PATH / \
    "cdf_close_landmark_check_log.pdf"
CLOSE_LANDMARK_FILE_2: Path = PDF_PATH / "cdf_close_landmark_check_2.pdf"
CLOSE_LANDMARK_LOG_FILE_2: Path = PDF_PATH / \
    "cdf_close_landmark_check_2_log.pdf"


# Omar à régler
CACHED_WEBSITES_FILE: Path = 'websites.json'
TMP_GEOLOC_INFO_ONE_TARGET_FILE: Path = 'all_info_geoloc.json'
