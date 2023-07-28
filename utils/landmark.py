import requests
import json
import overpy
import dns
import dns.resolver
import urllib3
import pyasn
import warnings

from pprint import pprint
from multiprocessing import Pool
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from geopy import Point, distance

from env_project import CACHED_WEBSITES_FILE_PATH, IP_TO_ASN_FILE_PATH


warnings.simplefilter("ignore", category=MarkupResemblesLocatorWarning)
urllib3.disable_warnings()


def get_bounding_box(lat, lon):
    p = Point(lat, lon)
    d = distance.distance(kilometers=2).meters
    top_right = distance.distance(meters=d).destination(p, 45)
    bottom_left = distance.distance(meters=d).destination(p, 225)
    return (bottom_left.latitude, bottom_left.longitude, top_right.latitude, top_right.longitude)


def check_domain_name_ip(domain_name, ip_address, protocol):
    # print(f"Checking {domain_name}")
    ip_url = protocol + "://" + ip_address
    domain_url = protocol + "://" + domain_name
    try:
        ip_response = requests.get(ip_url, verify=False, timeout=1)
        if ip_response.status_code != 200:
            return False
        domain_response = requests.get(domain_url, timeout=1)
        if domain_response.status_code != 200:
            return False
    except Exception:
        # print(traceback.format_exc())
        return False

    try:
        ip_soup = BeautifulSoup(ip_response.content, "html.parser")
        domain_soup = BeautifulSoup(domain_response.content, "html.parser")
        ip_title = ip_soup.head.title.text
        domain_title = domain_soup.head.title.text
        if ip_title == domain_title:
            return True
        else:
            return False
    except:
        return False


def check_and_get_website_ip(website, protocol):
    asns = ['20940', '16625', '12222', '16625', '21342', '21399', '32787', '35994', '35993', '35995', '36408', '393234', '394689',
            '13335', '202018', '202109', '133293', '395747',
            '54113', '209242',
            '16509', '14618', '16509', '39111', '16509',
            '8075', '8075', '8075', '12076', '12222',
            '15169', '36351', '22577', '36040', '55023',
            '22822',
            '701', '22394, 11608, 11608',
            '3356', '133229, 133229, 395570',
            '60068', '136620', '395354',
            '32934']
    res = {}
    asndb = pyasn.pyasn(IP_TO_ASN_FILE_PATH)
    try:
        result = dns.resolver.resolve(website)
    except Exception:
        # print(traceback.format_exc())
        return {'dns-failed': True}
    if len(result) == 0:
        return {'dns-failed': True}
    res = {'dns-failed': False}

    ip = result[0].to_text()
    res['ip'] = ip
    asn = asndb.lookup(ip)[0]
    if asn == None:
        res['asn-found'] = False
        return res
    else:
        res['asn-found'] = True
    if str(asn) in asns or 'google' in website or 'facebook' in website or 'amazon' in website or 'microsoft' in website or 'azure' in website or 'akamai' in website or 'cdn' in website:
        res['cdn'] = True
        return res
    else:
        res['cdn'] = False

    if check_domain_name_ip(website, ip, protocol):
        res['header-test'] = True
        return res
    else:
        res['header-test'] = False
        return res


def get_one_website_ip(domain, protocol, lat, lon):
    ip_info = check_and_get_website_ip(domain, protocol)
    ip_info['domain'] = domain
    ip_info['protocol'] = protocol
    ip_info['lat'] = lat
    ip_info['lon'] = lon
    return ip_info


def get_all_website_ips(landmarks, tmp_save=False):
    res = []
    with Pool() as pool:
        results = pool.starmap(get_one_website_ip, landmarks)
        for result in results:
            if result != None:
                res.append(result)
    return res


def get_landmarks_with_website_from_lat_lon(lat_arg, lon_arg):
    # api = overpy.Overpass()
    # api = overpy.Overpass(url="https://overpass.kumi.systems/api/interpreter")
    api = overpy.Overpass(
        url="https://maps.mail.ru/osm/tools/overpass/api/interpreter")
    bbox = get_bounding_box(lat_arg, lon_arg)
    query = f"""
        [out:json];
        (
        node ({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]})
            [website];
        way ({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]})
            [website];
        );
        out;
    """
    result = api.query(query)
    res = []
    for node in result.nodes:
        lat = float(node.lat)
        lon = float(node.lon)
        tags = node.tags
        website = tags['website']
        res.append((website, lat, lon))
    for way in result.ways:
        try:
            tmp_lat = 0
            tmp_lon = 0
            nodes = way.get_nodes(resolve_missing=True)
            for node in nodes:
                tmp_lat += float(node.lat)
                tmp_lon += float(node.lon)
            lat = tmp_lat/len(nodes)
            lon = tmp_lon/len(nodes)
            tags = way.tags
            website = tags['website']
            res.append((website, lat, lon))
        except:
            continue
    return res


def get_landmarks_with_website_in_area(area_name, postcode):
    # api = overpy.Overpass()
    # api = overpy.Overpass(url="https://overpass.kumi.systems/api/interpreter")
    api = overpy.Overpass(
        url="https://maps.mail.ru/osm/tools/overpass/api/interpreter")
    query = f"""
        [out:json];
        area[name="{area_name}"]->.small;
        (
            node
                [website]
                ["addr:postcode"="{postcode}"]
                (area.small);
            way
                [website]
                ["addr:postcode"="{postcode}"]
                (area.small);
        );
        out;
    """
    result = api.query(query)
    res = []
    for node in result.nodes:
        lat = float(node.lat)
        lon = float(node.lon)
        tags = node.tags
        website = tags['website']
        res.append((website, lat, lon, tags))
    for way in result.ways:
        try:
            tmp_lat = 0
            tmp_lon = 0
            nodes = way.get_nodes(resolve_missing=True)
            for node in nodes:
                tmp_lat += float(node.lat)
                tmp_lon += float(node.lon)
            lat = tmp_lat/len(nodes)
            lon = tmp_lon/len(nodes)
            tags = way.tags
            website = tags['website']
            res.append((website, lat, lon))
        except:
            continue
    return res


