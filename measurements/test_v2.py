import logging
import time
import ujson as json
import traceback

from pprint import pprint
from clickhouse_driver import Client

from default import RIPE_CREDENTIALS
from ripe_atlas_utils.measurements.traceroutes import traceroute_measurement, TracerouteMeasurementOption
from ripe_atlas_utils.fetch.traceroutes import fetch_traceroutes_from_measurement_ids_no_csv
from ripe_atlas_utils.probes.download import dump_ripe_probes, load_probes_from_file
from ripe_atlas_utils.fetch.ripe_public_measurements import fetch_anchors_meshed_public_measurement_ids
from env_project import TMP_GEOLOC_INFO_ONE_TARGET_FILE_PATH, LOCAL_SERVER_GEOLOC_BATCH_RESULTS_FILE_PATH, ALL_PROBES_FILE_PATH, ALL_PROBES_AND_ANCHORS_FILE_PATH, GOOD_ANCHORS_FILE_PATH
from utils.geoloc_earth import get_points_in_poly, plot_circles_and_points, get_center_of_poly
from landmark import get_zipcodes_for_points, get_all_landmarks, filter_websites, get_all_website_ips, get_all_landmarks_and_stats_from_points
from utils.helpers import circle_preprocessing, haversine


def traceroute(target, probe_id):
    description = "Geoloc project"
    tags = ["traceroute", "test", "geoloc"]
    is_public = True
    is_oneoff = True
    probes = {
        "value": str(probe_id),
        "type": "probes",
        "requested": 1
    }
    interval = 60
    is_dry_run = False
    packets = 3
    protocol = "ICMP"
    options = TracerouteMeasurementOption(
        RIPE_KEY, description, tags, is_public, is_oneoff, interval, is_dry_run, packets, protocol)

    response = traceroute_measurement(target, probes, options)
    if "measurements" in response and len(response["measurements"]) == 1:
        return response["measurements"][0]
    else:
        print(f"Failed to traceroute")
        pprint(response)
        return None


def download_mesh_data_from_server():
    # dump_ripe_probes(ALL_ANCHORS_FILE_PATH, ALL_PROBES_FILE_PATH, ALL_PROBES_AND_ANCHORS_FILE_PATH)
    measurement_urls = fetch_anchors_meshed_public_measurement_ids()
    measurement_ids = []
    for m in measurement_urls:
        id = m.split("/")[-2]
        measurement_ids.append(id)
    start = "2023-04-24T12:00:00Z"
    stop = "2023-04-24T13:00:00Z"
    for id in measurement_ids:
        try:
            ids = [id]
            traceroute_data = fetch_traceroutes_from_measurement_ids_no_csv(
                ids, start, stop)
            insert_lst = []
            for t in traceroute_data:
                ts = t.split(",")
                insert_lst.append((ts[0], ts[1], ts[2], ts[3], int(ts[4]), int(
                    ts[5]), float(ts[6]), int(ts[7]), int(ts[8]), int(ts[9]), int(ts[10])))
            client = Client('127.0.0.1')
            client.execute(
                f'insert into bgp_interdomain_te.street_lvl_traceroutes (src_addr, dst_prefix, dst_addr, resp_addr, proto, hop, rtt, ttl, prb_id, msm_id, tstamp) values', insert_lst)
            print(f"{id} => {len(insert_lst)}")
        except:
            print(f"Failed for id {id}")


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

    probes_data = load_probes_from_file(GOOD_ANCHORS_FILE_PATH)
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


def get_probes_to_use_for_circles(circles):
    probes_data = load_probes_from_file(GOOD_ANCHORS_FILE_PATH)
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


def get_landmarks_full(target_ip, rot, rad, tmp_save=False):
    circles = get_circles_to_target(target_ip)
    print(f"{len(circles)} initial vp")
    circles = circle_preprocessing(circles, speed_threshold=4/9)
    print(f"{len(circles)} used vp")
    points = get_points_in_poly(circles, rot, rad)
    print(f"{len(points)} points to look for zipcode")
    area_lst = get_zipcodes_for_points(points, tmp_save)
    print(f"{len(area_lst)} zipcode to look for landmarks")
    landmarks = get_all_landmarks(area_lst, tmp_save)
    print(f"{len(landmarks)} landmarks with websites")
    landmarks = filter_websites(landmarks)
    print(f"{len(landmarks)} unique websites")
    final_landmarks = get_all_website_ips(landmarks, tmp_save)
    print(f"{len(final_landmarks)} local landmarks")
    return final_landmarks


