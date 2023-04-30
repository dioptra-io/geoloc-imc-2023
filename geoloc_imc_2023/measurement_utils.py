import pickle
import requests
import json
import logging
import time

from ipaddress import IPv4Network
from random import randint
from copy import copy

from geoloc_imc_2023.atlas_probing import RIPEAtlas
from geoloc_imc_2023.query_api import get_measurement_from_id
from geoloc_imc_2023.default import (
    ANCHORS_FILE,
    PROBES_FILE,
    HITLIST_FILE,
    MEASUREMENT_CONFIG_PATH,
    NB_PACKETS,
    MAX_NUMBER_OF_VPS,
    NB_TARGETS_PER_PREFIX,
    NB_MAX_CONCURRENT_MEASUREMENTS,
)

logger = logging.getLogger()


def get_from_atlas(url):
    """get request url atlas endpoint"""
    response = requests.get(url).json()
    while True:
        for anchor in response["results"]:
            yield anchor

        if response["next"]:
            response = requests.get(response["next"]).json()
        else:
            break


def is_geoloc_disputed(probe: dict) -> dict:
    """check if geoloc disputed flag is contained in probe metadata"""

    tags = probe["tags"]
    for tag in tags:
        if tag["slug"] == "system-geoloc-disputed":
            return True

    return False


def get_atlas_probes() -> dict:
    """return all connected atlas probes"""
    probes = {}
    rejected = 0
    geoloc_disputed = 0
    for _, probe in enumerate(get_from_atlas("https://atlas.ripe.net/api/v2/probes/")):
        # filter probes based on generic criteria
        if not probe["is_anchor"]:
            if (
                probe["status"]["name"] != "Connected"
                or probe.get("geometry") is None
                or probe.get("address_v4") is None
                or probe.get("country_code") is None
                or probe.get("geometry") is None
            ):
                rejected += 1
                continue

            if is_geoloc_disputed(probe):
                geoloc_disputed += 1
                continue

            probes[probe["address_v4"]] = {
                "id": probe["id"],
                "ip": probe["address_v4"],
                "is_anchor": probe["is_anchor"],
                "country_code": probe["country_code"],
                "latitude": probe["geometry"]["coordinates"][1],
                "longitude": probe["geometry"]["coordinates"][0],
            }

    # cache probes
    with open(PROBES_FILE, "wb") as f:
        pickle.dump(probes, f)

    return probes, rejected, geoloc_disputed


def get_atlas_anchors() -> dict:
    """return all atlas anchors"""
    anchors = {}
    rejected = 0
    geoloc_disputed = 0
    for _, anchor in enumerate(get_from_atlas("https://atlas.ripe.net/api/v2/probes/")):
        # filter anchors based on generic criteria
        if anchor["is_anchor"]:
            if (
                anchor["status"]["name"] != "Connected"
                or anchor.get("geometry") is None
                or anchor.get("address_v4") is None
                or anchor.get("country_code") is None
                or anchor.get("geometry") is None
            ):
                rejected += 1
                continue

            if is_geoloc_disputed(anchor):
                geoloc_disputed += 1
                continue

            anchors[anchor["address_v4"]] = {
                "id": anchor["id"],
                "is_anchor": anchor["is_anchor"],
                "country_code": anchor["country_code"],
                "latitude": anchor["geometry"]["coordinates"][1],
                "longitude": anchor["geometry"]["coordinates"][0],
            }

    # cache anchor
    with open(ANCHORS_FILE, "wb") as f:
        pickle.dump(anchors, f)

    return anchors, rejected, geoloc_disputed


def load_atlas_probes() -> dict:
    """return cached probes"""
    with open(PROBES_FILE, "rb") as f:
        probes = pickle.load(f)

    return probes


def load_atlas_anchors() -> dict:
    """return cached anchors"""
    with open(ANCHORS_FILE, "rb") as f:
        anchors = pickle.load(f)

    return anchors


def load_prefix_hitlist() -> dict:
    """return target list dataset for all prefixes in /24"""
    with open(HITLIST_FILE, "rb") as f:
        targets_per_prefix = pickle.load(f)

    return targets_per_prefix


def save_config_file(measurement_config: dict) -> None:
    """save measurement config file"""
    file_path = MEASUREMENT_CONFIG_PATH / f"{measurement_config['UUID']}.json"
    with open(file_path, "w") as f:
        json.dump(measurement_config, f, indent=4)


def get_target_hitlist(
    target_prefix: str, nb_targets: int, targets_per_prefix: dict
) -> list:
    """from ip, return a list of target ips"""
    target_addr_list = []
    try:
        target_addr_list = targets_per_prefix[target_prefix]
    except KeyError:
        pass

    target_addr_list = list(set(target_addr_list))

    if len(target_addr_list) < nb_targets:
        prefix = IPv4Network(target_prefix + "/24")
        target_addr_list.extend(
            [
                str(prefix[randint(1, 254)])
                for _ in range(0, nb_targets - len(target_addr_list))
            ]
        )

    if len(target_addr_list) > nb_targets:
        target_addr_list = target_addr_list[:nb_targets]

    return target_addr_list
