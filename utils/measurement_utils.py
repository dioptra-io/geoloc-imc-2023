import pickle
import requests
import json
import logging

from pathlib import Path
from ipaddress import IPv4Network
from random import randint

from default import (
    ANCHORS_FILE,
    PROBES_FILE,
    PROBES_AND_ANCHORS_FILE,
    HITLIST_FILE,
    MEASUREMENT_CONFIG_PATH,
)

logger = logging.getLogger()


def save_data(out_file: Path, subset_results: dict) -> None:
    """save measurements data into pickle local file"""
    cached_results = []

    # get cached results
    try:
        with open(out_file, "rb") as f:
            cached_results = pickle.load(f)
            cached_results.append(subset_results)
    except FileNotFoundError:
        cached_results = [subset_results]

    with open(out_file, "wb") as f:
        pickle.dump(cached_results, f)


def load_measurement_results(in_file: Path) -> dict:
    """load local pickle data"""
    with open(in_file, "rb") as f:
        return pickle.load(f)


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


def get_atlas_probes_and_anchors() -> dict:
    """return all atlas probes wether or not they are connected"""
    probes = {}
    for _, probe in enumerate(get_from_atlas("https://atlas.ripe.net/api/v2/probes/")):

        # filter probes based on generic criteria
        if probe.get("geometry") is None:
            continue

        probes[probe["address_v4"]] = {
            "is_anchor": probe["is_anchor"],
            "country_code": probe["country_code"],
            "latitude": probe["geometry"]["coordinates"][1],
            "longitude": probe["geometry"]["coordinates"][0],
        }

    # cache probes
    with open(PROBES_AND_ANCHORS_FILE, "wb") as f:
        pickle.dump(probes, f)

    return probes


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
        return pickle.load(f)


def load_atlas_anchors() -> dict:
    """return cached anchors"""
    with open(ANCHORS_FILE, "rb") as f:
        return pickle.load(f)


def load_atlas_probes_and_anchors() -> dict:
    """return cached anchors"""
    with open(PROBES_AND_ANCHORS_FILE, "rb") as f:
        return pickle.load(f)


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