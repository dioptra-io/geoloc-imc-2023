"""all functions to query RIPE Atlas API"""
import requests
import time


def get_measurement_url(measurement_id: int, key: str):
    """return Atlas API url for get measurement request"""

    return f"https://atlas.ripe.net/api/v2/measurements/{measurement_id}/results/?key={key}"


def get_from_atlas(url: str, max_retry: int = 60):
    """request to Atlas API"""

    for _ in range(max_retry):
        response = requests.get(url, timeout=20).json()
        if response:
            break
        time.sleep(2)

    return response


def parse_measurements_results(response: list) -> dict:
    """from get Atlas measurement request return parsed results"""

    # parse response
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

            # get min rtt
            min_rtt = min(rtt_list)

            measurement_results.append(
                {
                    "node": vp_addr,
                    "min_rtt": min_rtt,
                    "rtt_list": rtt_list,
                }
            )

        else:
            print(f"no results: {result}")

    measurement_results = sorted(measurement_results, key=lambda x: x["min_rtt"])

    return {
        "target_addr": dst_addr,
        "results": measurement_results,
    }


def get_measurement_from_id(measurement_id: int, key: str) -> dict:
    """retreive measurement results from RIPE Atlas with measurement id"""

    url = get_measurement_url(measurement_id, key)

    response = get_from_atlas(url)

    measurement_result = parse_measurements_results(response)

    return measurement_result


def get_measurements_from_tag(tag: str, key: str) -> dict:
    """retreive all measurements that share the same tag and return parsed measurement results"""

    measurement_results = []
    url = f"https://atlas.ripe.net/api/v2/measurements/tags/{tag}/results/?key={key}"

    responses = requests.get(url).json()

    for response in responses:
        measurement_result = parse_measurements_results(response)
        measurement_results.append(measurement_result)

    return measurement_results
