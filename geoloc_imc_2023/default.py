from pathlib import Path


# Default path
DEFAULT_DIR: Path = Path(__file__).resolve().parent

# output path
LOG_PATH: Path = DEFAULT_DIR / "../log/"
CACHE_PATH: Path = DEFAULT_DIR / "../cache/"
RESULT_PATH: Path = DEFAULT_DIR / "../result/"
MEASUREMENT_CONFIG_PATH: Path = DEFAULT_DIR / "../measurement_config/"

# file path
HITLIST_FILE: Path = DEFAULT_DIR / "../datasets/parsed_hitlist.pickle"
ANCHORS_FILE: Path = DEFAULT_DIR / "../datasets/anchors.pickle"
PROBES_FILE: Path = DEFAULT_DIR / "../datasets/probes.pickle"

# cache files
ANCHOR_TARGET_ANCHOR_VP: Path = DEFAULT_DIR / "../cache/anchor_target_anchor_vp.pickle"
ANCHOR_TARGET_PROBE_VP: Path = DEFAULT_DIR / "../cache/anchor_target_probe_vp.pickle"
ANCHOR_PREFIX_ANCHOR_VP: Path = DEFAULT_DIR / "../cache/anchor_prefix_anchor_vp.pickle"
ANCHOR_PREFIX_PROBE_VP: Path = DEFAULT_DIR / "../cache/anchor_prefix_probe_vp.pickle"

# constant
MAX_NUMBER_OF_VPS = 1000
NB_MAX_CONCURRENT_MEASUREMENTS = 90
NB_PACKETS = 3
NB_TARGETS_PER_PREFIX = 3

# RIPE atlas credentials
RIPE_CREDENTIALS = {
    "username": "timur.friedman@sorbonne-universite.fr",
    "key": "b3d3d4fc-724e-4505-befe-1ad16a70dc87",
}
