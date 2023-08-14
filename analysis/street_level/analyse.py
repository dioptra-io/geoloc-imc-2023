import pyasn
from env_project import FINAL_ANALYSABLE_FILE_PATH, IP_TO_ASN_FILE_PATH, POPULATION_CITY_FILE_PATH
from ipaddress import ip_network
from clickhouse_driver import Client
from plot_utils.plot import plot_multiple_cdf, plot_scatter, plot_save, plot_scatter_multiple
import math
from scipy.stats import pearsonr
from geoloc_earth import get_points_in_poly, plot_circles_and_points
import statistics
import seaborn as sns
from matplotlib import pyplot as plt
import numpy as np
from pprint import pprint
import ujson as json
from helpers import haversine, rtt_to_km, is_within_cirle, polygon_centroid, circle_intersections, distance
import sys
sys.path.insert(0, './geoloc-imc-2023/geoloc_imc_2023')


def success_rate(data):
    feilds_count = {'tier1:done': 0, 'tier2:done': 0, 'tier3:done': 0}
    for _, d in data.items():
        for feild in feilds_count:
            if d[feild]:
                feilds_count[feild] += 1
    print(f"{len(data)} Total targets done")
    for k, v in feilds_count.items():
        print(f"{v} {k}")

    dict_reasons = {
        'tier2_failed_because_no_zipcodes': 0,
        'tier2_failed_because_no_landmark': 0,
        'tier2_failed_because_no_valid_traceroute': 0,
        'tier2_failed_because_other': 0,
        'tier3_failed_because_no_zipcodes': 0,
        'tier3_failed_because_no_landmark': 0,
        'tier3_failed_because_no_valid_traceroute': 0,
        'tier3_failed_because_other': 0
    }

    for _, d in data.items():
        if not d['tier1:done']:  # Here you should analyse tier1
            continue
        if not d['tier2:done']:
            if d['tier2:inspected_points_count'] == 0:
                dict_reasons['tier2_failed_because_no_zipcodes'] += 1
                continue
            if d['tier2:landmark_count'] == 0:
                dict_reasons['tier2_failed_because_no_landmark'] += 1
                continue
            one_traceroute_found = False
            for t in d['tier2:traceroutes']:
                if t[4] > 0:
                    one_traceroute_found = True
                    break
            if not one_traceroute_found:
                dict_reasons['tier2_failed_because_no_valid_traceroute'] += 1
                continue
            dict_reasons['tier2_failed_because_other'] += 1
            continue
        if not d['tier3:done']:
            if d['tier3:inspected_points_count'] == 0:
                dict_reasons['tier3_failed_because_no_zipcodes'] += 1
                # if d['target_ip'] not in ['185.28.221.65', '46.183.219.225']:
                #    print(d['target_ip'])
                #    exit()
                continue
            if d['tier3:landmark_count'] == 0:
                dict_reasons['tier3_failed_because_no_landmark'] += 1
                continue
            one_traceroute_found = False
            for t in d['tier3:traceroutes']:
                if t[4] > 0:
                    one_traceroute_found = True
                    break
            if not one_traceroute_found:
                dict_reasons['tier3_failed_because_no_valid_traceroute'] += 1
                continue
            dict_reasons['tier3_failed_because_other'] += 1
            continue

    for k, v in dict_reasons.items():
        print(f"{k} {v}")


