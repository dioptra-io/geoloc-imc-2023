import requests
import json
import overpy
import dns
import dns.resolver
import urllib3
# import pyasn
import warnings
import shlex
import csv

from pprint import pprint
from subprocess import Popen, PIPE, STDOUT
from multiprocessing import Pool
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from geopy import Point, distance

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

    with open(CACHED_WEBSITES_FILE) as json_file:
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

    with open(CACHED_WEBSITES_FILE, 'w') as outfile:
        json.dump(all_websites, outfile)

    return failed_dns_count, failed_asn_count, cdn_count, failed_header_test_count, landmarks


def fix_websites():
    with open(CACHED_WEBSITES_FILE) as json_file:
        all_websites = json.load(json_file)
    for k, v in all_websites.items():
        if 'google' in k or 'facebook' in k or 'amazon' in k or 'microsoft' in k or 'azure' in k or 'akamai' in k or 'cdn' in k:
            all_websites[k]['cdn'] = True

    with open(CACHED_WEBSITES_FILE, 'w') as outfile:
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


def fill_city(targets):
    res = []
    for d in targets:
        ip = d['address_v4']
        lat = d['geometry']['coordinates'][1]
        lon = d['geometry']['coordinates'][0]
        country_code = d['country_code']
        res.append({'target_ip': ip, 'lat': lat, 'lon': lon,
                   'country_code': country_code})
    for t in targets:
        if 'city' in t:
            res.append(t)
        else:
            url = f"https://nominatim.openstreetmap.org/reverse?format=geojson&lat={t['lat']}&lon={t['lon']}"
            r = requests.get(url)
            try:
                elem = r.json()
            except requests.JSONDecodeError:
                continue
            if 'features' not in elem or len(elem['features']) != 1:
                continue
            info = elem['features'][0]
            if 'properties' not in info or 'address' not in info['properties']:
                continue
            address = info['properties']['address']
            if 'city' in address:
                t['city'] = address['city']
            elif 'village' in address:
                t['city'] = address['village']
            elif 'town' in address:
                t['city'] = address['town']
            elif 'country' in address:
                t['city'] = address['country']
            else:
                pprint(info)
                break
            res.append(t)

    return res


def run_cmd(cmd, is_background=False, stdout=PIPE, is_print_output=True, is_return_output=False):
    if is_background:
        cmd = shlex.split(cmd)
        p = Popen(cmd, stdout=stdout, stderr=STDOUT)
        return p
    else:
        process = Popen(cmd, stdout=stdout, stderr=STDOUT, shell=True)
        out, err = process.communicate()
        if is_print_output:
            out_ = [line.decode("utf-8") for line in out.splitlines()]
        if is_return_output:
            return process, out, err
        return process


def add_city(all_cities, city_low, city_key, lat, long, geoname_id):
    if city_low not in all_cities:
        all_cities[city_low] = [(city_key, (lat, long), geoname_id)]
    else:
        all_cities[city_low].append((city_key, (lat, long), geoname_id))


def input_city_genoname_csv(city_file_path, population_threshold=100000):
    '''
    Format
    geoname_id;name;ascii_name;alternate_names;latitude;longitude;feature_class;feature_code;
    country_code;country_code_2;admin1_code;admin2_code;admin3_code;admin4_code;population;elevation;dem
    ;timezone;modification_date;country;coordinates
    :param city_file_path:
    :return:
    '''

    geolocation_by_city = {}
    city_by_geoname_id = {}
    geoname_id_by_city = {}
    population_by_city = {}

    raw_cities = set()
    ngram_cities = [set() for x in range(0, 8)]
    all_cities = {}
    with open(city_file_path) as csvfile:
        reader = csv.reader(csvfile, delimiter="\t", quotechar='"', )
        next(reader, None)
        for row in reader:
            geoname_id = row[0]
            city = row[1]
            ascii_city = row[2]
            lat, long = float(row[4]), float(row[5])
            # Iso2 code
            country = row[8]
            population = row[14]
            city_key = f"{city}_{country}"
            city_low = city.lower()
            ascii_city_key = f"{ascii_city}_{country}"
            ascii_city_low = ascii_city.lower()
            add_city(all_cities, city_low, city_key, lat, long, geoname_id)
            add_city(all_cities, ascii_city_low,
                     ascii_city_key, lat, long, geoname_id)
            if population != "":
                population = int(float(population))
                if population >= population_threshold:
                    geolocation_by_city[ascii_city_key] = (lat, long)
                    geolocation_by_city[city_key] = (lat, long)
                    city_by_geoname_id[geoname_id] = ascii_city_key
                    geoname_id_by_city[ascii_city_key] = geoname_id
                    geoname_id_by_city[city_key] = geoname_id
                    population_by_city[ascii_city_key] = population
                    population_by_city[city_key] = population
                else:
                    continue
            else:
                continue

            raw_cities.add(ascii_city.lower())
            raw_cities.add(city.lower())
            for i in range(3, 8):
                if len(ascii_city) < i:
                    break
                ngram_cities[i].add(ascii_city.lower()[:i])
    return geolocation_by_city, \
        city_by_geoname_id, \
        geoname_id_by_city, \
        population_by_city, \
        all_cities, raw_cities, ngram_cities


# if __name__ == '__main__':
    # fix_websites()
