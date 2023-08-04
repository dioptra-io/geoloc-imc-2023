from geoloc_earth import get_points_in_poly
from pprint import pprint
from env_project import FINAL_ANALYSABLE_FILE_PATH, ALL_ANCHORS_FILE_PATH, GOOD_ANCHORS_FILE_PATH, BAD_ANCHORS_FILE_PATH, MISLOCATED_PROBES_FILE_PATH
from clickhouse_driver import Client
import ujson as json
from helpers import haversine, rtt_to_km, is_within_cirle
import sys
sys.path.insert(0, './geoloc-imc-2023/geoloc_imc_2023')


def remove_bad_results():
    with open(BAD_ANCHORS_FILE_PATH, 'r') as json_file:
        bad_anchores = json.load(json_file)
    bad_targeted_ip = []
    bad_source = {}
    for p in bad_anchores:
        bad_targeted_ip.append(p["address_v4"])
        lat = p["geometry"]["coordinates"][1]
        lon = p["geometry"]["coordinates"][0]
        bad_source[(lat, lon)] = p["address_v4"]

    with open(FINAL_ANALYSABLE_FILE_PATH, 'r') as json_file:
        all_results = json.load(json_file)
    print(f"{len(all_results)} done results")
    to_redo = []
    removed_without_redo = 0
    good_results = {}
    bad_vp_count = 0
    tier1_failed_count = 0
    cbg_failed_count = 0
    without_points_info = 0
    no_negative_rtt = 0
    for k, dct in all_results.items():
        if k in bad_targeted_ip:
            removed_without_redo += 1
            continue
        bvp = False
        for vp in dct['vps']:
            if (vp[0], vp[1]) in bad_source:
                bvp = True
        if bvp:
            to_redo.append(k)
            bad_vp_count += 1
            continue
        if not dct['tier1:done']:
            to_redo.append(k)
            tier1_failed_count += 1
            continue
        all_in = True
        candidate_geo = (dct['lat_c'], dct['lon_c'])
        for vp in dct['vps']:
            if not is_within_cirle((vp[0], vp[1]), vp[2], candidate_geo, speed_threshold=4/9):
                all_in = False
        if not all_in:
            to_redo.append(k)
            cbg_failed_count += 1
            continue
        if 'tier2:inspected_points_count' not in dct and 'tier3:inspected_points_count' not in dct:
            to_redo.append(k)
            without_points_info += 1
            continue
        if 'negative_rtt_included' not in dct:
            to_redo.append(k)
            no_negative_rtt += 1
            continue

        good_results[k] = dct

    print(f"{removed_without_redo} result we can remove without redo")
    print(f"{len(to_redo)} targets to redo")
    print(f"{bad_vp_count} to redo because of miss placed vp")
    print(f"{tier1_failed_count} to redo because tier1 failed")
    print(f"{cbg_failed_count} to redo because cbg got the wrong area")
    print(f"{without_points_info} to redo because old without points info")
    print(f"{no_negative_rtt} to redo because old without negative rtt")
    print(f"{len(good_results)} result to keep")

    # with open(FINAL_ANALYSABLE_FILE_PATH, 'w') as outfile:
    #    json.dump(good_results, outfile)


def remove_bad_anchors():
    with open(ALL_ANCHORS_FILE_PATH, 'r') as json_file:
        anchors = json.load(json_file)
    with open(MISLOCATED_PROBES_FILE_PATH, 'r') as json_file:
        miss_placed_probes_ip = json.load(json_file)

    print(f"{len(anchors)} total anchors")
    good_anchors = []
    bad_anchors = []
    incorrect_geolocation_count = 0
    not_enough_vps = 0
    client = Client('127.0.0.1')
    for p in anchors:
        if p['address_v4'] in miss_placed_probes_ip:
            bad_anchors.append(p)
            bad_anchors[-1]['remove_reason'] = "Incorrect geolocation"
            incorrect_geolocation_count += 1
            continue
        target_ip = p['address_v4']
        tmp_res_db = client.execute(
            f'select distinct src_addr from bgp_interdomain_te.street_lvl_traceroutes where resp_addr = \'{target_ip}\' and dst_addr = \'{target_ip}\' and src_addr <> \'{target_ip}\'')
        if len(tmp_res_db) < 100:
            bad_anchors.append(p)
            bad_anchors[-1]['remove_reason'] = "Not enought traceroute data towards"
            bad_anchors[-1]['vp_traceroutes_count'] = len(tmp_res_db)
            not_enough_vps += 1
            continue
        good_anchors.append(p)

    print(f"{len(good_anchors)} anchors to keep")
    print(f"{incorrect_geolocation_count} anchors removed because of incorrect geolocation")
    print(f"{not_enough_vps} anchors removed because the lack of traceroute data towards")

    print(len(good_anchors))
    # with open(GOOD_ANCHORS_FILE_PATH, 'w') as outfile:
    #     json.dump(good_anchors, outfile)
    # with open(BAD_ANCHORS_FILE_PATH, 'w') as outfile:
    #     json.dump(bad_anchors, outfile)


def key_target_ip_spec():
    with open(FINAL_ANALYSABLE_FILE_PATH, 'r') as json_file:
        all_results = json.load(json_file)
    print(f"{len(all_results)} done results")
    diff_lst = []
    for k, v in all_results.items():
        if k != v['target_ip']:
            diff_lst.append((k, v['target_ip']))

    print(len(diff_lst))
    pprint(diff_lst)


def remove_bad_cbg():
    with open(FINAL_ANALYSABLE_FILE_PATH, 'r') as json_file:
        all_results = json.load(json_file)
    print(f"{len(all_results)} done results")
    to_redo = []
    good_results = {}
    tier1_failed_count = 0
    bad_cbg = 0
    for k, dct in all_results.items():
        if not dct['tier1:done']:
            to_redo.append(k)
            tier1_failed_count += 1
            continue
        else:
            tmp_cercles = []
            for vp in dct['vps']:
                tmp_cercles.append((vp[0], vp[1], vp[2], None, None))

            points = get_points_in_poly(tmp_cercles, 36, 5, 4/9)
            if len(points) > 0:
                p1 = points[0]
                p2 = (dct['tier1:lat'], dct['tier1:lon'])
                if haversine(p1, p2) > 0.01:
                    bad_cbg += 1
                    continue
            else:
                print("BAAADD")
        good_results[k] = dct

    print(f"{bad_cbg} to redo because cbg failed")
    print(f"{tier1_failed_count} to redo because tier1 failed")
    print(f"{len(good_results)} result to keep")

    # with open(FINAL_ANALYSABLE_FILE_PATH, 'w') as outfile:
    #    json.dump(good_results, outfile)


def get_ip_list(anchors_file):
    with open(anchors_file, 'r') as json_file:
        anchors = json.load(json_file)

    ip_lst = []
    for anchor in anchors:
        ip_lst.append(anchor['address_v4'])
    print(len(ip_lst))

    with open("anchors_ip_lst.json", 'w') as outfile:
        json.dump(ip_lst, outfile)


if __name__ == '__main__':
    # remove_bad_anchors()
    # remove_bad_results()
    # key_target_ip_spec()
    # remove_bad_cbg()
    get_ip_list(GOOD_ANCHORS_FILE_PATH)