def get_all_landmarks(area_lst, tmp_save=False):
    args = []
    for x in area_lst:
        args.append((x[0], x[1]))
    all_landmarks = []
    with Pool(8) as pool:
        results = pool.starmap(get_landmarks_with_website_in_area, args)
        for point_res in results:
            if point_res != None:
                for result in point_res:
                    all_landmarks.append(result)
    return all_landmarks


def get_all_landmarks_and_stats_from_points(points):
    dict_website = {}
    print(f"{len(points)} Points to look for")
    with Pool(8) as pool:
        results = pool.starmap(get_landmarks_with_website_from_lat_lon, points)
        for result in results:
            if result != None and result != []:
                for elem in result:
                    dict_website[elem[0]] = elem

    print(f"{len(dict_website)} website found")
    unique_website = {}
    for url in dict_website:
        if "://" in url:
            protocol = url.split("://")[0]
            domain_name = url.split("://")[1]
        else:
            protocol = "http"
            domain_name = url
        website = domain_name.split("/")[0]
        if (website, protocol) not in unique_website:
            unique_website[(website, protocol)] = dict_website[url]

    print(f"{len(unique_website)} unique website found")

    args = []
    failed_dns_count = 0
    failed_asn_count = 0
    cdn_count = 0
    failed_header_test_count = 0
    landmarks = []

    with open(CACHED_WEBSITES_FILE_PATH) as json_file:
        all_websites = json.load(json_file)

    for k, v in unique_website.items():
        if k[0] not in all_websites:
            args.append((k[0], k[1], v[1], v[2]))
        else:
            result = all_websites[k[0]]
            if 'dns-failed' not in result or result['dns-failed']:
                failed_dns_count += 1
                continue
            if 'asn-found' not in result or not result['asn-found']:
                failed_asn_count += 1
                continue
            if 'cdn' not in result or result['cdn']:
                cdn_count += 1
                continue
            if 'header-test' not in result or not result['header-test']:
                failed_header_test_count += 1
                continue
            landmarks.append(
                (result['ip'], result['domain'], result['lat'], result['lon']))

    with Pool() as pool:
        results = pool.starmap(get_one_website_ip, args)
        # print(f"results are here {len(results)}")
        for result in results:
            all_websites[result['domain']] = result
            if 'dns-failed' not in result or result['dns-failed']:
                failed_dns_count += 1
                continue
            if 'asn-found' not in result or not result['asn-found']:
                failed_asn_count += 1
                continue
            if 'cdn' not in result or result['cdn']:
                cdn_count += 1
                continue
            if 'header-test' not in result or not result['header-test']:
                failed_header_test_count += 1
                continue
            landmarks.append(
                (result['ip'], result['domain'], result['lat'], result['lon']))

    with open(CACHED_WEBSITES_FILE_PATH, 'w') as outfile:
        json.dump(all_websites, outfile)

    return failed_dns_count, failed_asn_count, cdn_count, failed_header_test_count, landmarks


def fix_websites():
    with open(CACHED_WEBSITES_FILE_PATH) as json_file:
        all_websites = json.load(json_file)
    for k, v in all_websites.items():
        if 'google' in k or 'facebook' in k or 'amazon' in k or 'microsoft' in k or 'azure' in k or 'akamai' in k or 'cdn' in k:
            all_websites[k]['cdn'] = True

    with open(CACHED_WEBSITES_FILE_PATH, 'w') as outfile:
        json.dump(all_websites, outfile)


def filter_websites(all_landmarks):
    dict_res = {}
    for info in all_landmarks:
        url = info[0]
        if "://" in url:
            protocol = url.split("://")[0]
            domain_name = url.split("://")[1]
        else:
            protocol = "http"
            domain_name = url
        website = domain_name.split("/")[0]
        if (website, protocol) not in dict_res:
            dict_res[(website, protocol)] = info
    res = []
    for k, v in dict_res.items():
        res.append((k[0], k[1], v[1], v[2]))
    return res


def get_zipcodes_for_points(points, tmp_save=False):
    print(f"{len(points)} zipcodes to look for")
    zipcodes = []
    res = []
    for point in points:
        url = f"https://nominatim.openstreetmap.org/reverse?format=geojson&lat={point[0]}&lon={point[1]}"
        r = requests.get(url)
        elem = r.json()
        if 'features' not in elem or len(elem['features']) != 1:
            continue
        info = elem['features'][0]
        if 'properties' not in info or 'address' not in info['properties']:
            continue
        address = info['properties']['address']
        if 'postcode' not in address:
            # pprint(address)
            postcode = None
        else:
            postcode = address['postcode']
        if 'city' in address:
            area_name = address['city']
        elif 'city_district' in address:
            area_name = address['city_district']
        elif 'town' in address:
            area_name = address['town']
        elif 'village' in address:
            area_name = address['village']
        elif 'suburb' in address:
            area_name = address['suburb']
        elif 'state' in address:
            area_name = address['state']
        else:
            area_name = None
        if area_name != None and postcode != None:
            res.append((area_name, postcode))
        zipcodes.append(elem)
    return res


if __name__ == '__main__':
    fix_websites()