def cdf_error(data):
    error1 = []
    error2 = []
    error3 = []
    error4 = []

    filtered_error1 = []
    filtered_error2 = []
    filtered_error3 = []
    filtered_error4 = []
    for _, d in data.items():
        errors = every_tier_result_and_errors(d)
        error1.append(errors['error1'])
        error2.append(errors['error2'])
        error3.append(errors['error3'])
        error4.append(errors['error4'])
        if d['tier1:done'] and 'tier2:landmarks' in d and len(d['tier2:landmarks']) > 0:
            filtered_error1.append(errors['error1'])
            filtered_error2.append(errors['error2'])
            filtered_error3.append(errors['error3'])
            filtered_error4.append(errors['error4'])

    print(len(error1))
    print(len(error2))
    print(len(error3))
    print(len(error4))
    print(len([i for i in error4 if i <= 1]))

    street_lvl_count_cbg = 0
    street_lvl_count_tech = 0
    for e in error1:
        if e <= 1:
            street_lvl_count_cbg += 1
    for e in error3:
        if e <= 1:
            street_lvl_count_tech += 1
    print(f"{street_lvl_count_cbg} targets are geolocated at street lvl using CBG {street_lvl_count_cbg/len(error1)}")
    print(f"{street_lvl_count_tech} targets are geolocated at street lvl using tech {street_lvl_count_tech/len(error3)}")

    median1 = np.median(error1)
    median2 = np.median(error2)
    median3 = np.median(error3)
    median4 = np.median(error4)

    print(f"tier 1 median error = {median1}")
    print(f"tier 2 median error = {median2}")
    print(f"tier 3 median error = {median3}")
    print(f"closest landmark distance median = {median4}")

    fmedian1 = np.median(filtered_error1)
    fmedian2 = np.median(filtered_error2)
    fmedian3 = np.median(filtered_error3)
    fmedian4 = np.median(filtered_error4)

    print(f"filtered tier 1 median error = {fmedian1}")
    print(f"filtered tier 2 median error = {fmedian2}")
    print(f"filtered tier 3 median error = {fmedian3}")
    print(f"filtered closest landmark distance median = {fmedian4}")

    less_then_1 = 0
    less_then_1_lm = 0
    for e in error3:
        if e <= 1:
            less_then_1 += 1
    for e in error4:
        if e <= 1:
            less_then_1_lm += 1
    print(f"{less_then_1} targets are geolocated at street lvl out of {len(error3)} or {less_then_1*100/len(error3)}%")
    print(f"{less_then_1_lm} targets has a landmark at street lvl out of {len(error4)} or {less_then_1_lm*100/len(error4)}%")

    plot_multiple_cdf([error3, error1, error4], 10000, 0.1, None, 'Geolocation error (km)',
                      'CDF of targets', ["Street Level", "CBG", "Closest Landmark"])
    plt.legend(fontsize="14")
    plot_save("./fig/error_t1_t3_t4.pdf", is_tight_layout=True)

    plot_multiple_cdf([error3, error1, error4], 10000, 0.1, None, 'Geolocation error (km)',
                      'CDF of targets', ["Street Level", "CBG", "Closest Landmark"], xscale="log")
    plt.legend(fontsize="14")
    plot_save("./fig/error_t1_t3_t4_log.pdf", is_tight_layout=True)

    plot_multiple_cdf([error3, error1, error4, error2], 10000, 0.1, None, 'Geolocation error (km)',
                      'CDF of targets', ["Street Level", "CBG", "Closest Landmark", "Tier 2 estimation"])
    plt.legend(fontsize="14")
    plot_save("./fig/error_t1_t2_t3_t4.pdf", is_tight_layout=True)

    plot_multiple_cdf([error3, error1, error4, error2], 10000, 0.1, None, 'Geolocation error (km)', 'CDF of targets', [
                      "Street Level", "CBG", "Closest Landmark", "Tier 2 estimation"], xscale="log")
    plt.legend(fontsize="14")
    plot_save("./fig/error_t1_t2_t3_t4_log.pdf", is_tight_layout=True)

    plot_multiple_cdf([filtered_error3, filtered_error1, filtered_error4, filtered_error2], 10000, 0.1, None,
                      'Geolocation error (km)', 'CDF of targets', ["Street Level", "CBG", "Closest Landmark", "Tier 2 estimation"])
    plt.legend(fontsize="14")
    plot_save("./fig/filtered_error_t1_t2_t3_t4.pdf", is_tight_layout=True)

    plot_multiple_cdf([filtered_error3, filtered_error1, filtered_error4, filtered_error2], 10000, 0.1, None,
                      'Geolocation error (km)', 'CDF of targets', ["Street Level", "CBG", "Closest Landmark", "Tier 2 estimation"], xscale="log")
    plt.legend(fontsize="14")
    plot_save("./fig/filtered_error_t1_t2_t3_t4_log.pdf", is_tight_layout=True)


