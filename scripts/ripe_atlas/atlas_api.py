# All functions to query RIPE Atlas API

import json
import time
import requests
import ipaddress

from collections import defaultdict, OrderedDict
from ipaddress import IPv4Network
from random import randint

from logger import logger


class RIPEAtlas(object):
    def __init__(
        self,
        account: str,
        key: str,
    ) -> None:
        self.account = account
        self.key = key

    def ping(
        self, target, vps, tag: str, nb_packets: int = 3, max_retry: int = 60
    ) -> None:
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
                logger.info(response)
                logger.warning("Too much measurements.", "Waiting.")
                time.sleep(60)
        else:
            raise Exception("Too much measurements. Stopping.")

        if not response:
            return

        try:
            return measurement_id
        except (IndexError, KeyError):
            return

    def traceroute_measurement(self, target, probes_selector, options):
        ripe_key, description, tags, is_public, packets, protocol = options

        core_parameters = {
            "target": target,
            "af": 4,
            "description": description,
            "resolve_on_probe": False,
            "type": "traceroute",
            "tags": tags,
            "is_public": is_public,
        }

        traceroute_parameters = {
            "packets": packets,
            "protocol": protocol,
        }

        parameters = {}
        parameters.update(core_parameters)
        parameters.update(traceroute_parameters)

        definitions = [parameters]

        response = requests.post(
            f"https://atlas.ripe.net/api/v2/measurements/?key={ripe_key}",
            json={
                "definitions": definitions,
                "probes": [probes_selector],
                "is_oneoff": True,
                "bill_to": self.account,
            },
        ).json()
        return response

    def __str__(self):
        return "RIPE Atlas"


def ripe_traceroute_to_csv(traceroute):
    protocols = {"ICMP": 1, "TCP": 6, "UDP": 17}
    rows = []
    try:
        src_addr = traceroute["from"]
        dst_addr = traceroute["dst_addr"]
        af = traceroute["af"]
        if af == 4:
            dst_prefix = ".".join(dst_addr.split(".")[:3] + ["0"])
        elif af == 6:
            dst_prefix = str(
                ipaddress.ip_network(dst_addr + "/48", strict=False).network_address
            )
    except (KeyError, ValueError):
        return rows

    for hop in traceroute["result"]:
        for response in hop.get("result", []):
            if not response or response.get("error"):
                continue
            if response.get("x") == "*" or not response.get("rtt"):
                response["from"] = "*"
                response["rtt"] = 0
                response["ttl"] = 0
            proto = protocols[traceroute["proto"]]
            try:
                row = (
                    src_addr,
                    dst_prefix,
                    dst_addr,
                    response["from"],
                    proto,
                    hop["hop"],
                    response["rtt"],
                    response["ttl"],
                    traceroute["prb_id"],
                    traceroute["msm_id"],
                    traceroute["timestamp"],
                )
                row_str = "".join(f",{x}" for x in row)[1:]
                rows.append(row_str)
            except Exception:
                print("ERROR", response)

    return rows


def fetch_traceroutes_from_measurement_ids_no_csv(
    measurement_ids, start=None, stop=None
):
    res = []
    for measurement_id in measurement_ids:
        result_url = (
            f"https://atlas.ripe.net/api/v2/measurements/{measurement_id}/results/?"
        )
        if start:
            result_url += f"start={start}"
        if stop:
            result_url += f"&stop={stop}"
        traceroutes = requests.get(result_url).json()
        if "error" in traceroutes:
            print(traceroutes)
            continue
        for traceroute in traceroutes:
            rows = ripe_traceroute_to_csv(traceroute)
            for row in rows:
                res.append(row)
    return res


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


def get_prefix_from_ip(addr):
    """from an ip addr return /24 prefix"""
    prefix = addr.split(".")[:-1]
    prefix.append("0")
    prefix = ".".join(prefix)
    return prefix


def get_target_hitlist(target_prefix, nb_targets, targets_per_prefix):
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
            logger.warning(f"no results: {result}")

    # order vps per increasing rtt
    for dst_addr in measurement_results:
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

    return response


def get_measurements_from_tag(tag: str) -> dict:
    """retrieve all measurements that share the same tag and return parsed measurement results"""

    url = f"https://atlas.ripe.net/api/v2/measurements/tags/{tag}/results/"

    response = get_response(url, max_retry=1, wait_time=1)

    return response


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
                "id": probe["id"],
                "address_v4": probe["address_v4"],
                "asn_v4": probe["asn_v4"],
                "country_code": probe["country_code"],
                "geometry": probe["geometry"],
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
                "id": anchor["id"],
                "address_v4": anchor["address_v4"],
                "asn_v4": anchor["asn_v4"],
                "country_code": anchor["country_code"],
                "geometry": anchor["geometry"],
                "id": anchor["id"],
            }
            anchors.append(reduced_anchor)

    return anchors, rejected, geoloc_disputed
