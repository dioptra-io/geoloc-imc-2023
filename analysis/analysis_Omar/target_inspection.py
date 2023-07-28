import json
import numpy as np

from pprint import pprint

from utils.helpers import haversine
from test_v2 import local_circle_preprocessing
from plot_utils.plot import plot_multiple_cdf, plot_save

from utils.geoloc_earth import plot_circles_and_points, get_points_in_poly
from env_project import FINAL_ANALYSABLE_FILE_PATH, OLD_ANALYSABLE_FILE_PATH


def test_1():
    res_file_path = FINAL_ANALYSABLE_FILE_PATH
    target_ip = '197.239.73.59'
    with open(res_file_path, 'r') as json_file:
        all_data = json.load(json_file)
    data = all_data[target_ip]
    points = get_points_in_poly(data['vps'], 36, 5, 4/9)
    points.append((data['lat_c'], data['lon_c']))
    plot_circles_and_points(data['vps'], points)


def test_2():
    res_file_path = FINAL_ANALYSABLE_FILE_PATH
    target_ip = '217.29.76.27'
    with open(res_file_path, 'r') as json_file:
        all_data = json.load(json_file)
    data = all_data[target_ip]
    pprint(data['vps'])
    points = get_points_in_poly(data['vps'], 36, 5, 4/9)
    points.append((data['lat_c'], data['lon_c']))
    plot_circles_and_points(data['vps'], points)


def test_3():
    res_file_path = FINAL_ANALYSABLE_FILE_PATH
    target_ip = '149.20.162.6'
    with open(res_file_path, 'r') as json_file:
        all_data = json.load(json_file)
    data = all_data[target_ip]
    pprint(data['vps'])
    points = get_points_in_poly(data['vps'], 36, 5, 4/9)
    points.append((data['lat_c'], data['lon_c']))
    plot_circles_and_points(data['vps'], points)
    # select * from bgp_interdomain_te.street_lvl_traceroutes where resp_addr = '149.20.162.6' and src_addr = '91.209.0.21'
    # 91.209.0.21 in SE
    # 77.37.29.7 in IT


def test_4():
    res_file_path = FINAL_ANALYSABLE_FILE_PATH
    target_ip = '217.168.87.54'
    with open(res_file_path, 'r') as json_file:
        all_data = json.load(json_file)
    data = all_data[target_ip]
    pprint(data['vps'])
    points = get_points_in_poly(data['vps'], 36, 5, 4/9)
    points.append((data['lat_c'], data['lon_c']))
    plot_circles_and_points(data['vps'], points)
    # select * from bgp_interdomain_te.street_lvl_traceroutes where resp_addr = '217.168.87.54' and src_addr = '63.222.7.46'
    # 63.222.7.46 in HK
    # 34.68.239.153 in US (google)
    # 217.168.87.54 in NO


def test_5():
    res_file_path = FINAL_ANALYSABLE_FILE_PATH
    target_ip = '149.20.162.6'
    with open(res_file_path, 'r') as json_file:
        all_data = json.load(json_file)
    data = all_data[target_ip]
    pprint(data['vps'])
    points = get_points_in_poly(data['vps'], 36, 5, 4/9)
    points.append((data['lat_c'], data['lon_c']))
    plot_circles_and_points(data['vps'], points)
    # select * from bgp_interdomain_te.street_lvl_traceroutes where resp_addr = '217.168.87.54' and src_addr = '63.222.7.46'


def test_6():
    res_file_path = FINAL_ANALYSABLE_FILE_PATH
    # target_ip = '185.28.221.65' intersection function not working?
    # target_ip = '46.183.219.225' 4/9 too small
    target_ip = '213.9.97.164'  # not intersection 4/9 too small
    with open(res_file_path, 'r') as json_file:
        all_data = json.load(json_file)
    data = all_data[target_ip]
    # pprint(data['vps'])
    # points = get_points_in_poly(data['vps'], 36, 5, 4/9)
    # points.append((data['lat_c'], data['lon_c']))
    # plot_circles_and_points(data['vps'], points)
    # return
    pprint(data['tier2:final_circles'])
    imp_circles = local_circle_preprocessing(
        data['tier2:final_circles'], speed_threshold=data['speed_threshold'])
    pprint(imp_circles)
    points = get_points_in_poly(data['tier2:final_circles'], 10, 1, 4/9)
    print(points)
    points.append((data['lat_c'], data['lon_c']))
    plot_circles_and_points(data['tier2:final_circles'], points)


def test_7():
    res_file_path = OLD_ANALYSABLE_FILE_PATH
    target_ip = '34.68.239.153'
    target_ip = '92.38.184.82'
    target_ip = '45.121.208.237'
    # target_ip = '103.151.64.31'
    with open(res_file_path, 'r') as json_file:
        all_data = json.load(json_file)
    data = all_data[target_ip]
    tmp_cercles = []
    for vp in data['vps']:
        tmp_cercles.append((vp[0], vp[1], vp[2], None, None))
    pprint(tmp_cercles)
    points = get_points_in_poly(tmp_cercles, 36, 5, 2/3)
    points.append((data['lat_c'], data['lon_c']))
    plot_circles_and_points(tmp_cercles, points, 2/3)


def test_8():
    res_file_path = OLD_ANALYSABLE_FILE_PATH
    extra_good_23 = 0
    extra_good_middel = 0
    bad_all = 0
    used_to_be_good_now_bad = 0
    with open(res_file_path, 'r') as json_file:
        all_data = json.load(json_file)
    for _, d in all_data.items():
        tmp_cercles = []
        for vp in d['vps']:
            tmp_cercles.append((vp[0], vp[1], vp[2], None, None))
        if not d['tier1:done']:
            points = get_points_in_poly(tmp_cercles, 36, 5, 4/9)
            if len(points) > 0:
                extra_good_middel += 1
            else:
                points = get_points_in_poly(tmp_cercles, 36, 5, 2/3)
                if len(points) > 0:
                    extra_good_23 += 1
                else:
                    print(d['target_ip'])
                    bad_all += 1
        else:
            points = get_points_in_poly(tmp_cercles, 36, 5, 4/9)
            if len(points) == 0:
                used_to_be_good_now_bad += 1

    print(extra_good_middel)
    print(extra_good_23)
    print(bad_all)
    print(used_to_be_good_now_bad)


def test_9():
    res_file_path = OLD_ANALYSABLE_FILE_PATH
    errors = []
    with open(res_file_path, 'r') as json_file:
        all_data = json.load(json_file)
    for _, d in all_data.items():
        if d['tier1:done']:
            tmp_cercles = []
            for vp in d['vps']:
                tmp_cercles.append((vp[0], vp[1], vp[2], None, None))

            points = get_points_in_poly(tmp_cercles, 36, 5, 4/9)
            if len(points) > 0:
                p1 = points[0]
                p2 = (d['tier1:lat'], d['tier1:lon'])
                errors.append(haversine(p1, p2))
            else:
                print("BAAAAD")

    print(min(errors))
    print(max(errors))
    print(np.median(errors))
    print(len([i for i in errors if i > 0.01]))
    for i in errors:
        if i > 0.01:
            print(i)
    plot_multiple_cdf([errors], 10000, 0.1, None,
                      'Error of old CDF', 'CDF of distances', None, xscale="log")
    plot_save("./fig/redo.pdf", is_tight_layout=True)


if __name__ == '__main__':
    test_9()
