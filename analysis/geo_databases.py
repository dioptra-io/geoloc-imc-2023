import os.path
import requests
import pickle
import logging

from bs4 import BeautifulSoup

from utils.common import compute_error_threshold_cdfs
from default import ANCHORS_FILE, REMOVED_PROBES_FILE
from utils.helpers import haversine
from utils.plot_utils import plot_save, plot_multiple_cdf, homogenize_legend
from utils.measurement_utils import load_json, dump_json


ip_info_geo_file = "resources/replicability/ip_info_geo_anchors.json"
maxmind_geo_file = "resources/replicability/maxmind_free_geo_anchors.json"

snapshot_date = "20230516"
maxmind_block_file = f"resources/maxmind/GeoLite2-City-CSV_{snapshot_date}/GeoLite2-City-Blocks-IPv4.csv"
maxmind_tree_file = f"{maxmind_block_file[:-4]}_{snapshot_date}.tree"


def load_radix_tree(maxmind_tree_file=maxmind_tree_file):

    with open(maxmind_tree_file, "rb") as f:
        tree = pickle.load(f)
        return tree


def maxmind_paid():
    html = '<tbody id="geoip-demo-results-tbody" data-use-downloadable-db="1"><tr class="geoip-results"><td>101.53.31.6</td><td>VN</td><td>San Thang,<br>Tinh Lai Chau,<br>Vietnam,<br>Asia</td><td>101.53.31.0/25</td><td></td><td>22.394,<br>103.5045</td><td>20</td><td>Netnam Company</td><td>Netnam Company</td><td>netnam.vn</td><td></td></tr><tr class="geoip-results"><td>102.130.49.144</td><td>ZA</td><td>Johannesburg,<br>Gauteng,<br>South Africa,<br>Africa</td><td>102.130.49.0/24</td><td>2001</td><td>-26.3811,<br>27.8376</td><td>20</td><td>Misaka Network, Inc.</td><td>Misaka Network, Inc.</td><td>misaka.io</td><td></td></tr><tr class="geoip-results"><td>102.163.100.12</td><td>MU</td><td>Port Mathurin,<br>Rodrigues,<br>Mauritius,<br>Africa</td><td>102.163.100.0/22</td><td></td><td>-19.6793,<br>63.4164</td><td>5</td><td>Emtel</td><td>Emtel</td><td></td><td></td></tr><tr class="geoip-results"><td>102.222.106.178</td><td>MU</td><td>Mauritius,<br>Africa</td><td>102.222.106.0/23</td><td></td><td>-20.3,<br>57.5833</td><td>50</td><td>cloud.mu</td><td>cloud.mu</td><td></td><td></td></tr><tr class="geoip-results"><td>103.102.166.20</td><td>US</td><td>United States,<br>North America</td><td>103.102.166.0/24</td><td></td><td>37.751,<br>-97.822</td><td>1000</td><td>Wikimedia Foundation</td><td>Wikimedia Foundation</td><td></td><td></td></tr><tr class="geoip-results"><td>103.113.176.82</td><td>TH</td><td>Thailand,<br>Asia</td><td>103.113.176.0/22</td><td></td><td>13.7442,<br>100.4608</td><td>500</td><td>Supernap Thailand Company Limited</td><td>Supernap Thailand Company Limited</td><td></td><td></td></tr><tr class="geoip-results"><td>103.116.125.2</td><td>SG</td><td>Singapore,<br>Asia</td><td>103.116.124.0/22</td><td></td><td>1.3673,<br>103.8014</td><td>50</td><td>PT.Mora Telematika Indonesia</td><td>PT.Mora Telematika Indonesia</td><td></td><td></td></tr><tr class="geoip-results"><td>103.121.34.150</td><td>NZ</td><td>Invercargill,<br>Southland,<br>New Zealand,<br>Oceania</td><td>103.121.34.0/24</td><td>9810</td><td>-46.3888,<br>168.3779</td><td>5</td><td>Prodigi Technology Services Limited</td><td>Prodigi Technology Services Limited</td><td>netbydesign.nz</td><td></td></tr><tr class="geoip-results"><td>103.122.190.141</td><td>TW</td><td>Taiwan,<br>Asia</td><td>103.122.190.0/24</td><td></td><td>24,<br>121</td><td>200</td><td>Hong Da Storage Equipment Co.</td><td>Hong Da Storage Equipment Co.</td><td>as131657.net</td><td></td></tr><tr class="geoip-results"><td>103.126.52.180</td><td>AU</td><td>Sydney,<br>New South Wales,<br>Australia,<br>Oceania</td><td>103.126.52.0/24</td><td>2000</td><td>-33.8715,<br>151.2006</td><td>20</td><td>DataMossa</td><td>DataMossa</td><td></td><td></td></tr><tr class="geoip-results"><td>103.136.36.18</td><td>IN</td><td>India,<br>Asia</td><td>103.136.36.0/22</td><td></td><td>21.9974,<br>79.0011</td><td>1000</td><td>Peer Networks Private Limited</td><td>Peer Networks Private Limited</td><td></td><td></td></tr><tr class="geoip-results"><td>103.143.136.43</td><td>JP</td><td>Japan,<br>Asia</td><td>103.143.136.0/23</td><td></td><td>35.6897,<br>139.6895</td><td>500</td><td>Kobayashi Family Net LLP</td><td>Kobayashi Family Net LLP</td><td>kobayashi.ad.jp</td><td></td></tr><tr class="geoip-results"><td>103.144.177.30</td><td>CA</td><td>Canada,<br>North America</td><td>103.144.177.0/24</td><td></td><td>43.6319,<br>-79.3716</td><td>1000</td><td>Free Range Cloud</td><td>Free Range Cloud</td><td></td><td></td></tr><tr class="geoip-results"><td>103.148.239.134</td><td>SG</td><td>Singapore,<br>Asia</td><td>103.148.239.0/24</td><td></td><td>1.3673,<br>103.8014</td><td>50</td><td>Alpha Networks Solution</td><td>Alpha Networks Solution</td><td></td><td></td></tr><tr style="display:none;"><td></td></tr><tr class="geoip-results"><td>103.151.64.31</td><td>AU</td><td>Australia,<br>Oceania</td><td>103.151.64.0/24</td><td></td><td>-33.494,<br>143.2104</td><td>1000</td><td>OneQode Gaming Carrier</td><td>OneQode Gaming Carrier</td><td>as140627.net</td><td></td></tr><tr class="geoip-results"><td>103.156.251.7</td><td>SG</td><td>Singapore,<br>Asia</td><td>103.156.250.0/23</td><td></td><td>1.3673,<br>103.8014</td><td>50</td><td>PrimeXM Networks Singapore PTE.</td><td>PrimeXM Networks Singapore PTE.</td><td></td><td></td></tr><tr class="geoip-results"><td>103.157.198.10</td><td>MY</td><td>Malaysia,<br>Asia</td><td>103.157.198.0/23</td><td></td><td>2.5,<br>112.5</td><td>1000</td><td>Madison Technologies Malaysia Plt</td><td>Madison Technologies Malaysia Plt</td><td></td><td></td></tr><tr class="geoip-results"><td>103.160.63.222</td><td>ID</td><td>Indonesia,<br>Asia</td><td>103.160.62.0/23</td><td></td><td>-6.1728,<br>106.8272</td><td>1000</td><td>Herza.ID</td><td>Herza.ID</td><td>herza.id</td><td></td></tr><tr class="geoip-results"><td>103.170.232.152</td><td>JP</td><td>Tokyo,<br>Tokyo,<br>Japan,<br>Asia</td><td>103.170.232.0/23</td><td>151-0053</td><td>35.6893,<br>139.6899</td><td>20</td><td>Misaka Network</td><td>Misaka Network</td><td></td><td></td></tr><tr class="geoip-results"><td>103.196.37.98</td><td>US</td><td>Fremont,<br>California,<br>United States,<br>North America</td><td>103.196.37.96/29</td><td>94536</td><td>37.5625,<br>-122.0004</td><td>20</td><td>Mach Dilemma, LLC</td><td>Mach Dilemma, LLC</td><td></td><td>807</td></tr><tr class="geoip-results"><td>103.2.186.195</td><td>NC</td><td>Noumea,<br>South Province,<br>New Caledonia,<br>Oceania</td><td>103.2.184.0/22</td><td>98800</td><td>-22.2665,<br>166.4742</td><td>5</td><td>Nautile</td><td>Nautile</td><td></td><td></td></tr><tr class="geoip-results"><td>103.202.216.76</td><td>JP</td><td>Japan,<br>Asia</td><td>103.202.216.72/29</td><td></td><td>35.6897,<br>139.6895</td><td>500</td><td>Home NOC Operators Group</td><td>Home NOC Operators Group</td><td></td><td></td></tr><tr class="geoip-results"><td>103.23.232.7</td><td>ID</td><td>Banjarmasin,<br>South Kalimantan,<br>Indonesia,<br>Asia</td><td>103.23.232.0/24</td><td></td><td>-3.3219,<br>114.5871</td><td>20</td><td>Universitas Lambung Mangkurat</td><td>Universitas Lambung Mangkurat</td><td></td><td></td></tr><tr class="geoip-results"><td>103.242.68.78</td><td>NZ</td><td>Auckland,<br>Auckland,<br>New Zealand,<br>Oceania</td><td>103.242.68.64/26</td><td>1010</td><td>-36.8506,<br>174.7679</td><td>200</td><td>Telesmart Limited</td><td>Telesmart Limited</td><td>telesmart.co.nz</td><td></td></tr></tbody>'
    parsed_html = BeautifulSoup(html)
    rows = parsed_html.find_all("tr", attrs={'class': 'geoip-results'})
    mm_geo_file = "resources/replicability/maxmind_geo_anchors.json"
    if os.path.exists(mm_geo_file):
        mm_geo = load_json(mm_geo_file)
    else:
        mm_geo = {}
    for row in rows:
        elements = row.find_all("td")
        for i, element in enumerate(elements):
            elements[i] = element.text
        ip, country_code, location, network, postal_code, coordinates, radius, isp, organization, domain, metro_code = elements

        mm_geo[ip] = (
            country_code, location, network, postal_code, coordinates, radius, isp, organization, domain, metro_code)


