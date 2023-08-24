import time

from clickhouse_driver import Client

from scripts.utils.file_utils import load_json
from scripts.ripe_atlas.ping_and_traceroute import TRACEROUTE
from scripts.ripe_atlas.atlas_api import fetch_traceroutes_from_measurement_ids_no_csv
from default import ANCHORS_FILE, RIPE_CREDENTIALS


def get_probes_to_use_for_circles(circles):
    probes_data = load_json(ANCHORS_FILE)
    lats_lons = {}
    for circle in circles:
        lats_lons[(circle[0], circle[1])] = circle
    res = []
    for probe in probes_data:
        if 'geometry' not in probe or 'type' not in probe['geometry'] or probe['geometry']['type'] != 'Point' or 'coordinates' not in probe['geometry']:
            continue
        lon, lat = probe['geometry']['coordinates']
        if (lat, lon) in lats_lons:
            res.append(probe)
    return res


def get_circles_to_target(target_ip):
    client = Client('127.0.0.1')
    res = client.execute(
        f'select src_addr, rtt, tstamp from bgp_interdomain_te.street_lvl_traceroutes where resp_addr = \'{target_ip}\' and dst_addr = \'{target_ip}\'')
    dict_rtt = {}
    for hop in res:
        if hop[0] not in dict_rtt:
            dict_rtt[hop[0]] = (hop[1], hop[2])
        if hop[2] > dict_rtt[hop[0]][1]:
            dict_rtt[hop[0]] = (hop[1], hop[2])
        if hop[2] == dict_rtt[hop[0]][1] and hop[1] < dict_rtt[hop[0]][0]:
            dict_rtt[hop[0]] = (hop[1], hop[2])

    probes_data = load_json(ANCHORS_FILE)
    dict_probe_info = {}
    for probe in probes_data:
        if probe['address_v4'] == target_ip:
            continue
        if 'address_v4' not in probe or probe['address_v4'] not in dict_rtt:
            continue
        if 'geometry' not in probe or 'type' not in probe['geometry'] or probe['geometry']['type'] != 'Point' or 'coordinates' not in probe['geometry']:
            continue
        lon, lat = probe['geometry']['coordinates']
        dict_probe_info[probe['address_v4']] = (
            lat, lon, dict_rtt[probe['address_v4']][0], None, None)

    res = []

    for k, v in dict_probe_info.items():
        res.append(v)
    return res


def start_tracerouts_to_landmarks(landmarks, probes):
    results_to_get = []
    for landmark in landmarks:
        landmark_ip = landmark[0]
        for probe in probes:
            probe_ip = probe['address_v4']
            probe_id = str(probe['id'])
            trace = TRACEROUTE(RIPE_CREDENTIALS)
            res = trace.traceroute(landmark_ip, probe_id)
            if res != None:
                results_to_get.append((res, probe_ip, landmark_ip))
    return results_to_get


def get_rtt_diff(probe_ip, target_ip, landmark_ip):
    client = Client('127.0.0.1')
    rtt_dict_target = {}
    rtt_dict_landmark = {}
    res = client.execute(
        f'select resp_addr, dst_addr, rtt from bgp_interdomain_te.street_lvl_traceroutes where src_addr = \'{probe_ip}\' and (dst_addr =  \'{target_ip}\' or dst_addr = \'{landmark_ip}\')')
    for l in res:
        resp_ip = l[0]
        dst_ip = l[1]
        rtt = l[2]
        if dst_ip == target_ip:
            if resp_ip not in rtt_dict_target:
                rtt_dict_target[resp_ip] = rtt
            if rtt < rtt_dict_target[resp_ip]:
                rtt_dict_target[resp_ip] = rtt
        elif dst_ip == landmark_ip:
            if resp_ip not in rtt_dict_landmark:
                rtt_dict_landmark[resp_ip] = rtt
            if rtt < rtt_dict_landmark[resp_ip]:
                rtt_dict_landmark[resp_ip] = rtt
    if target_ip not in rtt_dict_target or landmark_ip not in rtt_dict_landmark:
        return -1, None
    target_rtt = rtt_dict_target[target_ip]
    landmark_rtt = rtt_dict_landmark[landmark_ip]
    same_dict = {}
    for ip in rtt_dict_target:
        if ip in rtt_dict_landmark:
            same_dict[ip] = min(rtt_dict_landmark[ip], rtt_dict_target[ip])
    best_rtt = 0
    best_ip = None
    for k, v in same_dict.items():
        if v > best_rtt:
            best_rtt = v
            best_ip = k
    return target_rtt + landmark_rtt - best_rtt - best_rtt, best_ip