def cdf_min_dist_landmark(data):
    without_landmarks_count = 0
    with_landmarks_count = 0
    distances = []
    for _, d in data.items():
        landmarks = []
        if 'tier2:landmarks' in d:
            for l in d['tier2:landmarks']:
                landmarks.append(l)
        if 'tier3:landmarks' in d:
            for l in d['tier3:landmarks']:
                landmarks.append(l)
        if len(landmarks) == 0:
            without_landmarks_count += 1
        else:
            with_landmarks_count += 1
            mindist = haversine((d['lat_c'], d['lon_c']),
                                (landmarks[0][2], landmarks[0][3]))
            for l in landmarks[1:]:
                dist = haversine((d['lat_c'], d['lon_c']), (l[2], l[3]))
                mindist = min(mindist, dist)
            distances.append(mindist)

    median = np.median(distances)
    print(f"Median distance to nearest landmark = {median}")

    plot_multiple_cdf([distances], 10000, 0.1, None,
                      'Distance to the nearest landmark (km)', 'CDF of targets', None)
    plot_save("./fig/distance_to_landmark.pdf", is_tight_layout=True)

    plot_multiple_cdf([distances], 10000, 0.1, None,
                      'Distance to the nearest landmark (km)', 'CDF of targets', None, xscale="log")
    plot_save("./fig/distance_to_landmark_log.pdf", is_tight_layout=True)

    print(f"{with_landmarks_count} targets with at least one landmark")
    print(f"{without_landmarks_count} targets without any landmark")


def get_all_bgp_prefixes():
    client = Client('127.0.0.1')
    db_table = client.execute(
        f'select distinct prefix from bgp_interdomain_te.IPv4_3238002744')
    res = {}
    for line in db_table:
        pref = line[0]
        if "." in pref:
            res[pref] = 1
    return res


def is_same_bgp_prefix(ip1, ip2, prefixes):
    for i in range(8, 25):
        n1 = ip_network(ip1+f"/{i}", strict=False).network_address
        n2 = ip_network(ip2+f"/{i}", strict=False).network_address
        if n1 == n2:
            if f"{str(n1)}/{i}" in prefixes:
                return True
        else:
            break
    return False


def correlation_same_network(data):
    asn_coef_lst = []
    bgp_coef_lst = []
    asndb = pyasn.pyasn(IP_TO_ASN_FILE_PATH)
    bgp_prefixes = get_all_bgp_prefixes()
    for _, d in data.items():
        same_bgp_x = []
        same_bgp_y = []
        same_asn_x = []
        same_asn_y = []
        for f in ['tier2:traceroutes', 'tier3:traceroutes']:
            if f in d:
                for t in d[f]:
                    if t[4] < 0:
                        continue
                    distance = haversine(
                        (t[5], t[6]), (d['lat_c'], d['lon_c']))
                    ipt = t[1]
                    ipl = t[2]
                    asnt = asndb.lookup(ipt)[0]
                    asnl = asndb.lookup(ipl)[0]
                    if asnl != None and asnt != None:
                        if asnt == asnl and distance not in same_asn_y:
                            same_asn_y.append(distance)
                            same_asn_x.append(t[4])

                    if is_same_bgp_prefix(ipt, ipl, bgp_prefixes):
                        if distance not in same_bgp_y:
                            same_bgp_y.append(distance)
                            same_bgp_x.append(t[4])
        if len(same_asn_x) > 1:
            correlation = pearsonr(same_asn_x, same_asn_y)[0]
            asn_coef_lst.append(correlation)
        if len(same_bgp_x) > 1:
            correlation = pearsonr(same_bgp_x, same_bgp_y)[0]
            bgp_coef_lst.append(correlation)

    print(f"{len(asn_coef_lst)} targets with correlation asn")
    print(f"{len(bgp_coef_lst)} targets with correlation bgp")
    print(f"{np.median(bgp_coef_lst)} median bgp correlation")
    print(f"{np.median(asn_coef_lst)} median asn correlation")


def ping_go_do(data):
    res_dct = {}
    res = []
    for _, d in data.items():
        for f in ['tier2:landmarks', 'tier3:landmarks']:
            target_geo = (d['lat_c'], d['lon_c'])
            if f in d:
                for l in d[f]:
                    landmark_geo = (l[2], l[3])
                    distance = haversine(target_geo, landmark_geo)
                    if distance <= 40:
                        res_dct[(d['target_ip'], l[0])] = float(distance)
    print(len(res_dct))
    for k, v in res_dct.items():
        res.append({'target_ip': k[0], 'landmark_ip': k[1], 'distance': v})

    with open("ping_todo.json", 'w') as outfile:
        json.dump(res, outfile)

    return res


