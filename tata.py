from utils.file_utils import dump_json, load_json
from default import ANCHORS_FILE, POPULATION_CITY_FILE


anchors = load_json(POPULATION_CITY_FILE)

print(len(anchors))
