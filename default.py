from pathlib import Path


# Default path
DEFAULT_DIR: Path = Path(__file__).resolve().parent

# dir path
RESULT_MILLION_SCALE_PATH: Path = DEFAULT_DIR / "measurements/million_scale/"
RESULT_STREET_LEVEL_PATH: Path = DEFAULT_DIR / "measurements/street_level/"
ATLAS_PATH: Path = DEFAULT_DIR / \
    "utils/datasets/atlas/"
GEOGRAPHIC_PATH: Path = DEFAULT_DIR / "utils/datasets/geography/"
MEASUREMENT_CONFIG_PATH: Path = DEFAULT_DIR / \
    "utils/measurement_config/"
FIGURE_PATH: Path = DEFAULT_DIR / "analysis/figures/"

# datasets files
HITLIST_FILE: Path = ATLAS_PATH / "parsed_hitlist.pickle"
ADDRESS_FILE: Path = ATLAS_PATH / \
    "internet_address_verfploeter_hitlist_it102w-20230125.fsdb"
ANCHORS_FILE: Path = ATLAS_PATH / "anchors.pickle"
PROBES_FILE: Path = ATLAS_PATH / "probes.pickle"
PROBES_AND_ANCHORS_FILE: Path = ATLAS_PATH / "probes_and_anchors.pickle"
REMOVED_PROBES_FILE: Path = ATLAS_PATH / "removed_probes.json"

ALL_ANCHORS_FILE: Path = ATLAS_PATH / "anchors_file.json"
ALL_PROBES_FILE: Path = ATLAS_PATH / "probes_file.json"
ALL_PROBES_AND_ANCHORS_FILE: Path = ATLAS_PATH / "probes_and_anchors_file.json"
GOOD_ANCHORS_FILE_PATH: Path = ATLAS_PATH / "good_anchors_file.json"
BAD_ANCHORS_FILE: Path = ATLAS_PATH / "bad_anchors_file.json"

COUNTRIES_PICKLE_FILE: Path = GEOGRAPHIC_PATH / "countries.pickle"
COUNTRIES_TXT_FILE: Path = GEOGRAPHIC_PATH / "countries.txt"

POPULATION_CITY_FILE: Path = GEOGRAPHIC_PATH / "population_target.json"

# result files
TARGET_ANCHOR_VP: Path = RESULT_MILLION_SCALE_PATH / "target_anchor_vp.pickle"
TARGET_PROBE_VP: Path = RESULT_MILLION_SCALE_PATH / "target_probe_vp.pickle"
PREFIX_ANCHOR_VP: Path = RESULT_MILLION_SCALE_PATH / "prefix_anchor_vp.pickle"
PREFIX_PROBE_VP: Path = RESULT_MILLION_SCALE_PATH / "prefix_probe_vp.pickle"
TARGET_ALL_VP: Path = RESULT_MILLION_SCALE_PATH / "target_all_vp.pickle"

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

# RIPE atlas credentials
RIPE_CREDENTIALS = {
    "username": "timur.friedman@sorbonne-universite.fr",
    "key": "b3d3d4fc-724e-4505-befe-1ad16a70dc87",
}


# Omar à régler
SERVER1_ANCHORS_FILE_PATH = 'anchors_file2.json'
SERVER2_ANCHORS_FILE_PATH = 'anchors_file1.json'


MISSING_TRACEROUTES_IDS_FILE_PATH = 'traceroutes_ids_to_get.json'
CACHED_WEBSITES_FILE_PATH = 'websites.json'
TMP_GEOLOC_INFO_ONE_TARGET_FILE_PATH = 'all_info_geoloc.json'


IP_TO_ASN_FILE_PATH = '/srv/kevin/internet-measurements-metadata/resources/ip2as/routeviews/2022-03-28.dat'
# IP_TO_ASN_FILE_PATH = '/home/kvermeulen/street_lvl/street_lvl/2022-03-28.dat'
