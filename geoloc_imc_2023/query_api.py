"""all functions to query RIPE Atlas API"""
import requests
import time

from collections import defaultdict


def get_measurement_url(measurement_id: int, key: str):
    """return Atlas API url for get measurement request"""
    return f"https://atlas.ripe.net/api/v2/measurements/{measurement_id}/results/?key={key}"

def get_from_atlas(url: str, max_retry:int = 60):
    """request to Atlas API"""
    for _ in range(max_retry):

        response = requests.get(url, timeout=20).json()
        if response:
            break
        time.sleep(2)

    return response

def retreive_single_measurement(measurement_id: int, anchors: dict, key: str) -> dict:
    """retreive measurement results from RIPE Atlas with measurement id"""
    measurement_results = []
    url = get_measurement_url(measurement_id, key)

    response = get_from_atlas(url)

    # parse response
    for result in response:
        # parse results and calculate geoloc
        if result.get('result') is not None:
            
            dst_addr = result['dst_addr']
            vp_ip = result['from']

            if type(result['result']) == list:
                rtt_list = [list(rtt.values())[0] for rtt in result['result']]
            else:
                rtt_list = [result['result']["rtt"]]

            # remove stars from results
            rtt_list = list(filter(lambda x: x != "*", rtt_list))
            if not rtt_list: 
                continue
            
            # get min rtt
            min_rtt = min(rtt_list)

            # both vp and target coordinates
            vp_lat = anchors[vp_ip]['latitude']
            vp_lon = anchors[vp_ip]['longitude']

            measurement_results.append({
                "node": vp_ip,
                "min_rtt": min_rtt,
                "rtt_list": rtt_list,
                "vp_lat": vp_lat,
                "vp_lon": vp_lon,
            })

        else:
            print(f"no results: {result}")

    measurement_results = sorted(measurement_results, key = lambda x: x["min_rtt"])

    return {
        "target_addr": dst_addr,
        "results": measurement_results,
    }
    