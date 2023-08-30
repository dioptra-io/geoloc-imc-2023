import requests
import overpy
import dns
import dns.resolver
import urllib3
import pyasn
import warnings

from multiprocessing import Pool
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from geopy import Point, distance

from scripts.utils.file_utils import load_json, dump_json
from default import CACHED_WEBSITES_FILE, IP_TO_ASN_FILE


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
    asndb = pyasn.pyasn(IP_TO_ASN_FILE)
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

    try:
        all_websites = load_json(CACHED_WEBSITES_FILE)
    except FileNotFoundError:
        all_websites = {}

    for k, v in unique_website.items():
        # fix websites
        if 'google' in k or 'facebook' in k or 'amazon' in k or 'microsoft' in k or 'azure' in k or 'akamai' in k or 'cdn' in k:
            all_websites[k]['cdn'] = True

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

    dump_json(all_websites, CACHED_WEBSITES_FILE)

    return failed_dns_count, failed_asn_count, cdn_count, failed_header_test_count, landmarks
