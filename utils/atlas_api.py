"""all functions to query RIPE Atlas API"""
import json
import logging
import time
import requests

from collections import defaultdict, OrderedDict


class RIPEAtlas(object):
    def __init__(
        self,
        account: str,
        key: str,
    ) -> None:
        self.account = account
        self.key = key

    def ping(self, target, vps, tag: str, nb_packets: int = 3, max_retry: int = 60) -> None:
        """start ping measurement towards target from vps, return Atlas measurement id"""

        for _ in range(max_retry):
            response = requests.post(
                f"https://atlas.ripe.net/api/v2/measurements/?key={self.key}",
                json={
                    "definitions": [
                        {
                            "target": target,
                            "af": 4,
                            "packets": nb_packets,
                            "size": 48,
                            "tags": [tag],
                            "description": f"Dioptra Geolocation of {target}",
                            "resolve_on_probe": False,
                            "skip_dns_check": True,
                            "include_probe_id": False,
                            "type": "ping",
                        }
                    ],
                    "probes": [
                        {"value": vp, "type": "probes", "requested": 1} for vp in vps
                    ],
                    "is_oneoff": True,
                    "bill_to": self.account,
                },
            ).json()

            try:
                measurement_id = response["measurements"][0]
                break
            except KeyError:
                logging.info(response)
                logging.warning("Too much measurements.", "Waiting.")
                time.sleep(60)
        else:
            raise Exception("Too much measurements. Stopping.")

        if not response:
            return

        try:
            return measurement_id
        except (IndexError, KeyError):
            return

    def __str__(self):
        return "RIPE Atlas"


def wait_for(measurement_id: str, max_retry: int = 30) -> None:
    for _ in range(max_retry):
        response = requests.get(
            f"https://atlas.ripe.net/api/v2/measurements/{measurement_id}/"
        ).json()

        # check if measurement is ongoing or not
        if response["status"]["name"] != "Ongoing":
            return response

        time.sleep(10)

    return None


def is_geoloc_disputed(probe: dict) -> bool:
    """check if geoloc disputed flag is contained in probe metadata"""

    tags = probe["tags"]
    for tag in tags:
        if tag["slug"] == "system-geoloc-disputed":
            return True
    return False


def get_measurement_url(measurement_id: int) -> str:
    """return Atlas API url for get measurement request"""

    return f"https://atlas.ripe.net/api/v2/measurements/{measurement_id}/results/"


def get_response(url: str, max_retry: int = 60, wait_time: int = 2) -> list:
    """request to Atlas API"""

    for _ in range(max_retry):
        response = requests.get(url)

        # small parsing, as response might not be Json formatted
        try:
            response = json.loads(response.content)
        except json.JSONDecodeError:
            response = response.content.decode()
            response = response.replace("}{", "}, {")
            response = response.replace("} {", "}, {")
            response = json.loads(response)

        if response != []:
            break
        time.sleep(wait_time)

    return response


def parse_measurements_results(response: list) -> dict:
    """from get Atlas measurement request return parsed results"""

    # parse response
    measurement_results = defaultdict(dict)
    for result in response:
        # parse results and calculate geoloc
        if result.get("result") is not None:
            dst_addr = result["dst_addr"]
            vp_addr = result["from"]

            if type(result["result"]) == list:
                rtt_list = [list(rtt.values())[0] for rtt in result["result"]]
            else:
                rtt_list = [result["result"]["rtt"]]

            # remove stars from results
            rtt_list = list(filter(lambda x: x != "*", rtt_list))
            if not rtt_list:
                continue

            # sometimes connection error with vantage point cause result to be string message
            try:
                min_rtt = min(rtt_list)
            except TypeError:
                continue

            if isinstance(min_rtt, str):
                continue

            measurement_results[dst_addr][vp_addr] = {
                "node": vp_addr,
                "min_rtt": min_rtt,
                "rtt_list": rtt_list,
            }

        else:
            logging.warning(f"no results: {result}")

    measurement_results[dst_addr] = OrderedDict(
        {
            vp: results
            for vp, results in sorted(
                measurement_results[dst_addr].items(),
                key=lambda item: item[1]["min_rtt"],
            )
        }
    )

    return measurement_results


def get_measurement_from_id(
    measurement_id: int,
    max_retry: int = 60,
    wait_time: int = 10,
) -> dict:
    """retrieve measurement results from RIPE Atlas with measurement id"""

    url = get_measurement_url(measurement_id)

    response = get_response(url, max_retry=max_retry, wait_time=wait_time)

    measurement_result = parse_measurements_results(response)

    return measurement_result


def get_measurements_from_tag(tag: str) -> dict:
    """retrieve all measurements that share the same tag and return parsed measurement results"""

    url = f"https://atlas.ripe.net/api/v2/measurements/tags/{tag}/results/"

    response = get_response(url, max_retry=1, wait_time=1)

    measurement_results = parse_measurements_results(response)

    return measurement_results


def get_from_atlas(url: str):
    """get request url atlas endpoint"""
    response = requests.get(url).json()
    while True:
        for anchor in response["results"]:
            yield anchor

        if response["next"]:
            response = requests.get(response["next"]).json()
        else:
            break


def get_atlas_probes() -> list:
    """return all connected atlas probes"""
    probes = []
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
            ):
                rejected += 1
                continue

            if is_geoloc_disputed(probe):
                geoloc_disputed += 1
                continue

            reduced_probe = {
                "address_v4": probe["address_v4"],
                "address_v6": probe["address_v6"],
                "asn_v4": probe["asn_v4"],
                "asn_v6": probe["asn_v6"],
                "country_code": probe["country_code"],
                "description": probe["description"],
                "first_connected": probe["first_connected"],
                "geometry": probe["geometry"]
            }
            probes.append(reduced_probe)

    return probes, rejected, geoloc_disputed


def get_atlas_anchors() -> list:
    """return all atlas anchors"""
    anchors = []
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
            ):
                rejected += 1
                continue

            if is_geoloc_disputed(anchor):
                geoloc_disputed += 1
                continue

            reduced_anchor = {
                "address_v4": anchor["address_v4"],
                "address_v6": anchor["address_v6"],
                "asn_v4": anchor["asn_v4"],
                "asn_v6": anchor["asn_v6"],
                "country_code": anchor["country_code"],
                "description": anchor["description"],
                "first_connected": anchor["first_connected"],
                "geometry": anchor["geometry"]
            }
            anchors.append(reduced_anchor)

    return anchors, rejected, geoloc_disputed
