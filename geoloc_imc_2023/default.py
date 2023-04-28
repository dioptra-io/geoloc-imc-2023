from pathlib import Path


# Default path
DEFAULT_DIR: Path = Path(__file__).resolve().parent

# output path
LOG_PATH: Path = DEFAULT_DIR / "../log/"
RESULT_PATH: Path = DEFAULT_DIR / "../result/"
MEASUREMENT_CONFIG_PATH: Path = DEFAULT_DIR / "../measurement_config/"

# file path
HITLIST_FILE: Path = DEFAULT_DIR / "../datasets/parsed_hitlist.pickle"
ANCHORS_FILE: Path = DEFAULT_DIR / "../datasets/anchors.pickle"
PROBES_FILE: Path = DEFAULT_DIR / "../datasets/probes.pickle"

# constant
MAX_NUMBER_OF_VPS = 1_00
NB_MAX_CONCURRENT_MEASUREMENTS = 20
NB_PACKETS = 3
NB_TARGETS_PER_PREFIX = 3

# RIPE atlas credentials
RIPE_CREDENTIALS = {
    "username": "timur.friedman@sorbonne-universite.fr",
    "key": "b3d3d4fc-724e-4505-befe-1ad16a70dc87",
}
