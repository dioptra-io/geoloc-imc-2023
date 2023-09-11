# All the reference paths to storing files are here. There are also some constants and information for the clickhouse database and Ripe Atlas API.

from pathlib import Path

# Default path
DEFAULT_DIR: Path = Path(__file__).resolve().parent


##################################################################################################
# CONSTANTS                                                                                      #
##################################################################################################
THRESHOLD_DISTANCES = [0, 40, 100, 500, 1000]
SPEED_OF_LIGHT = 300000
SPEED_OF_INTERNET = SPEED_OF_LIGHT * 2 / 3


# Atlas path
ATLAS_PATH: Path = DEFAULT_DIR / "datasets/atlas/"
##################################################################################################
# REPRODUCIBILITY DATASET FILES (static)                                                         #
##################################################################################################
REPRO_PATH: Path = DEFAULT_DIR / "datasets/reproducibility_datasets/"
REPRO_ATLAS_PATH: Path = REPRO_PATH / "atlas/"
REPRO_GENERATED_PATH: Path = REPRO_PATH / "generated/"

REPRO_ANCHORS_FILE: Path = REPRO_ATLAS_PATH / "reproducibility_anchors.json"
REPRO_PROBES_FILE: Path = REPRO_ATLAS_PATH / "reproducibility_probes.json"
REPRO_PROBES_AND_ANCHORS_FILE: Path = (
    REPRO_ATLAS_PATH / "reproducibility_probes_and_anchors.json"
)

REPRO_PAIRWISE_DISTANCE_FILE: Path = (
    REPRO_GENERATED_PATH / "reproducibility_pairwise_distance_ripe_probes.json"
)
REPRO_REMOVED_PROBES_FILE: Path = (
    REPRO_GENERATED_PATH / "reproducibility_removed_probes.json"
)
REPRO_FILTERED_PROBES_FILE: Path = (
    REPRO_GENERATED_PATH / "reproducibility_filtered_probes.json"
)
REPRO_GREEDY_PROBES_FILE: Path = (
    REPRO_GENERATED_PATH / "reproducibility_greedy_probes.json"
)
REPRO_HITLIST_FILE: Path = REPRO_GENERATED_PATH / "reproducibility_parsed_hitlist.json"


##################################################################################################
# USER DATASET FILES (generated)                                                                 #
##################################################################################################
USER_PATH: Path = DEFAULT_DIR / "datasets/user_datasets/"
USER_ATLAS_PATH: Path = USER_PATH / "atlas/"
USER_GENERATED_PATH: Path = USER_PATH / "generated/"

USER_ANCHORS_FILE: Path = USER_ATLAS_PATH / "user_anchors.json"
USER_PROBES_FILE: Path = USER_ATLAS_PATH / "user_probes.json"
USER_PROBES_AND_ANCHORS_FILE: Path = USER_ATLAS_PATH / "user_probes_and_anchors.json"

USER_PAIRWISE_DISTANCE_FILE: Path = (
    USER_GENERATED_PATH / "user_pairwise_distance_ripe_probes.json"
)
USER_REMOVED_PROBES_FILE: Path = USER_GENERATED_PATH / "user_removed_probes.json"
USER_FILTERED_PROBES_FILE: Path = USER_GENERATED_PATH / "user_filtered_probes.json"
USER_GREEDY_PROBES_FILE: Path = USER_GENERATED_PATH / "user_greedy_probes.json"
USER_HITLIST_FILE: Path = USER_GENERATED_PATH / "user_parsed_hitlist.json"

##################################################################################################
# CLICKHOUSE SETTINGS                                                                            #
##################################################################################################
CLICKHOUSE_CLIENT_PATH = DEFAULT_DIR / "clickhouse/clickhouse"
CLICKHOUSE_HOST = "localhost"
CLICKHOUSE_DB = "geolocation_replication"
CLICKHOUSE_USER = "default"
CLICKHOUSE_PASSWORD = ""

