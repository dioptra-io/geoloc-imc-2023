from pathlib import Path


# Default path
DEFAULT_DIR: Path = Path(__file__).resolve().parent

# dir path
LOG_PATH: Path = DEFAULT_DIR / "../log/"
CACHE_PATH: Path = DEFAULT_DIR / "../cache/"
RESULT_PATH: Path = DEFAULT_DIR / "../result/"
DATA_PATH: Path = DEFAULT_DIR / "../data/"
FIGURE_PATH: Path = DEFAULT_DIR / "../figures/"

MEASUREMENT_CONFIG_PATH: Path = DEFAULT_DIR / "../measurement_config/"

# file path
HITLIST_FILE: Path = DEFAULT_DIR / "../datasets/parsed_hitlist.pickle"
ANCHORS_FILE: Path = DEFAULT_DIR / "../datasets/anchors.pickle"
PROBES_FILE: Path = DEFAULT_DIR / "../datasets/probes.pickle"
ALL_ATLAS_PROBES_FILE: Path = DEFAULT_DIR / "../datasets/all_atlas_probes.pickle"
REMOVED_PROBES: Path = DEFAULT_DIR / "../datasets/removed_probes.json"

# dataset files
ANCHOR_TARGET_ANCHOR_VP: Path = DATA_PATH / "anchor_target_anchor_vp.pickle"
ANCHOR_TARGET_PROBE_VP: Path = DATA_PATH / "anchor_target_probe_vp.pickle"
ANCHOR_PREFIX_ANCHOR_VP: Path = DATA_PATH / "anchor_prefix_anchor_vp.pickle"
ANCHOR_PREFIX_PROBE_VP: Path = DATA_PATH / "anchor_prefix_probe_vp.pickle"
ANCHOR_TARGET_ALL_VP: Path = DATA_PATH / "anchor_target_all_vp.pickle"

# results files
ANCHOR_TARGET_ANCHOR_VP_RESULT_FILE = (
    DATA_PATH / "anchor_target_anchor_vp_result_file.pickle"
)
ANCHOR_TARGET_PROBE_VP_RESULT_FILE = (
    DATA_PATH / "anchor_target_probe_vp_result_file.pickle"
)

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
