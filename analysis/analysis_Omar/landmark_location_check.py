import json


from matplotlib import pyplot as plt

from scipy.stats import pearsonr
import math
from plot_utils.plot import plot_multiple_cdf, plot_scatter, plot_save, plot_scatter_multiple
from clickhouse_driver import Client
from ipaddress import ip_network

import pyasn

from analyse import every_tier_result_and_errors
from utils.helpers import haversine
from env_project import FINAL_ANALYSABLE_FILE_PATH, IP_TO_ASN_FILE_PATH


def get_min_rtt_per_src_dst_query_traceroute_table(database, table, filter=None):
    query = (
        f"WITH groupUniqArray(rtt) as rtts, "
        f" arrayMin(rtts) as min_rtt "
        f"SELECT dst_ip, src_ip, min_rtt "
        f"FROM {database}.{table} "
        f"WHERE reply_ip = dst_ip {filter} "

        f"GROUP BY dst_ip, src_ip "
    )
    print(query)
    return query


def get_min_rtt_per_src_dst_query_ping_table(database, table, filter=None, threshold=10000):
    query = (
        f"WITH  arrayMin(groupArray(`min`)) as min_rtt "
        f"SELECT IPv4NumToString(dst), IPv4NumToString(src), min_rtt "
        f"FROM {database}.{table} "
        f"WHERE `min` > -1 AND `min`< {threshold} AND dst != src {filter} "
        f"GROUP BY dst, src "
    )
    print(query)
    return query


def get_min_rtt_per_src_dst_prefix_query_ping_table(database, table, filter=None, threshold=10000):
    query = (
        f"WITH  arrayMin(groupArray(`min`)) as min_rtt "
        f"SELECT IPv4NumToString(dst_prefix), IPv4NumToString(src), min_rtt "
        f"FROM {database}.{table} "
        f"WHERE `min` > -1 AND `min`< {threshold} "
        f"AND dst_prefix != toIPv4(substring(cutIPv6(IPv4ToIPv6(src), 0, 1), 8)) "
        f"{filter} "
        f"GROUP BY dst_prefix, src "
    )
    print(query)
    return query


def plot_cdf_min_rtt(data):
    query = get_min_rtt_per_src_dst_query_ping_table(
        'geolocation_replication', 'targets_to_landmarks_pings', '', 1000000)
    client = Client('127.0.0.1')
    db_table = client.execute(query)
    rtts = []
    remove_dict = {}
    print(len(db_table))
    for l in db_table:
        rtts.append(l[2])
        remove_dict[(l[0], l[1])] = l[2]
    print(len(rtts))
    plot_multiple_cdf([rtts], 10000, 0, None, 'Min RTT (ms)',
                      'CDF of (landmark, target) pairs', None)
    plot_save("./fig/cdf_close_landmark_check.pdf", is_tight_layout=True)

    plot_multiple_cdf([rtts], 10000, 0.1, None, 'Min RTT (ms)',
                      'CDF of (landmark, target) pairs', None, xscale="log")
    plot_save("./fig/cdf_close_landmark_check_log.pdf", is_tight_layout=True)

    error1 = []
    error2 = []
    error3 = []
    error4 = []
    error1ms = []
    error2ms = []
    error5ms = []
    error10ms = []

    for _, d in data.items():
        errors = every_tier_result_and_errors(d)
        error1.append(errors['error1'])
        error2.append(errors['error2'])
        error3.append(errors['error3'])
        error4.append(errors['error4'])
        err1ms = 50000
        err2ms = 50000
        err5ms = 50000
        err10ms = 50000
        for f in ['tier2:landmarks', 'tier3:landmarks']:
            if f in d:
                for l_ip, _, l_lat, l_lon in d[f]:
                    dist = haversine((l_lat, l_lon), (d['lat_c'], d['lon_c']))
                    key_rtt = (l_ip, d['target_ip'])
                    if dist < err1ms and (key_rtt not in remove_dict or remove_dict[key_rtt] <= 1):
                        err1ms = dist
                    if dist < err2ms and (key_rtt not in remove_dict or remove_dict[key_rtt] <= 2):
                        err2ms = dist
                    if dist < err5ms and (key_rtt not in remove_dict or remove_dict[key_rtt] <= 5):
                        err5ms = dist
                    if dist < err10ms and (key_rtt not in remove_dict or remove_dict[key_rtt] <= 10):
                        err10ms = dist
        if err1ms != 50000:
            error1ms.append(err1ms)
        else:
            error1ms.append(error1[-1])
        if err2ms != 50000:
            error2ms.append(err2ms)
        else:
            error2ms.append(error1[-1])
        if err5ms != 50000:
            error5ms.append(err5ms)
        else:
            error5ms.append(error1[-1])
        if err10ms != 50000:
            error10ms.append(err10ms)
        else:
            error10ms.append(error1[-1])

    plot_multiple_cdf([error3, error4, error1ms, error2ms, error5ms, error10ms], 10000, 0, None, 'Geolocation error (km)', 'CDF of targets', [
                      "Street Level", "Closest landmark unfiltered", "Closest landmark <= 1ms", "Closest landmark <= 2ms", "Closest landmark <= 5ms", "Closest landmark <= 10ms"])
    plt.legend(fontsize="10")
    plot_save("./fig/cdf_check_close_landmarks.pdf", is_tight_layout=True)

    plot_multiple_cdf([error3, error4, error1ms, error2ms, error5ms, error10ms], 10000, 0.1, None, 'Geolocation error (km)', 'CDF of targets', [
                      "Street Level", "Closest landmark unfiltered", "Closest landmark <= 1ms", "Closest landmark <= 2ms", "Closest landmark <= 5ms", "Closest landmark <= 10ms"], xscale="log")
    plt.legend(fontsize="10")
    plot_save("./fig/cdf_check_close_landmarks_log.pdf", is_tight_layout=True)

    for i in [1, 5, 10, 40, 9999999999]:
        c = len([j for j in error1ms if j <= i])
        print(f"{c} targets with landmarks (ping <= {i}) or {c/len(error1ms)}")


if __name__ == "__main__":
    with open(FINAL_ANALYSABLE_FILE_PATH, 'r') as json_file:
        data = json.load(json_file)
    plot_cdf_min_rtt(data)