def get_rtt_diff_id(probe_ip, target_ip, landmark_ip):
    print(probe_ip)
    print(target_ip)
    print(landmark_ip)
    client = Client('127.0.0.1')
    rtt_dict_target = {}
    rtt_dict_landmark = {}
    res = client.execute(
        f'select resp_addr, dst_addr, rtt, msm_id from bgp_interdomain_te.street_lvl_traceroutes where src_addr = \'{probe_ip}\' and (dst_addr =  \'{target_ip}\' or dst_addr = \'{landmark_ip}\')')
    traceroute_id = None
    for l in res:
        if l[1] == landmark_ip:
            traceroute_id = l[3]
    if traceroute_id == None:
        return -1, None, None

    for l in res:
        resp_ip = l[0]
        dst_ip = l[1]
        rtt = l[2]
        if dst_ip == target_ip:
            if resp_ip not in rtt_dict_target:
                rtt_dict_target[resp_ip] = rtt
            if rtt < rtt_dict_target[resp_ip]:
                rtt_dict_target[resp_ip] = rtt
        elif dst_ip == landmark_ip:
            if resp_ip not in rtt_dict_landmark:
                rtt_dict_landmark[resp_ip] = rtt
            if rtt < rtt_dict_landmark[resp_ip]:
                rtt_dict_landmark[resp_ip] = rtt
    if target_ip not in rtt_dict_target or landmark_ip not in rtt_dict_landmark:
        return -1, None, traceroute_id
    target_rtt = rtt_dict_target[target_ip]
    landmark_rtt = rtt_dict_landmark[landmark_ip]
    same_dict = {}
    for ip in rtt_dict_target:
        if ip in rtt_dict_landmark:
            same_dict[ip] = min(rtt_dict_landmark[ip], rtt_dict_target[ip])
    best_rtt = 0
    best_ip = None
    for k, v in same_dict.items():
        if v > best_rtt:
            best_rtt = v
            best_ip = k
    return target_rtt + landmark_rtt - best_rtt - best_rtt, best_ip, traceroute_id


def get_traceroutes_results(traceroute_ids):
    next_to_do = []
    for id in traceroute_ids:
        next_to_do.append(id)
    nb_tries = 20
    while nb_tries > 0 and len(next_to_do) > 0:
        nb_tries -= 1
        to_do = []
        for id in next_to_do:
            to_do.append(id)

        next_to_do = []

        for id in to_do:
            try:
                ids = [id]
                traceroute_data = fetch_traceroutes_from_measurement_ids_no_csv(
                    ids)
                if len(traceroute_data) == 0:
                    next_to_do.append(id)
                else:
                    insert_lst = []
                    for t in traceroute_data:
                        ts = t.split(",")
                        insert_lst.append((ts[0], ts[1], ts[2], ts[3], int(ts[4]), int(
                            ts[5]), float(ts[6]), int(ts[7]), int(ts[8]), int(ts[9]), int(ts[10])))
                    client = Client('127.0.0.1')
                    client.execute(
                        f'insert into bgp_interdomain_te.street_lvl_traceroutes (src_addr, dst_prefix, dst_addr, resp_addr, proto, hop, rtt, ttl, prb_id, msm_id, tstamp) values', insert_lst)
            except Exception:
                # print(traceback.format_exc())
                # print(f"Failed for id {id}")
                next_to_do.append(id)
        if len(next_to_do) > 0:
            time.sleep(15)


def start_and_get_traceroutes(target_ip, vps, landmarks):
    probes = get_probes_to_use_for_circles(vps)
    tmp_res_traceroutes = start_tracerouts_to_landmarks(landmarks, probes)
    print(f"{len(tmp_res_traceroutes)} traceroute done")

    traceroute_ids = []
    for elem in tmp_res_traceroutes:
        traceroute_ids.append(elem[0])
    get_traceroutes_results(traceroute_ids)

    res = []
    for t in tmp_res_traceroutes:
        traceroute_id = t[0]
        probe_ip = t[1]
        landmark_ip = t[2]
        rtt, r1ip = get_rtt_diff(probe_ip, target_ip, landmark_ip)
        for landmark in landmarks:
            if landmark[0] == landmark_ip:
                res.append((probe_ip, target_ip, landmark_ip, r1ip,
                           rtt, landmark[2], landmark[3], traceroute_id))
                break
    return res


def serialize(res1):
    res = {}
    for k, v in res1.items():
        res[k] = v
    if 'vps' in res:
        tmp_lst = []
        for x in res['vps']:
            tmp_lst.append(list(x))
        res['vps'] = tmp_lst
    if 'tier2:landmarks' in res:
        tmp_lst = []
        for x in res['tier2:landmarks']:
            tmp_lst.append(list(x))
        res['tier2:landmarks'] = tmp_lst
    if 'tier2:traceroutes' in res:
        tmp_lst = []
        for x in res['tier2:traceroutes']:
            tmp_lst.append(list(x))
        res['tier2:traceroutes'] = tmp_lst
    if 'tier3:landmarks' in res:
        tmp_lst = []
        for x in res['tier3:landmarks']:
            tmp_lst.append(list(x))
        res['tier3:landmarks'] = tmp_lst
    if 'tier3:traceroutes' in res:
        tmp_lst = []
        for x in res['tier3:traceroutes']:
            tmp_lst.append(list(x))
        res['tier3:traceroutes'] = tmp_lst
    return res
