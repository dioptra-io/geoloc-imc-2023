# All the reference paths to storing files are here. There are also some constants and information for the clickhouse database and Ripe Atlas API.

from pathlib import Path


# constant
THRESHOLD_DISTANCES = [0, 40, 100, 500, 1000]
SPEED_OF_LIGHT = 300000
SPEED_OF_INTERNET = SPEED_OF_LIGHT * 2 / 3


# clickhouse
DB_HOST = "localhost"
GEO_REPLICATION_DB = "geolocation_replication"
ANCHORS_MESHED_PING_TABLE = f"anchors_meshed_pings"
PROBES_TO_ANCHORS_PING_TABLE = f"ping_10k_to_anchors"
ANCHORS_TO_PREFIX_TABLE = f"anchors_to_prefix_pings"
PROBES_TO_PREFIX_TABLE = f"probes_to_prefix_pings"
TARGET_TO_LANDMARKS_PING_TABLE = f"targets_to_landmarks_pings"


# RIPE atlas credentials
# Enter your RIPE ATLAS credentials below
# username: email address
# key: password
RIPE_CREDENTIALS = {
    "username": "timur.friedman@sorbonne-universite.fr",
    "key": "b3d3d4fc-724e-4505-befe-1ad16a70dc87",
}


# Default path
DEFAULT_DIR: Path = Path(__file__).resolve().parent


# Atlas path
ATLAS_PATH: Path = DEFAULT_DIR / "datasets/atlas/"
ASNS_TYPES: Path = DEFAULT_DIR / "datasets/asns_types"

# files
ANCHORS_FILE: Path = ATLAS_PATH / "anchors.json"
PROBES_FILE: Path = ATLAS_PATH / "probes.json"
PROBES_AND_ANCHORS_FILE: Path = ATLAS_PATH / "probes_and_anchors.json"
REPRODUC_ANCHORS_FILE: Path = ATLAS_PATH / "reproducibility_anchors.json"
REPRODUC_PROBES_FILE: Path = ATLAS_PATH / "reproducibility_probes.json"
REMOVED_PROBES_FILE: Path = ATLAS_PATH / "removed_probes.json"
FILTERED_PROBES_FILE: Path = ATLAS_PATH / "filtered_probes.json"
GREEDY_PROBES_FILE: Path = ATLAS_PATH / "greedy_probes.json"
ASNS_TYPE_CAIDA: Path = ASNS_TYPES / "caida_enhanced_as_type.json"
ASNS_TYPE_STANFORD: Path = ASNS_TYPES / "AS_categories_stanford.json"


# Georgraphic path
GEOGRAPHIC_PATH: Path = DEFAULT_DIR / "datasets/geography/"

# files
COUNTRIES_JSON_FILE: Path = GEOGRAPHIC_PATH / "countries.json"
COUNTRIES_TXT_FILE: Path = GEOGRAPHIC_PATH / "countries.txt"
COUNTRIES_CSV_FILE: Path = GEOGRAPHIC_PATH / "iso_code_2.csv"
POPULATION_CITY_FILE: Path = GEOGRAPHIC_PATH / "population.json"
CITIES_500_FILE: Path = GEOGRAPHIC_PATH / "cities500.txt"
POPULATION_DENSITY_FILE: Path = (
    GEOGRAPHIC_PATH / "gpw_v4_population_density_rev11_2020_30_sec.tif"
)


# Various path
VARIOUS_PATH: Path = DEFAULT_DIR / "datasets/various/"

# files
PAIRWISE_DISTANCE_FILE = VARIOUS_PATH / "pairwise_distance_ripe_probes.json"
HITLIST_FILE: Path = VARIOUS_PATH / "parsed_hitlist.json"
ADDRESS_FILE: Path = (
    VARIOUS_PATH / "internet_address_verfploeter_hitlist_it102w-20230125.fsdb"
)
GEOLITE_FILE: Path = VARIOUS_PATH / "GeoLite2-City-Blocks-IPv4_20230516.tree"
IP_INFO_GEO_FILE: Path = VARIOUS_PATH / "ip_info_geo_anchors.json"
MAXMIND_GEO_FILE: Path = VARIOUS_PATH / "maxmind_free_geo_anchors.json"
GEOPAPIFY_1_FILE: Path = VARIOUS_PATH / "geocoded_by_geoapify-10_05_2023_0_500.csv"
GEOPAPIFY_2_FILE: Path = VARIOUS_PATH / "geocoded_by_geoapify-10_05_2023_500_last.csv"
IP_TO_ASN_FILE: Path = VARIOUS_PATH / "2022-03-28.dat"
ANCHORS_SECOND_PAPER_FILE: Path = VARIOUS_PATH / "anchors_ip_list.json"
CACHED_WEBSITES_FILE: Path = VARIOUS_PATH / "websites.json"
BGP_PRIFIXES_FILE: Path = VARIOUS_PATH / "bgp_prefixes.json"


# Measurements paths
MEASUREMENTS_MILLION_SCALE_PATH: Path = (
    DEFAULT_DIR / "measurements/million_scale_results/"
)
MEASUREMENTS_STREET_LEVEL_PATH: Path = (
    DEFAULT_DIR / "measurements/street_level_results/"
)
MEASUREMENT_CONFIG_PATH: Path = (
    DEFAULT_DIR / "measurements/million_scale_results/measurement_config/"
)

# Million scale files
TARGET_ANCHOR: Path = MEASUREMENTS_MILLION_SCALE_PATH / "target_ANCHOR.json"
TARGET_PROBE: Path = MEASUREMENTS_MILLION_SCALE_PATH / "target_PROBE.json"
PREFIX_ANCHOR: Path = MEASUREMENTS_MILLION_SCALE_PATH / "prefix_ANCHOR.json"
PREFIX_PROBE: Path = MEASUREMENTS_MILLION_SCALE_PATH / "prefix_PROBE.json"
TARGET_ALL_VP: Path = MEASUREMENTS_MILLION_SCALE_PATH / "target_all_vp.json"

# Street level file
ANALYZABLE_FILE: Path = MEASUREMENTS_STREET_LEVEL_PATH / "all_res.json"


# Analysis path
ANALYSIS_PATH: Path = DEFAULT_DIR / "analysis/results"

# files
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
    ANALYSIS_PATH / "vp_selection_algorithm_probes_10.json"
)
ACCURACY_VS_N_VPS_PROBES_FILE: Path = ANALYSIS_PATH / "accuracy_vs_n_vps_probes.json"
ROUND_BASED_ALGORITHM_FILE: Path = (
    ANALYSIS_PATH / "round_based_algorithm_error_cdf.json"
)


# Pdf path
PDF_PATH: Path = DEFAULT_DIR / "plot/pdf/"

# files
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
