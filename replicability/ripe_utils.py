import os
from ripe_atlas_utils.probes.download import dump_ripe_probes
from utils.utils import load_json
def download_ripe_probes():
    """
        Get geo information about vantage points and targets
        """
    anchors_file = "resources/ripe/anchors.json"
    probe_file = "resources/ripe/probes.json"
    all_probes_file = "resources/ripe/all_probes.json"
    if not os.path.exists(anchors_file):
        dump_ripe_probes(anchors_file, probe_file, all_probes_file, max_page = None)

    anchors = load_json(anchors_file)
    probes = load_json(probe_file)
    all_probes = load_json(all_probes_file)
    return anchors, probes, all_probes