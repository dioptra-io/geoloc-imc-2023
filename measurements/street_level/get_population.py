import json
import csv
import numpy as np
import requests
import shlex

from subprocess import Popen, PIPE, STDOUT
from pprint import pprint

from utils.helpers import haversine
from env_project import GOOD_ANCHORS_FILE_PATH, POPULATION_CITY_FILE_PATH


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


def load_population_by_city_name():
    geolocation_by_city_name, city_by_geoname_id, geoname_id_by_city, population_by_city_500, \
        all_cities, raw_cities, ngram_cities = \
        input_city_genoname_csv(
            "/srv/geolocation-at-scale/resources/cities500.txt", population_threshold=500)
    return population_by_city_500


def fill_lat_lon(targets):
    res = []
    for d in targets:
        ip = d['address_v4']
        lat = d['geometry']['coordinates'][1]
        lon = d['geometry']['coordinates'][0]
        country_code = d['country_code']
        res.append({'target_ip': ip, 'lat': lat, 'lon': lon,
                   'country_code': country_code})
    return res


def fill_city(targets):
    res = []
    for t in targets:
        if 'city' in t:
            res.append(t)
        else:
            url = f"http://localhost:8080/reverse?format=geojson&lat={t['lat']}&lon={t['lon']}"
            r = requests.get(url)
            elem = r.json()
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


def fill_population(targets):
    res = []
    population_by_city_500 = load_population_by_city_name()

    # for k in population_by_city_500:
    #    if 'IT' in k and 'Mil' in k:
    #        print(k)
    # return

    i = 0
    for t in targets:
        if 'population' in t and t['population'] != 0:
            res.append(t)
        else:
            try:
                t['population'] = population_by_city_500[f"{t['city']}_{t['country_code']}"]
                res.append(t)
            except:
                try:
                    _, output, err = run_cmd(
                        f"cat /srv/geolocation-at-scale/resources/cities500.txt | grep \"{t['city']}\"", is_print_output=False, is_return_output=True)
                    row = output.decode().split("\t")
                    t['population'] = int(row[14])
                    res.append(t)
                except Exception as e:
                    print(e)
                    print(row)
                    print(t)
                    print(f"{t['lat']}, {t['lon']}")
                    t['population'] = 0
                    res.append(t)
                    i += 1
    print(i)
    return res


if __name__ == '__main__':
    # with open(GOOD_ANCHORS_FILE_PATH, 'r') as json_file:
    #    data = json.load(json_file)
    # res = fill_lat_lon(data)
    # res = fill_city(res)
    #
    # with open(POPULATION_CITY_FILE_PATH, 'w') as outfile:
    #    json.dump(res, outfile)

    with open(POPULATION_CITY_FILE_PATH, 'r') as json_file:
        res = json.load(json_file)
    max_pop = 0
    max_v = None
    for r in res:
        if r['density'] > max_pop:
            max_pop = r['density']
            max_v = r

    pprint(max_v)

    # res = fill_population(res)
    # with open(POPULATION_CITY_FILE_PATH, 'w') as outfile:
    #    json.dump(res, outfile)
