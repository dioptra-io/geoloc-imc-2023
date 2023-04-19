import csv
import logging
import pickle
from datetime import datetime
from pathlib import Path
from uuid import UUID

import requests

from geoloc_imc_2023.iris_probing import IrisProber, PingResults

logger = logging.getLogger()


def get_from_atlas(url):
    """request atlas api"""
    response = requests.get(url).json()
    while True:
        for anchor in response["results"]:
            yield anchor

        if response["next"]:
            response = requests.get(response["next"]).json()
        else:
            break


def get_atlas_probes(probe_url="https://atlas.ripe.net/api/v2/probes/") -> dict:
    """get all atlas probes with API"""

    anchors = {}
    for index, anchor in enumerate(get_from_atlas(probe_url)):
        # filter probes based on generic criteria
        if (
            anchor["status"]["name"] != "Connected"
            or anchor.get("geometry") is None
            or anchor.get("address_v4") is None
            or anchor.get("country_code") is None
        ):
            continue

        anchors[anchor["address_v4"]] = {
            "id": anchor["id"],
            "is_anchor": anchor["is_anchor"],
            "country_code": anchor["country_code"],
            "latitude": anchor["geometry"]["coordinates"][1],
            "longitude": anchor["geometry"]["coordinates"][0],
        }

    logger.info(f"Number of Atlas probes kept: {len(anchors)}/{index}")

    return anchors


def generate_iris_probing_file(
    raw_atlas_probe_file: Path = Path(".") / "../datasets/raw_probe_atlas.pickle",
    output_file: Path = Path(".") / "../datasets/iris_ping_probing.csv",
) -> None:
    """generate probing files for IRIS ping"""

    # get probes dataset
    with open(raw_atlas_probe_file, "rb") as f:
        probes_atlas = pickle.load(f)

    # generate probing file
    with open(output_file, "w") as f:
        csv_writer = csv.writer(f)
        for probe in probes_atlas:
            row = [str(probe) + "/32", "icmp", 2, 50, 1]
            csv_writer.writerow(row)


def iris_probing(
    probing_rate: int = 5_000,
    agent_uuid: str = "ddd8541d-b4f5-42ce-b163-e3e9bfcd0a47",
    probe_file: Path = Path(".") / "../datasets/iris_ping_probing.csv",
) -> str:
    """perform IRIS ping probing toward every Atlas probes"""

    date = datetime.today().strftime("%Y-%m-%d-%H-%M-%S")
    tags = [f"atlas-ping-{date}-{probing_rate}"]
    agent_uuids = {
        UUID(agent_uuid): probing_rate,
    }
    iris_prober = IrisProber(
        tags=tags,
        tool="ping",
        input_file_path=probe_file,
        probing_rates=agent_uuids,
        idle_time=180,
    )

    logger.info("starting measurements")
    measurement_uuid = iris_prober.probe()
    iris_prober.wait_until_complete(measurement_uuid)

    logger.info(measurement_uuid)


def validate_atlas_probing(
    responsive_probe_atlas_file=Path(".") / "../datasets/responsive_probe_atlas.pickle",
    raw_atlas_probe_file=Path(".") / "../datasets/raw_probe_atlas.pickle",
    agent_uuid: str = "ddd8541d-b4f5-42ce-b163-e3e9bfcd0a47",
) -> None:
    generate_iris_probing_file()

    measurement_uuid = iris_probing(agent_uuid=agent_uuid)

    ping_results = PingResults(measurement_uuid).query(agent_uuid)

    with open(raw_atlas_probe_file, "rb") as f:
        raw_atlas_probe = pickle.load(f)

    responsive_probes = {}
    unresponsive_ip = 0
    for row in ping_results:
        probe_dst = row["probe_dst_addr"].split(":")[-1]
        rtt = row["rtt"]

        try:
            probe_description = raw_atlas_probe[probe_dst]
        except KeyError:
            unresponsive_ip += 1
            continue

        responsive_probes[probe_dst] = probe_description

    logger.info(
        f"Number of Atlas probes kept: {len(responsive_probes)}, rejected : {len(raw_atlas_probe)-len(responsive_probes) }"
    )

    # save results
    with open(responsive_probe_atlas_file, "wb") as f:
        pickle.dump(responsive_probes, f)
