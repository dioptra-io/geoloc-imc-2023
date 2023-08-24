import time

from scripts.analysis.analysis import local_circle_preprocessing
from scripts.analysis.landmark import get_all_landmarks_and_stats_from_points
from scripts.utils.helpers import get_center_of_poly, get_points_in_poly
from scripts.traceroute_measurements.traceroutes import get_circles_to_target, start_and_get_traceroutes


from scripts.utils.file_utils import load_json


def tier_1(target_ip, res):
    st = time.time()
    circles_file = load_json("circles.json")
    # all_circles = get_circles_to_target(target_ip)
    all_circles = circles_file[target_ip]
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