def get_probes(target_ip, speed_threshold=4/9):
    circles = get_circles_to_target(target_ip)
    circles = circle_preprocessing(circles, speed_threshold)
    return get_probes_to_use_for_circles(circles)


def start_tracerouts_to_landmarks(landmarks, probes):
    results_to_get = []
    for landmark in landmarks:
        landmark_ip = landmark[0]
        for probe in probes:
            probe_ip = probe['address_v4']
            probe_id = str(probe['id'])
            res = traceroute(landmark_ip, probe_id)
            if res != None:
                results_to_get.append((res, probe_ip, landmark_ip))
    return results_to_get


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


def tier_1(target_ip, res):
    st = time.time()
    all_circles = get_circles_to_target(target_ip)
    speed_threshold = 4/9
    imp_circles = local_circle_preprocessing(
        all_circles, speed_threshold=speed_threshold)
    lat, lon = get_center_of_poly(imp_circles, speed_threshold)
    if lat == None or lon == None:
        speed_threshold = 2/3
        imp_circles = local_circle_preprocessing(
            all_circles, speed_threshold=speed_threshold)
        lat, lon = get_center_of_poly(imp_circles, speed_threshold)
    res['speed_threshold'] = speed_threshold
    res['tier1:lat'] = lat
    res['tier1:lon'] = lon
    res['vps'] = imp_circles
    et = time.time()
    res['tier1:duration'] = et-st
    res['target_ip'] = target_ip
    return res


def tier_2(target_ip, res):
    st = time.time()
    tier2_points = get_points_in_poly(
        res['vps'], 36, 5, res['speed_threshold'])
    res['tier2:all_points_count'] = len(tier2_points)
    tier2_points = tier2_points[:40*5*10+1]
    res['tier2:inspected_points_count'] = len(tier2_points)
    if len(tier2_points) == 0:
        res['tier2:lat'] = None
        res['tier2:lon'] = None
        et = time.time()
        res['tier2:duration'] = et-st
        return res

    failed_dns_count, failed_asn_count, cdn_count, failed_header_test_count, landmarks = get_all_landmarks_and_stats_from_points(
        tier2_points)
    res['tier2:failed_dns_count'] = failed_dns_count
    res['tier2:failed_asn_count'] = failed_asn_count
    res['tier2:cdn_count'] = cdn_count
    res['tier2:non_cdn_count'] = len(landmarks) + failed_header_test_count
    res['tier2:landmark_count'] = len(landmarks)
    res['tier2:failed_header_test_count'] = failed_header_test_count
    res['tier2:landmarks'] = landmarks

    if len(res['tier2:landmarks']) == 0:
        res['tier2:lat'] = None
        res['tier2:lon'] = None
        et = time.time()
        res['tier2:duration'] = et-st
        return res

    res['tier2:traceroutes'] = start_and_get_traceroutes(
        target_ip, res['vps'], res['tier2:landmarks'])
    all_circles = []
    best_rtt = 5000
    res_lat = None
    res_lon = None
    for probe_ip, target_ip, landmark_ip, r1ip, rtt, lat, lon, traceroute_id in res['tier2:traceroutes']:
        if rtt < 0:
            continue
        all_circles.append((lat, lon, rtt, None, None))
        if rtt < best_rtt:
            best_rtt = rtt
            res_lat = lat
            res_lon = lon

    if len(all_circles) == 0:
        res['tier2:lat'] = None
        res['tier2:lon'] = None
        et = time.time()
        res['tier2:duration'] = et-st
        return res

    res['tier2:lat'] = res_lat
    res['tier2:lon'] = res_lon
    res['tier2:final_circles'] = all_circles
    et = time.time()
    res['tier2:duration'] = et-st
    return res


