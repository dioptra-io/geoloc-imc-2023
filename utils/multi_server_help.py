import json

from pprint import pprint
from clickhouse_driver import Client


from test_v2 import get_probes_to_use_for_circles, get_traceroutes_results, get_rtt_diff_id
from env_project import FINAL_ANALYSABLE_FILE_PATH, GOOD_ANCHORS_FILE_PATH, SERVER1_ANCHORS_FILE_PATH, SERVER2_ANCHORS_FILE_PATH, LOCAL_SERVER_GEOLOC_BATCH_RESULTS_FILE_PATH, DIST_SERVER_GEOLOC_BATCH_RESULTS_FILE_PATH, MISSING_TRACEROUTES_IDS_FILE_PATH


def split_servers():
    with open(GOOD_ANCHORS_FILE_PATH, 'r') as json_file:
        anchors = json.load(json_file)
    with open(FINAL_ANALYSABLE_FILE_PATH, 'r') as json_file:
        all_res = json.load(json_file)
    next_anc = 0
    anchors1 = []
    anchors2 = []
    for target in anchors:
        try:
            target_ip = target['address_v4']
            if target_ip in all_res:
                continue
            if next_anc == 0:
                anchors1.append(target)
                next_anc = 1
            else:
                anchors2.append(target)
                next_anc = 0
        except:
            pprint(target)
    print(len(anchors1))
    print(len(anchors2))
    with open(SERVER1_ANCHORS_FILE_PATH, 'w') as outfile:
        json.dump(anchors1, outfile)
    with open(SERVER2_ANCHORS_FILE_PATH, 'w') as outfile:
        json.dump(anchors2, outfile)


def combine_results():
    with open(LOCAL_SERVER_GEOLOC_BATCH_RESULTS_FILE_PATH, 'r') as json_file:
        res1 = json.load(json_file)
    with open(DIST_SERVER_GEOLOC_BATCH_RESULTS_FILE_PATH, 'r') as json_file:
        res2 = json.load(json_file)

    print(len(res1))
    print(len(res2))
    with open(FINAL_ANALYSABLE_FILE_PATH, 'r') as json_file:
        all_res = json.load(json_file)
    for k, v in res1.items():
        if 'negative_rtt_included' not in v:
            continue
        all_res[k] = v
    for k, v in res2.items():
        if 'negative_rtt_included' not in v:
            continue
        all_res[k] = v
    print(len(all_res))

    with open(FINAL_ANALYSABLE_FILE_PATH, 'w') as outfile:
        json.dump(all_res, outfile)


def get_db_ids():
    client = Client('127.0.0.1')
    query = 'select distinct msm_id from bgp_interdomain_te.street_lvl_traceroutes where dst_addr not in (select distinct src_addr from bgp_interdomain_te.street_lvl_traceroutes)'
    res = client.execute(query)
    lst = []
    for r in res:
        lst.append(r[0])
    return lst


def fill_db():
    with open(MISSING_TRACEROUTES_IDS_FILE_PATH, 'r') as json_file:
        ids_to_get = json.load(json_file)
    print(len(ids_to_get))
    existing_ids = get_db_ids()
    tmp_existing_ids = {}
    for id in existing_ids:
        tmp_existing_ids[id] = 1
    existing_ids = tmp_existing_ids
    print(len(existing_ids))
    final_ids_to_get = []
    for id in ids_to_get:
        if id not in existing_ids:
            final_ids_to_get.append(id)
    print(len(final_ids_to_get))
    ids = final_ids_to_get
    get_traceroutes_results(ids)


def fill_negative_rtt():
    with open(FINAL_ANALYSABLE_FILE_PATH, 'r') as json_file:
        all_res = json.load(json_file)

    i = 0
    for ip, d in all_res.items():
        if 'negative_rtt_included' in d and d['negative_rtt_included']:
            continue
        i += 1
        probes = get_probes_to_use_for_circles(d['vps'])
        probe_ips = []
        for p in probes:
            probe_ips.append(p['address_v4'])
        if 'tier2:traceroutes' in d and 'tier2:landmarks' in d:
            landmark_ips = []
            landmarks = d['tier2:landmarks']
            for l in landmarks:
                landmark_ips.append(l[0])
            target_ip = d['target_ip']
            traceroutes = []
            for p in probe_ips:
                for l in landmark_ips:
                    rtt, r1ip, traceroute_id = get_rtt_diff_id(p, target_ip, l)
                    for landmark in landmarks:
                        if landmark[0] == l:
                            traceroutes.append(
                                [p, target_ip, l, r1ip, rtt, landmark[2], landmark[3], traceroute_id])
                            break
            all_res[ip]['tier2:traceroutes'] = traceroutes

        if 'tier3:traceroutes' in d and 'tier3:landmarks' in d:
            landmark_ips = []
            landmarks = d['tier3:landmarks']
            for l in landmarks:
                landmark_ips.append(l[0])
            target_ip = d['target_ip']
            traceroutes = []
            for p in probe_ips:
                for l in landmark_ips:
                    rtt, r1ip, traceroute_id = get_rtt_diff_id(p, target_ip, l)
                    for landmark in landmarks:
                        if landmark[0] == l:
                            traceroutes.append(
                                [p, target_ip, l, r1ip, rtt, landmark[2], landmark[3], traceroute_id])
                            break
            all_res[ip]['tier3:traceroutes'] = traceroutes
        all_res[ip]['negative_rtt_included'] = True
    print(f"{i} new target with negative RTT")
    with open(FINAL_ANALYSABLE_FILE_PATH, 'w') as outfile:
        json.dump(all_res, outfile)


def count_todo():
    with open(SERVER1_ANCHORS_FILE_PATH, 'r') as json_file:
        d1 = json.load(json_file)
    with open(SERVER2_ANCHORS_FILE_PATH, 'r') as json_file:
        d2 = json.load(json_file)
    print(len(d1))
    print(len(d2))


if __name__ == '__main__':
    # split_servers()
    combine_results()
    # ids = get_db_ids()
    # with open(MISSING_TRACEROUTES_IDS_FILE_PATH, 'w') as outfile:
    #    json.dump(ids, outfile)
    # fill_db()
    # fill_negative_rtt()
    # count_todo()
4