def cdf_landmarks(data):
    valid_landmarks_count = 0
    unvalid_landmarks_count = 0
    values = []
    same_asn_lst = []
    same_24_lst = []
    same_bgp_lst = []
    all_traceroutes_count = 0
    no_r1_traceroutes_count = 0
    asndb = pyasn.pyasn(IP_TO_ASN_FILE_PATH)
    distances_to_landmarks = []
    all_landmarks = []
    bgp_prefixes = get_all_bgp_prefixes()
    for _, d in data.items():
        good = 0
        bad = 0
        same_asn = 0
        diff_asn = 0
        same_bgp = 0
        diff_bgp = 0
        same_24 = 0
        diff_24 = 0
        all_landmarks.append(0)
        if "tier2:cdn_count" in d and "tier2:landmark_count" in d and "tier2:failed_header_test_count" in d:
            all_landmarks[-1] += d['tier2:landmark_count'] + \
                d['tier2:cdn_count'] + d['tier2:failed_header_test_count']
            valid_landmarks_count += d['tier2:landmark_count']
            unvalid_landmarks_count += d['tier2:cdn_count'] + \
                d['tier2:failed_header_test_count']
        if "tier3:cdn_count" in d and "tier3:landmark_count" in d and "tier3:failed_header_test_count" in d:
            all_landmarks[-1] += d['tier3:landmark_count'] + \
                d['tier3:cdn_count'] + d['tier3:failed_header_test_count']
            valid_landmarks_count += d['tier3:landmark_count']
            unvalid_landmarks_count += d['tier3:cdn_count'] + \
                d['tier3:failed_header_test_count']
        for f in ['tier2:traceroutes', 'tier3:traceroutes']:
            if f in d:
                for t in d[f]:
                    if t[4] < 0:
                        bad += 1
                    else:
                        good += 1

                    all_traceroutes_count += 1
                    if t[3] == None:
                        no_r1_traceroutes_count += 1

                    ipt = t[1]
                    ipl = t[2]
                    asnt = asndb.lookup(ipt)[0]
                    asnl = asndb.lookup(ipl)[0]
                    if asnl != None and asnt != None:
                        if asnt == asnl:
                            same_asn += 1
                        else:
                            diff_asn += 1
                    nt = ip_network(ipt+"/24", strict=False).network_address
                    nl = ip_network(ipl+"/24", strict=False).network_address
                    if nt == nl:
                        same_24 += 1
                    else:
                        diff_24 += 1

                    if is_same_bgp_prefix(ipt, ipl, bgp_prefixes):
                        same_bgp += 1
                    else:
                        diff_bgp += 1
        distances = []
        for f in ['tier2:landmarks', 'tier3:landmarks']:
            target_geo = (d['lat_c'], d['lon_c'])
            if f in d:
                for l in d[f]:
                    landmark_geo = (l[2], l[3])
                    distances.append(haversine(target_geo, landmark_geo))
        distances_to_landmarks.append(distances)

        if same_asn != 0 or diff_asn != 0:
            same_asn_lst.append(same_asn/(same_asn+diff_asn))

        if same_24 != 0 or diff_24 != 0:
            same_24_lst.append(same_24/(same_24+diff_24))
            if same_24 != 0:
                print(
                    f"Found {d['target_ip']} with a landmark in the same /24")
        if same_bgp != 0 or diff_bgp != 0:
            same_bgp_lst.append(same_bgp/(diff_bgp+same_bgp))

        if good != 0 or bad != 0:
            values.append(bad/(bad+good))

    print(f"{no_r1_traceroutes_count} no r1 found out of {all_traceroutes_count}")
    plot_multiple_cdf([values], 10000, 0, 1,
                      'Fraction of landmarks with\nD1 + D2 < 0', 'CDF of targets', None)
    plot_save("./fig/invalid_rtt.pdf", is_tight_layout=True)

    # plot_multiple_cdf([error3, error1, error4, error2], 10000, 0.1, None, 'Error distance (km)', 'CDF of error distance', ["Street Level", "CBG", "Closest Landmarks", "Tier 2 estimation"])
    only_outside_asn = 0
    for x in same_asn_lst:
        if x == 0:
            only_outside_asn += 1
    only_outside_24 = 0
    for x in same_24_lst:
        if x == 0:
            only_outside_24 += 1
    only_outside_bgp = 0
    for x in same_bgp_lst:
        if x == 0:
            only_outside_bgp += 1

    print(f"{valid_landmarks_count} total valid landmarks")
    print(f"{unvalid_landmarks_count} unvalid landmarks")
    print(f"{(valid_landmarks_count*100)/(valid_landmarks_count+unvalid_landmarks_count)}% valid landmarks")

    print(f"{only_outside_asn} targets has all its landmarks outside its AS out of {len(same_asn_lst)} {only_outside_asn*100/(len(same_asn_lst))}%")
    print(f"{only_outside_24} targets has all its landmarks outside its /24 out of {len(same_24_lst)} {only_outside_24*100/(len(same_24_lst))}%")
    print(f"{only_outside_bgp} targets has all its landmarks outside its BGP prefix out of {len(same_bgp_lst)} {only_outside_bgp*100/(len(same_bgp_lst))}%")

    plot_multiple_cdf([same_asn_lst, same_bgp_lst, same_24_lst], 10000, None, None,
                      'Fraction of landmarks and targets\nsharing network', 'CDF of targets', ['ASN', 'BGP prefix', '/24'])
    plt.legend(fontsize="14")
    plot_save("./fig/landmarks_targets_network.pdf", is_tight_layout=True)

    landmarks_all = []
    landmarks_less_1 = []
    landmarks_less_5 = []
    landmarks_less_10 = []
    landmarks_less_40 = []
    total_count_ping = 0
    for landmark_distances in distances_to_landmarks:
        # if len(landmark_distances) == 0:
        #     continue
        landmarks_all.append(len(landmark_distances))
        landmarks_less_1.append(len([i for i in landmark_distances if i <= 1]))
        landmarks_less_5.append(len([i for i in landmark_distances if i <= 5]))
        landmarks_less_10.append(
            len([i for i in landmark_distances if i <= 10]))
        landmarks_less_40.append(
            len([i for i in landmark_distances if i <= 40]))
        total_count_ping += len([i for i in landmark_distances if i <= 40])

    print(f"{total_count_ping} ping measurement to do")

    lm_a_0 = len([i for i in all_landmarks if i > 0])
    lmv_a_0 = len([i for i in landmarks_all if i > 0])
    lm1_0 = len([i for i in landmarks_less_1 if i > 0])
    lm5_0 = len([i for i in landmarks_less_5 if i > 0])
    lm10_0 = len([i for i in landmarks_less_10 if i > 0])
    lm40_0 = len([i for i in landmarks_less_40 if i > 0])

    lm1_1 = len([i for i in landmarks_less_1 if i >= 1])
    print(lm1_1)

    len_all = len(data)
    print(f"{lm_a_0} target have potentail landmarks or {lm_a_0/len_all}")
    print(f"{lmv_a_0} target have valid landmarks or {lmv_a_0/len_all}")
    print(f"{lm1_0} target with a landmark within 1 km or {lm1_0/len_all}")
    print(f"{lm5_0} target with a landmark within 5 km or {lm5_0/len_all}")
    print(f"{lm10_0} target with a landmark within 10 km or {lm10_0/len_all}")
    print(f"{lm40_0} target with a landmark within 40 km or {lm40_0/len_all}")

    plot_multiple_cdf([all_landmarks, landmarks_all, landmarks_less_1, landmarks_less_5, landmarks_less_10, landmarks_less_40], 10000, 1, 0, 'Number of landmarks', 'CDF of targets', [
                      'All potential landmarks', 'All valid landmarks', 'Landmarks within 1 km', 'Landmarks within 5 km', 'Landmarks within 10 km', 'Landmarks within 40 km'])
    plt.legend(fontsize="14")
    plot_save("./fig/landmarks_count_per_target.pdf", is_tight_layout=True)

    plot_multiple_cdf([landmarks_less_1, landmarks_less_5, landmarks_less_10, landmarks_less_40], 10000, 1, 0, 'Number of landmarks',
                      'CDF of targets', ['Landmarks within 1 km', 'Landmarks within 5 km', 'Landmarks within 10 km', 'Landmarks within 40 km'])
    plt.legend(fontsize="14")
    plot_save("./fig/landmarks_count_per_target_40.pdf", is_tight_layout=True)

    plot_multiple_cdf([all_landmarks, landmarks_all, landmarks_less_1, landmarks_less_5, landmarks_less_10, landmarks_less_40], 10000, 0.8, 0, 'Number of landmarks', 'CDF of targets', [
                      'All potential landmarks', 'All valid landmarks', 'Landmarks within 1 km', 'Landmarks within 5 km', 'Landmarks within 10 km', 'Landmarks within 40 km'], xscale="log")
    plt.legend(fontsize="14")
    plot_save("./fig/landmarks_count_per_target_log.pdf", is_tight_layout=True)

    plot_multiple_cdf([landmarks_less_1, landmarks_less_5, landmarks_less_10, landmarks_less_40], 10000, 1, 0, 'Number of landmarks', 'CDF of targets', [
                      'Landmarks within 1 km', 'Landmarks within 5 km', 'Landmarks within 10 km', 'Landmarks within 40 km'], xscale="log")
    plt.legend(fontsize="14")
    plot_save("./fig/landmarks_count_per_target_40_log.pdf",
              is_tight_layout=True)


