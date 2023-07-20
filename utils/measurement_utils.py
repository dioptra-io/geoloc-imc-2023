import pickle
import requests
import json
import logging

from pathlib import Path

from default import (
    ANCHORS_FILE,
    PROBES_FILE,
    PROBES_AND_ANCHORS_FILE,
    MEASUREMENT_CONFIG_PATH,
)

logger = logging.getLogger()


def load_pickle(file: Path) -> dict:
    with open(file, "rb") as f:
        return pickle.load(f)


def save_pickle(out_file: Path, subset_results: dict) -> None:
    """save measurements data into pickle local file"""

    # get cached results
    try:
        with open(out_file, "rb") as f:
            cached_results = pickle.load(f)
            cached_results.update(subset_results)
    except FileNotFoundError:
        cached_results = subset_results

    with open(out_file, "wb") as f:
        pickle.dump(cached_results, f)


def save_config_file(measurement_config: dict) -> None:
    """save measurement config file"""
    file_path = MEASUREMENT_CONFIG_PATH / f"{measurement_config['UUID']}.json"
    with open(file_path, "w") as f:
        json.dump(measurement_config, f, indent=4)


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


def get_prefix_from_ip(addr: str):
    """from an ip addr return /24 prefix"""
    prefix = addr.split(".")[:-1]
    prefix.append("0")
    prefix = ".".join(prefix)

    return prefix


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
    save_pickle(PROBES_FILE, probes)

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
    save_pickle(ANCHORS_FILE, anchors)

    return anchors, rejected, geoloc_disputed


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
    save_pickle(PROBES_AND_ANCHORS_FILE, probes)

    return probes
