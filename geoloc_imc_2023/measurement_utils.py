import pickle
import requests
import json

from pathlib import Path

from geoloc_imc_2023.helpers import distance
from geoloc_imc_2023.default import (
    ANCHORS_PATH,
    PROBES_PATH,
)


def get_from_atlas(url):
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
    with open(PROBES_PATH, "wb") as f:
        pickle.dump(probes, f)

    return probes, rejected, geoloc_disputed


def get_atlas_anchors() -> dict:
    """return all atlas anchors"""
    anchors = {}
    rejected = 0
    geoloc_disputed = 0
    for _, anchor in enumerate(get_from_atlas("https://atlas.ripe.net/api/v2/probes/")):
        # filter probes based on generic criteria
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

        if anchor["is_anchor"]:
            anchors[anchor["address_v4"]] = {
                "id": anchor["id"],
                "is_anchor": anchor["is_anchor"],
                "country_code": anchor["country_code"],
                "latitude": anchor["geometry"]["coordinates"][1],
                "longitude": anchor["geometry"]["coordinates"][0],
            }

    # cache anchor
    with open(ANCHORS_PATH, "wb") as f:
        pickle.dump(anchors, f)

    return anchors, rejected, geoloc_disputed


def load_atlas_probes() -> dict:
    """return cached probes"""
    with open(PROBES_PATH, "rb") as f:
        probes = pickle.load(f)

    return probes


def load_atlas_anchors() -> dict:
    """return cached anchors"""
    with open(ANCHORS_PATH, "rb") as f:
        anchors = pickle.load(f)

    return anchors
