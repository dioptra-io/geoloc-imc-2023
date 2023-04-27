"""run measurements"""
import logging
import pickle
import json

from pathlib import Path
import uuid

from geoloc_imc_2023.cbg import CBG, get_prefix_from_ip
from geoloc_imc_2023.query_api import get_measurements_from_tag

from geoloc_imc_2023.default import (
    PROBES_PATH,
    ANCHORS_PATH,
    HITLIST_PATH,
    RIPE_CREDENTIALS,
)

logging.basicConfig(level=logging.INFO)

NB_TARGET = 2
NB_VP = 5

def get_probes() -> dict:
    """return all probes"""
    # load probes
    with open(PROBES_PATH, "rb") as f:
        probes = pickle.load(f)

    return probes

def get_anchors() -> dict:
    """return all anchors"""
    # load anchors
    with open(ANCHORS_PATH, "rb") as f:
        anchors = pickle.load(f)

def load_dataset():
    # load hitlist
    with open(HITLIST_PATH, "rb") as f:
        targets_per_prefix = pickle.load(f)



    return targets_per_prefix, probes, anchors

def probe_prefixes():

# select targets and vps from anchors
targets= list(anchors.keys())[:NB_TARGET]
vps = {}
for i, probe in enumerate(probes):
    if i >= NB_VP: break
    vps[probe] = probes[probe]

logging.info(f"nb targets: {len(targets)}")
logging.info(f"nb_vps : {len(vps)}")

dry_run = True
measurement_uuid = uuid.uuid4()

# measurement configuration for retrieval
measurement_config = {
    "UUID": str(measurement_uuid),
    "is_dry_run": dry_run,
    "description": "measurement towards all anchors with all probes as vps",
    "type" : "target prefix",
    "af" : 4,
    "targets": targets,
    "vps": vps,
}

# save measurement configuration before starting measurement
measurement_config_path = Path(".") / f"../measurements_metadata/{str(measurement_uuid)}.json"
with open(measurement_config_path, "w") as f:
    json.dump(measurement_config, f, indent=4)

cbg = CBG(RIPE_CREDENTIALS)

# get target prefixes
target_prefixes = []
for target_addr in targets:
    target_prefix = get_prefix_from_ip(target_addr)
    target_prefixes.append(target_prefix)

# measurement for 3 targets in every target prefixes
measurement_config["start_time"], measurement_config["end_time"] = cbg.prefix_probing(
    target_prefixes= target_prefixes, 
    vps= vps,
    targets_per_prefix= targets_per_prefix,
    tag= measurement_uuid,
    dry_run=dry_run
)

# save measurement configuration before starting measurement
measurement_config_path = Path(".") / f"../measurements_metadata/{str(measurement_uuid)}.json"
with open(measurement_config_path, "w") as f:
    json.dump(measurement_config, f, indent=4)

measurement_results = get_measurements_from_tag(measurement_config["UUID"])

# test that everything is alright
logging.info(f"nb measurements retrieved: {len(measurement_results)}")

print(f"measurements for {len(measurement_results)} target addr.")
for i, (target_addr, results) in enumerate(measurement_results.items()):
    if i > 10: break
    print(target_addr, ":", len(results))

# save results
out_file = f"../results/{measurement_config['UUID']}.pickle"
print(out_file)
with open(out_file, "wb") as f:
    pickle.dump(measurement_results,f)