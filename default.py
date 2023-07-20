from pathlib import Path


# Default path
DEFAULT_DIR: Path = Path(__file__).resolve().parent

# dir path
LOG_PATH: Path = DEFAULT_DIR / "log/"
RESULT_PATH: Path = DEFAULT_DIR / "measurements/results/"
ATLAS_PATH: Path = DEFAULT_DIR / \
    "measurements/anchors_probes_dataset/"
MEASUREMENT_CONFIG_PATH: Path = DEFAULT_DIR / \
    "measurements/measurement_config/"
FIGURE_PATH: Path = DEFAULT_DIR / "analysis/figures/"

# file path
HITLIST_FILE: Path = ATLAS_PATH / "parsed_hitlist.pickle"
ADDRESS_FILE: Path = ATLAS_PATH / \
    "internet_address_verfploeter_hitlist_it102w-20230125.fsdb"
ANCHORS_FILE: Path = ATLAS_PATH / "anchors.pickle"
PROBES_FILE: Path = ATLAS_PATH / "probes.pickle"
PROBES_AND_ANCHORS_FILE: Path = ATLAS_PATH / "probes_and_anchors.pickle"
COUNTRIES_PICKLE_FILE: Path = ATLAS_PATH / "countries.pickle"
COUNTRIES_TXT_FILE: Path = ATLAS_PATH / "countries.txt"

# result files
TARGET_ANCHOR_VP: Path = RESULT_PATH / "target_anchor_vp.pickle"
TARGET_PROBE_VP: Path = RESULT_PATH / "target_probe_vp.pickle"
PREFIX_ANCHOR_VP: Path = RESULT_PATH / "prefix_anchor_vp.pickle"
PREFIX_PROBE_VP: Path = RESULT_PATH / "prefix_probe_vp.pickle"
TARGET_ALL_VP: Path = RESULT_PATH / "target_all_vp.pickle"

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