def cdf_time_needed_to_geoloc(data):
    time1 = []
    time2 = []
    time3 = []
    values = []
    for _, d in data.items():
        if d['tier1:done'] and 'tier1:duration' in d:
            time1.append(d['tier1:duration'])
        if d['tier2:done'] and 'tier2:duration' in d:
            time2.append(d['tier2:duration'])
        if d['tier3:done'] and 'tier3:duration' in d:
            time3.append(d['tier3:duration'])
            values.append(d['tier1:duration'] +
                          d['tier2:duration']+d['tier3:duration'])

    median1 = np.median(time1)
    median2 = np.median(time2)
    median3 = np.median(time3)
    median = np.median(values)

    print(f"tier 1 median duration = {median1}")
    print(f"tier 2 median duration = {median2}")
    print(f"tier 3 median duration = {median3}")
    print(f"Street Level median duration = {median}")

    plot_multiple_cdf([values], 1000, None, None,
                      'Time to geolocate a target (sec)', 'CDF of targets', None)
    plot_save("./fig/cdf_time_to_geolocate.pdf", is_tight_layout=True)


def cbg_evaluation(data):
    bad = 0
    good = 0
    good_23_only = 0
    empty_vps = 0
    not_empty_vps = 0
    targeted_traceroutes = 0
    not_targeted_traceroutes = 0
    vps_not_working = []
    for _, d in data.items():
        if d['tier1:done']:
            good += 1
        else:
            bad += 1
            points = get_points_in_poly(d['vps'], 36, 5, 4/9)
            if len(points) != 0:
                print(len(points))
            tmp_vps = []
            for vp in d['vps']:
                tmp_vps.append((vp[0], vp[1], vp[2], None, None))
            points = get_points_in_poly(tmp_vps, 36, 5, 2/3)
            if len(points) != 0:
                good_23_only += 1
            else:
                if len(d['vps']) > 0:
                    not_empty_vps += 1
                    vps_not_working.append(d['target_ip'])
                else:
                    empty_vps += 1
                    client = Client('127.0.0.1')
                    tmp_row = client.execute(
                        f'select src_addr, rtt, tstamp from bgp_interdomain_te.street_lvl_traceroutes where dst_addr = \'{d["target_ip"]}\'')
                    if len(tmp_row) != 0:
                        targeted_traceroutes += 1
                        print(f"{d['target_ip']} was targeted by traceroutes")
                    else:
                        not_targeted_traceroutes += 1

    print(vps_not_working)
    print(f"{bad} no intersection out or {bad+good} = {bad/(bad+good)}")
    print(
        f"If the speed where to be 2/3 CBG would have worked for {good_23_only} more targets")
    print(f"{empty_vps} no vp, {not_empty_vps} some vps")
    print(
        f"When no vp found {targeted_traceroutes} target had a traceroute dedecated to it and {not_targeted_traceroutes} did not")

    position_in = 0
    position_out = 0
    would_be_in = 0
    for _, d in data.items():
        if not d['tier1:done']:
            continue
        all_in = True
        candidate_geo = (d['lat_c'], d['lon_c'])
        for vp in d['vps']:
            if not is_within_cirle((vp[0], vp[1]), vp[2], candidate_geo, speed_threshold=4/9):
                all_in = False
        if all_in:
            position_in += 1
        else:
            position_out += 1
            all_in = True
            for vp in d['vps']:
                if not is_within_cirle((vp[0], vp[1]), vp[2], candidate_geo, speed_threshold=2/3):
                    all_in = False
            if all_in:
                would_be_in += 1
            else:
                print(f"{d['target_ip']} is always outside the CBG area")

    print(f"the target was in the CBG area {position_in} times")
    print(f"the target was out of the CBG area {position_out} times")
    print(f"CBG failed {position_out*100/(position_in+position_out)}%")
    print(
        f"If we would use 2/3 {would_be_in} extra targets would be in the CBG area")


