"""all functions to query RIPE Atlas API"""
import requests
import time
import json
import logging

from collections import defaultdict, OrderedDict

from geoloc_imc_2023.default import RIPE_CREDENTIALS

logger = logging.getLogger()


def get_measurement_url(measurement_id: int):
    """return Atlas API url for get measurement request"""

    return f"https://atlas.ripe.net/api/v2/measurements/{measurement_id}/results/"


def get_from_atlas(url: str, max_retry: int = 60, wait_time: int = 5):
    """request to Atlas API"""

    for _ in range(max_retry):
        response = requests.get(url, timeout=20).json()
        if response:
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

    response = get_from_atlas(url, max_retry=max_retry, wait_time=wait_time)

    measurement_result = parse_measurements_results(response)

    return measurement_result


def get_measurements_from_tag(tag: str) -> dict:
    """retrieve all measurements that share the same tag and return parsed measurement results"""

    url = f"https://atlas.ripe.net/api/v2/measurements/tags/{tag}/results/"

    response = requests.get(url)

    # small parsing, as response might not be Json formatted
    try:
        response = json.loads(response.content)
    except json.JSONDecodeError:
        response = response.content.decode()
        response = response.replace("}{", "}, {")
        response = response.replace("} {", "}, {")
        response = json.loads(response)

    measurement_results = parse_measurements_results(response)

    return measurement_results
