"""code constants, path, etc..."""
from pathlib import Path


# Path
HITLIST_PATH: Path = Path().absolute() / "../datasets/parsed_hitlist.pickle"
ANCHORS_PATH: Path = Path().absolute() / "../datasets/anchors.pickle"
PROBES_PATH: Path = Path().absolute() / "../datasets/probes.pickle"
RESULTS_PATH: Path = Path().absolute() / "../results/"
MEASURMENT_METATDATA_PATH: Path = Path().absolute() / "../measurements_metadata/"

# constant
MAX_NUMBER_OF_VPS = 1_00
NB_MAX_CONCURRENT_MEASUREMENTS = 5
NB_PACKETS = 3
NB_TARGETS_PER_PREFIX = 3

RIPE_CREDENTIALS = {
    "username": "timur.friedman@sorbonne-universite.fr",
    "key": "b3d3d4fc-724e-4505-befe-1ad16a70dc87",
}