def measured_distance_vs_distance(data):
    correlations = []
    mdvd = {}
    scater_plot_data = {}
    for target_ip, d in data.items():
        tmp_landmarks = {}
        for f in ['tier2:traceroutes', 'tier3:traceroutes']:
            if f in d:
                for t in d[f]:
                    # if t[3] == None or t[4]<0:
                    if t[4] < 0:
                        continue
                    landmarks_ip = t[2]
                    measured_distance = rtt_to_km(t[4], 4/9, 300)
                    distance = haversine(
                        (t[5], t[6]), (d['lat_c'], d['lon_c']))
                    if landmarks_ip not in tmp_landmarks:
                        tmp_landmarks[landmarks_ip] = (
                            measured_distance, distance)
                    if measured_distance < tmp_landmarks[landmarks_ip][0]:
                        tmp_landmarks[landmarks_ip] = (
                            measured_distance, distance)
        if len(tmp_landmarks) != 0:
            tmp_dict = {'md': [], 'd': []}
            for k, v in tmp_landmarks.items():
                all_diff = True
                for i in range(len(tmp_dict['d'])):
                    if v[1] == tmp_dict['d'][i]:
                        all_diff = False
                if all_diff:
                    tmp_dict['md'].append(v[0])
                    tmp_dict['d'].append(v[1])
            if len(tmp_dict['md']) > 1:
                correlation = pearsonr(tmp_dict['md'], tmp_dict['d'])[0]
                tmp_dict['correlation'] = correlation
                correlations.append(correlation)
                mdvd[d['target_ip']] = tmp_dict
            if len(tmp_dict['md']) >= 5:  # and len(tmp_dict['md']) <= 15:
                error = every_tier_result_and_errors(d)
                if error['error3'] < 45:
                    scater_plot_data[target_ip] = {
                        'geo_loc_data': d, 'error_data': error, 'mdvd_data': tmp_dict}

    medianc = np.median(correlations)
    minc = min(correlations)
    maxc = max(correlations)

    print(f"Measured Distance vs Distance median correlation = {medianc}")
    print(f"Measured Distance vs Distance min correlation = {minc}")
    print(f"Measured Distance vs Distance max correlation = {maxc}")

    plot_multiple_cdf([correlations], 10000, -1, 1,
                      'Correlation Coef MD Vs D', 'CDF of Correlation Coef', None)
    plot_save("./fig/cdf_md_vs_d.pdf", is_tight_layout=True)

    x1 = []
    x2 = []
    x3 = []
    x4 = []
    y1 = []
    y2 = []
    y3 = []
    y4 = []
    for _, d in scater_plot_data.items():
        if d['error_data']['error3'] != d['error_data']['error1'] and d['error_data']['error3'] < 1:
            if len(x1) == 0:
                x1 = d['mdvd_data']['d']
                y1 = d['mdvd_data']['md']
            if len(x1) > len(d['mdvd_data']['d']):
                x1 = d['mdvd_data']['d']
                y1 = d['mdvd_data']['md']
        if d['error_data']['error3'] != d['error_data']['error1'] and d['error_data']['error3'] < 6 and d['error_data']['error3'] > 4:
            if len(x2) == 0:
                x2 = d['mdvd_data']['d']
                y2 = d['mdvd_data']['md']
            if len(x2) > len(d['mdvd_data']['d']):
                x2 = d['mdvd_data']['d']
                y2 = d['mdvd_data']['md']
        if d['error_data']['error3'] != d['error_data']['error1'] and d['error_data']['error3'] < 11 and d['error_data']['error3'] > 9:
            if len(x3) == 0:
                x3 = d['mdvd_data']['d']
                y3 = d['mdvd_data']['md']
            if len(x3) > len(d['mdvd_data']['d']):
                x3 = d['mdvd_data']['d']
                y3 = d['mdvd_data']['md']
        if d['error_data']['error3'] != d['error_data']['error1'] and d['error_data']['error3'] < 41 and d['error_data']['error3'] > 39:
            if len(x4) == 0:
                x4 = d['mdvd_data']['d']
                y4 = d['mdvd_data']['md']
            if len(x4) > len(d['mdvd_data']['d']):
                x4 = d['mdvd_data']['d']
                y4 = d['mdvd_data']['md']

    list_color = ['r', 'b', 'g', 'y']
    list_mak = ['o', '*', 'x', '+']
    list_lab = ['< 1 km error', '5 km error', '10 km error', '40 km error']
    plot_scatter_multiple([x1, x2, x3, x4], [y1, y2, y3, y4], None, None, 1, None, "log", "log",
                          'Geographical distance (km)', 'Measured distance (km)', list_mak, list_color, [10, 10, 10, 10])
    plt.legend(list_lab, fontsize="14")
    plot_save("./fig/scater_md_vs_d.pdf", is_tight_layout=True)