def maxmind_free():

    tree = load_radix_tree()
    maxmind_geo = {}
    anchors = load_json(ANCHORS_FILE)
    for i, anchor in enumerate(sorted(anchors, key=lambda x: x["address_v4"])):
        ip = anchor["address_v4"]
        node = tree.search_best(ip)
        if node is not None:
            if "city" in node.data:
                maxmind_geo[ip] = node.data["coordinates"]

    return maxmind_geo


def ip_info():
    anchors = load_json(ANCHORS_FILE)
    token = "4f6c895ec9224f"
    if os.path.exists(ip_info_geo_file):
        ip_info_geo = load_json(ip_info_geo_file)
    else:
        ip_info_geo = {}

    for i, anchor in enumerate(sorted(anchors, key=lambda x: x["address_v4"])):
        ip = anchor["address_v4"]
        if ip in ip_info_geo:
            continue
        logging.info(ip)
        url = f"https://ipinfo.io/{ip}?token={token}"
        result = requests.get(url).json()
        ip_info_geo[ip] = result

    # dump_json(ip_info_geo, ip_info_geo_file)
    return ip_info_geo


def plot_results():

    removed_probes = load_json(REMOVED_PROBES_FILE)
    anchors = load_json(ANCHORS_FILE)
    ip_info_geo = ip_info()
    mm_geo = maxmind_free()

    errors_threshold_probes_to_anchors = load_json(
        probes_to_anchors_results_file)
    error_threshold_cdfs_p_to_a, circles_threshold_cdfs_p_to_a, _ = compute_error_threshold_cdfs(
        errors_threshold_probes_to_anchors)

    maxmind_error = {}
    ip_info_error = {}
    for i, anchor in enumerate(sorted(anchors, key=lambda x: x["address_v4"])):
        ip = anchor["address_v4"]
        if ip in removed_probes:
            continue

        if "geometry" not in anchor:
            continue
        long, lat = anchor["geometry"]["coordinates"]
        if ip in mm_geo:
            error = haversine(mm_geo[ip], (lat, long))
            maxmind_error[ip] = error

        if ip in ip_info_geo:
            ipinfo_lat, ipinfo_long = ip_info_geo[ip]["loc"].split(",")
            ipinfo_lat, ipinfo_long = float(ipinfo_lat), float(ipinfo_long)
            error = haversine((ipinfo_lat, ipinfo_long), (lat, long))
            ip_info_error[ip] = error

    Ys = [error_threshold_cdfs_p_to_a[0], list(
        maxmind_error.values()), list(ip_info_error.values())]
    print([len(Y) for Y in Ys])
    labels = ["All VPs", "Maxmind (Free)", "IPinfo"]
    fig, ax = plot_multiple_cdf(Ys, 10000, 1, 10000,
                                "Geolocation error (km)",
                                "CDF of targets",
                                xscale="log",
                                yscale="linear",
                                legend=labels)
    homogenize_legend(ax, "lower right")
    ofile = f"resources/replicability/geo_databases.pdf"
    plot_save(ofile, is_tight_layout=True)


if __name__ == "__main__":
    # ip_info()
    # maxmind_free()
    plot_results()