ANCHORS_MESHED_PING_TABLE = "anchors_meshed_pings"
ANCHORS_TO_PREFIX_TABLE = "anchors_to_prefix_pings"
PROBES_TO_PREFIX_TABLE = "probes_to_prefix_pings"
TARGET_TO_LANDMARKS_PING_TABLE = "targets_to_landmarks_pings"
PROBES_TO_ANCHORS_PING_TABLE = "ping_10k_to_anchors"
ANCHORS_MESHED_TRACEROUTE_TABLE = "anchors_meshed_traceroutes"

CLICKHOUSE_STATIC_DATASET: Path = DEFAULT_DIR / "datasets/clickhouse_data"

ANCHORS_MESHED_PING_FILE = (
    CLICKHOUSE_STATIC_DATASET / f"{ANCHORS_MESHED_PING_TABLE}.zst"
)
ANCHORS_TO_PREFIX_FILE = CLICKHOUSE_STATIC_DATASET / f"{ANCHORS_TO_PREFIX_TABLE}.zst"
PROBES_TO_PREFIX_FILE = CLICKHOUSE_STATIC_DATASET / f"{PROBES_TO_PREFIX_TABLE}.zst"
TARGET_TO_LANDMARKS_PING_FILE = (
    CLICKHOUSE_STATIC_DATASET / f"{TARGET_TO_LANDMARKS_PING_TABLE}.zst"
)
PROBES_TO_ANCHORS_PING_FILE = (
    CLICKHOUSE_STATIC_DATASET / f"{PROBES_TO_ANCHORS_PING_TABLE}.zst"
)
ANCHORS_MESHED_TRACEROUTE_FILE = (
    CLICKHOUSE_STATIC_DATASET / f"{ANCHORS_MESHED_TRACEROUTE_TABLE}.zst"
)


##################################################################################################
# RIPE ATLAS VPS BIAS ANALYSIS                                                                   #
##################################################################################################
ASNS_TYPES: Path = DEFAULT_DIR / "datasets/asns_types"
ASNS_TYPE_CAIDA: Path = ASNS_TYPES / "caida_enhanced_as_type.json"
ASNS_TYPE_STANFORD: Path = ASNS_TYPES / "AS_categories_stanford.json"


##################################################################################################
# STATIC FILES                                                                                   #
##################################################################################################
STATIC_PATH: Path = DEFAULT_DIR / "datasets/static_datasets/"

COUNTRIES_JSON_FILE: Path = STATIC_PATH / "countries.json"
COUNTRIES_TXT_FILE: Path = STATIC_PATH / "countries.txt"
COUNTRIES_CSV_FILE: Path = STATIC_PATH / "iso_code_2.csv"
POPULATION_CITY_FILE: Path = STATIC_PATH / "population.json"
CITIES_500_FILE: Path = STATIC_PATH / "cities500.txt"
POPULATION_DENSITY_FILE: Path = (
    STATIC_PATH / "gpw_v4_population_density_rev11_2020_30_sec.tif"
)

ADDRESS_FILE: Path = (
    STATIC_PATH / "internet_address_verfploeter_hitlist_it102w-20230125.fsdb"
)
GEOLITE_FILE: Path = STATIC_PATH / "GeoLite2-City-Blocks-IPv4_20230516.tree"
IP_INFO_GEO_FILE: Path = STATIC_PATH / "ip_info_geo_anchors.json"
MAXMIND_GEO_FILE: Path = STATIC_PATH / "maxmind_free_geo_anchors.json"

GEOPAPIFY_1_FILE: Path = STATIC_PATH / "geocoded_by_geoapify-10_05_2023_0_500.csv"
GEOPAPIFY_2_FILE: Path = STATIC_PATH / "geocoded_by_geoapify-10_05_2023_500_last.csv"

IP_TO_ASN_FILE: Path = STATIC_PATH / "2022-03-28.dat"
ANCHORS_SECOND_PAPER_FILE: Path = STATIC_PATH / "anchors_ip_list.json"
CACHED_WEBSITES_FILE: Path = STATIC_PATH / "websites.json"
BGP_PRIFIXES_FILE: Path = STATIC_PATH / "bgp_prefixes.json"

##################################################################################################
# ANALYSIS RESULTS FILES                                                                         #
##################################################################################################