def api_calles_count(data):
    zipcodes_counts = []
    landmarks_counts = []
    traceroutes_counts = []
    for _, d in data.items():
        zipcodes_count = 0
        landmarks_count = 0
        traceroutes_count = 0

        for f in ['tier2:inspected_points_count', 'tier3:inspected_points_count']:
            if f in d:
                zipcodes_count += d[f]
        if zipcodes_count != 0:
            zipcodes_counts.append(zipcodes_count)

        for f in ["tier2:failed_dns_count", "tier2:failed_asn_count", "tier2:cdn_count", "tier2:non_cdn_count", "tier3:failed_dns_count", "tier3:failed_asn_count", "tier3:cdn_count", "tier3:non_cdn_count"]:
            if f in d:
                landmarks_count += d[f]
        if landmarks_count != 0:
            landmarks_counts.append(landmarks_count)

        for f in ['tier2:traceroutes', 'tier3:traceroutes']:
            if f in d:
                traceroutes_count += len(d[f])
        if traceroutes_count != 0:
            traceroutes_counts.append(traceroutes_count)

    print(f"{np.median(zipcodes_counts)} Zipcode to check (median)")
    print(f"{np.median(traceroutes_counts)} traceroutes to check (median)")
    print(f"{np.median(landmarks_counts)} landmarks to check (median)")

    total = 0
    for zip in zipcodes_counts:
        total += zip
    print(f"{total} Overpass queries")
    total = 0
    for x in landmarks_counts:
        total += x
    print(f"{total} landmarks verification")
    total = 0
    for x in traceroutes_counts:
        total += x
    print(f"{total} traceroutes")