def tier_3(target_ip, res):
    st = time.time()
    if 'tier2:final_circles' not in res:
        res['tier3:lat'] = None
        res['tier3:lon'] = None
        et = time.time()
        res['tier3:duration'] = et-st
        return res

    else:
        all_circles = res['tier2:final_circles']

    imp_circles = local_circle_preprocessing(
        all_circles, speed_threshold=res['speed_threshold'])
    tier3_points = get_points_in_poly(
        imp_circles, 10, 1, res['speed_threshold'], res['vps'])
    res['tier3:all_points_count'] = len(tier3_points)
    tier3_points = tier3_points[:40*1*36+1]
    res['tier3:inspected_points_count'] = len(tier3_points)
    if len(tier3_points) == 0:
        res['tier3:lat'] = None
        res['tier3:lon'] = None
        et = time.time()
        res['tier3:duration'] = et-st
        return res

    failed_dns_count, failed_asn_count, cdn_count, failed_header_test_count, tmp_landmarks = get_all_landmarks_and_stats_from_points(
        tier3_points)
    landmarks = []
    for landmark in tmp_landmarks:
        ip = landmark[0]
        found = False
        for t2_lm in res['tier2:landmarks']:
            if t2_lm[0] == ip:
                found = True
                break
        if not found:
            landmarks.append(landmark)

    res['tier3:failed_dns_count'] = failed_dns_count
    res['tier3:failed_asn_count'] = failed_asn_count
    res['tier3:cdn_count'] = cdn_count
    res['tier3:non_cdn_count'] = len(landmarks) + failed_header_test_count
    res['tier3:landmark_count'] = len(landmarks)
    res['tier3:failed_header_test_count'] = failed_header_test_count
    res['tier3:landmarks'] = landmarks

    if len(res['tier3:landmarks']) == 0:
        res['tier3:lat'] = None
        res['tier3:lon'] = None
        et = time.time()
        res['tier3:duration'] = et-st
        return res

    res['tier3:traceroutes'] = start_and_get_traceroutes(
        target_ip, res['vps'], res['tier3:landmarks'])

    best_lon = None
    best_lat = None
    best_rtt = 5000
    for probe_ip, target_ip, landmark_ip, r1ip, rtt, lat, lon, traceroute_id in res['tier2:traceroutes']:
        if rtt < 0:
            continue
        if rtt < best_rtt:
            best_rtt = rtt
            best_lon = lon
            best_lat = lat
    for probe_ip, target_ip, landmark_ip, r1ip, rtt, lat, lon, traceroute_id in res['tier3:traceroutes']:
        if rtt < 0:
            continue
        if rtt < best_rtt:
            best_rtt = rtt
            best_lon = lon
            best_lat = lat

    res['tier3:lat'] = best_lat
    res['tier3:lon'] = best_lon
    et = time.time()
    res['tier3:duration'] = et-st
    return res


def get_all_info_geoloc(target_ip):
    logging.info(f"tier1 for {target_ip}")
    res = {'target_ip': target_ip, 'tier1:done': False, 'tier2:done': False,
           'tier3:done': False, 'negative_rtt_included': True}
    res = tier_1(target_ip, res)

    res['lat'] = res['tier1:lat']
    res['lon'] = res['tier1:lon']
    if res['tier1:lat'] == None or res['tier1:lon'] == None:
        return res
    res['tier1:done'] = True
    with open(TMP_GEOLOC_INFO_ONE_TARGET_FILE_PATH, 'w') as outfile:
        json.dump(serialize(res), outfile)

    logging.info(f"tier2 for {target_ip}")
    res = tier_2(target_ip, res)

    if res['tier2:lat'] == None or res['tier2:lon'] == None:
        return res
    else:
        res['tier2:done'] = True
        res['lat'] = res['tier2:lat']
        res['lon'] = res['tier2:lon']
    with open(TMP_GEOLOC_INFO_ONE_TARGET_FILE_PATH, 'w') as outfile:
        json.dump(serialize(res), outfile)

    logging.info(f"tier3 for {target_ip}")
    res = tier_3(target_ip, res)

    if res['tier3:lat'] != None and res['tier3:lon'] != None:
        res['tier3:done'] = True
        res['lat'] = res['tier3:lat']
        res['lon'] = res['tier3:lon']
    with open(TMP_GEOLOC_INFO_ONE_TARGET_FILE_PATH, 'w') as outfile:
        json.dump(serialize(res), outfile)

    return res


def get_geoloc(target_ip):
    circles = tier_2(target_ip)
    res = tier_3(target_ip)
    best_rtt = 5000
    lat = 0
    lon = 0
    for r in res:
        if r[2] < best_rtt:
            best_rtt = r[2]
            lat = r[0]
            lon = r[1]
    return lat, lon