ANALYSIS_PATH: Path = DEFAULT_DIR / "analysis/results"
PROBES_TO_ANCHORS_RESULT_FILE: Path = (
    ANALYSIS_PATH / "cbg_thresholds_probes_to_anchors.json"
)
VP_SELECTION_ALGORITHM_PROBES_1_FILE: Path = (
    ANALYSIS_PATH / "vp_selection_algorithm_probes_1.json"
)
VP_SELECTION_ALGORITHM_PROBES_3_FILE: Path = (
    ANALYSIS_PATH / "vp_selection_algorithm_probes_3.json"
)
VP_SELECTION_ALGORITHM_PROBES_10_FILE: Path = (
    ANALYSIS_PATH / "vp_selection_algoxrithm_probes_10.json"
)
ACCURACY_VS_N_VPS_PROBES_FILE: Path = ANALYSIS_PATH / "accuracy_vs_n_vps_probes.json"
ROUND_BASED_ALGORITHM_FILE: Path = (
    ANALYSIS_PATH / "round_based_algorithm_error_cdf.json"
)

##################################################################################################
# MEASUREMENTS RESULTS FILES                                                                     #
##################################################################################################
MEASUREMENTS_MILLION_SCALE_PATH: Path = (
    DEFAULT_DIR / "measurements/results/million_scale/"
)
MEASUREMENTS_STREET_LEVEL_PATH: Path = (
    DEFAULT_DIR / "measurements/results/street_level/"
)
MEASUREMENT_CONFIG_PATH: Path = (
    DEFAULT_DIR / "measurements/results/million_scale/measurement_config/"
)

############## MILLION SCALE FILES
TARGET_ANCHOR: Path = MEASUREMENTS_MILLION_SCALE_PATH / "target_anchor.json"
TARGET_PROBE: Path = MEASUREMENTS_MILLION_SCALE_PATH / "target_probe.json"
TARGET_ALL_VP: Path = MEASUREMENTS_MILLION_SCALE_PATH / "target_all_vp.json"
PREFIX_ANCHOR: Path = MEASUREMENTS_MILLION_SCALE_PATH / "prefix_anchor.json"
PREFIX_PROBE: Path = MEASUREMENTS_MILLION_SCALE_PATH / "prefix_probe.json"

############## STREET LEVEL FILES
ANALYZABLE_FILE: Path = MEASUREMENTS_STREET_LEVEL_PATH / "all_res.json"


##################################################################################################
# FIGURES FILES                                                                                  #
##################################################################################################
PDF_PATH: Path = DEFAULT_DIR / "plot/pdf/"
GEO_DATABASE_FILE: Path = PDF_PATH / "geo_databases.pdf"
ACCURACY_VS_NB_VPS_FILE: Path = PDF_PATH / "accuracy_vs_n_vps_probes.pdf"
ACCURACY_VS_SUBSET_SIZES_FILE: Path = PDF_PATH / "accuracy_vs_subset_sizes.pdf"
CBG_THRESHOLD_PROBES_FILE: Path = PDF_PATH / "cbg_thresholds_probes.pdf"
CBG_THRESHOLD_VP_SELECTION_FILE: Path = PDF_PATH / "cbg_thresholds_vp_selection.pdf"
CBG_THRESHOLD_CONTINENT_FILE: Path = PDF_PATH / "cbg_thresholds_continent.pdf"
ROUND_ALGORITHM_ERROR_FILE: Path = PDF_PATH / "round_algorithm_error.pdf"
CLOSE_LANDMARK_FILE: Path = PDF_PATH / "cdf_close_landmark_check_log.pdf"
INVALID_RTT_FILE: Path = PDF_PATH / "invalid_rtt.pdf"
TIME_TO_GEOLOCATE_FILE: Path = PDF_PATH / "cdf_time_to_geolocate.pdf"
SCATTER_DISTANCE_FILE: Path = PDF_PATH / "scatter_md_vs_d.pdf"
SCATTER_DENSITY_FILE: Path = PDF_PATH / "scatter_density.pdf"
CDF_DENSITY_FILE: Path = PDF_PATH / "cdf_density.pdf"