def density_plot(data):
    with open(POPULATION_CITY_FILE_PATH, 'r') as json_file:
        pop_data = json.load(json_file)

    dens_lst = []
    error_lst = []
    for d in pop_data:
        ip = d['target_ip']
        pop = d['density']
        dens_lst.append(pop)
        errors = every_tier_result_and_errors(data[ip])
        error_lst.append(errors['error3'])

    fig, ax = plot_scatter_multiple([error_lst], [dens_lst], 0.1, 10000, 0.1, 100000, "log",
                                    "log", 'Error distance (km)', 'Population Density (people/km²)', ["x"], ["b"], [10])
    degree = 1
    coef = np.polyfit(error_lst, dens_lst, deg=degree)
    xseq = np.linspace(0, 10000, num=100)
    yseq = [0 for i in range(len(xseq))]
    for i in range(len(coef)):
        power = len(coef) - i - 1
        yseq = [(xseq[j]**power)*coef[i]+yseq[j] for j in range(len(xseq))]
    ax.plot(xseq, yseq, color="k", lw=2.5)
    plot_save("./fig/scater_density.pdf", is_tight_layout=True)

    plot_multiple_cdf([dens_lst], 10000, None, None,
                      'Population Density (people/km²)', 'CDF of targets', None, xscale="log")
    plot_save("./fig/cdf_density.pdf", is_tight_layout=True)


if __name__ == '__main__':
    with open(FINAL_ANALYSABLE_FILE_PATH, 'r') as json_file:
        data = json.load(json_file)

    # cbg_evaluation(data)
    # success_rate(data)
    # cdf_error(data)
    # cdf_min_dist_landmark(data)
    # cdf_landmarks(data)
    # cdf_time_needed_to_geoloc(data)
    # measured_distance_vs_distance(data)
    # api_calles_count(data)
    density_plot(data)
    # correlation_same_network(data)
    # ping_go_do(data)