def get_multi_pos():
    target_ips = [("145.220.0.55", 4.8985, 52.3675), ("193.171.255.2", 16.3695, 48.2085), ("192.65.184.54",
                                                                                           6.0495, 46.2285), ("185.42.136.158", 18.0595, 59.3315), ("197.80.104.36",  28.0095, -26.1415)]
    res = []
    for info in target_ips:
        target_ip, lon1, lat1 = info
        lat, lon = get_geoloc(target_ip)
        print(f"{target_ip} is in ({lat}, {lon})")
        print(f"{lat1} {lon1}")
        res.append((target_ip, lat, lon, lat1, lon1))
    for r in res:
        print(
            f"{r[0]} is said to be in ({r[1]}, {r[2]}), correct pos is ({r[3]}, {r[4]})")


def plot_tier1_res(target_ip, speed_threshold):
    circles = get_circles_to_target(target_ip)
    circles = circle_preprocessing(circles, speed_threshold)
    points = get_points_in_poly(circles, 36, 5, speed_threshold)
    plot_circles_and_points(circles, points)


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


def local_circle_preprocessing(circles, speed_threshold=None):
    res_circles = []
    min_rtt = 5000
    for circle in circles:
        min_rtt = min(min_rtt, circle[2])

    for circle in circles:
        if circle[2] < min_rtt * 5:
            res_circles.append(circle)

    return circle_preprocessing(res_circles, speed_threshold)


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


def multi_run(filename):
    with open(filename, 'r') as json_file:
        anchors = json.load(json_file)
    with open(LOCAL_SERVER_GEOLOC_BATCH_RESULTS_FILE_PATH, 'r') as json_file:
        all_res = json.load(json_file)
    i = 0
    for target in anchors:
        try:
            target_ip = target['address_v4']
            if target_ip in all_res:
                continue
            print(f"{i}:{target_ip}")
            i += 1
            lat = target['geometry']['coordinates'][1]
            lon = target['geometry']['coordinates'][0]
            res = {}
            res = get_all_info_geoloc(target_ip)
            res = serialize(res)
            res['lat_c'] = lat
            res['lon_c'] = lon

            if res['lat'] != None and res['lon'] != None:
                res['error'] = haversine(
                    (res['lat'], res['lon']), (res['lat_c'], res['lon_c']))
            if 'tier1:lat' in res and 'tier1:lon' in res and res['tier1:lat'] != None and res['tier1:lon'] != None:
                res['tier1:error'] = haversine(
                    (res['tier1:lat'], res['tier1:lon']), (res['lat_c'], res['lon_c']))
            if 'tier2:lat' in res and 'tier2:lon' in res and res['tier2:lat'] != None and res['tier2:lon'] != None:
                res['tier2:error'] = haversine(
                    (res['tier2:lat'], res['tier2:lon']), (res['lat_c'], res['lon_c']))
            if 'tier3:lat' in res and 'tier3:lon' in res and res['tier3:lat'] != None and res['tier3:lon'] != None:
                res['tier3:error'] = haversine(
                    (res['tier3:lat'], res['tier3:lon']), (res['lat_c'], res['lon_c']))

            all_res[target_ip] = res
            with open(LOCAL_SERVER_GEOLOC_BATCH_RESULTS_FILE_PATH, 'w') as outfile:
                json.dump(all_res, outfile)
        except Exception:
            traceback.print_exc()
            print(f"{target_ip} problem")
            pprint(res)


if __name__ == '__main__':
    logging.basicConfig(filename='log.out',
                        format='%(asctime)s - %(message)s', level=logging.INFO)
    # download_mesh_data_from_server()
    multi_run(GOOD_ANCHORS_FILE_PATH)

"""
create table bgp_interdomain_te.street_lvl_traceroutes
(
    src_addr String,
    dst_prefix String,
    dst_addr String,
    resp_addr String,
    proto Int16,
    hop Int16,
    rtt Float64,
    ttl Int16,
    prb_id Int64,
    msm_id Int64,
    tstamp Datetime('UTC')
)
ENGINE = MergeTree()
order by (dst_addr, src_addr, tstamp);

145.220.0.55 is said to be in (0, 0), correct pos is (4.8985, 52.3675)
193.171.255.2 is said to be in (0, 0), correct pos is (16.3695, 48.2085)
192.65.184.54 is said to be in (46.5076965, 6.6272016), correct pos is (6.0495, 46.2285)
185.42.136.158 is said to be in (0, 0), correct pos is (18.0595, 59.3315)
197.80.104.36 is said to be in (0, 0), correct pos is (28.0095, -26.1415)

"""
