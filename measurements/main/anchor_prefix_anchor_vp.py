"""measure atlas anchor prefixes from atlas anchors"""
import logging
import sys
import uuid
import argparse
import pickle

from geoloc_imc_2023.cbg import PING, get_prefix_from_ip
from geoloc_imc_2023.default import LOG_PATH, RIPE_CREDENTIALS, ANCHOR_PREFIX_ANCHOR_VP
from geoloc_imc_2023.measurement_utils import (
    load_atlas_anchors,
    load_prefix_hitlist,
    save_config_file,
)


if __name__ == "__main__":
    # parse cmd line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry_run",
        help="boolean, decide wether or not to start actual probing, set to True for testing",
        action="store_true",
    )
    parser.add_argument(
        "--use_cache",
        help="boolean, decide wether or not to start actual probing, set to True for testing",
        action="store_true",
    )
    parser.add_argument(
        "--nb_targets", help="define the number of targets to measure", type=int
    )
    parser.add_argument(
        "--nb_vps", help="define the number of atlas vantage points to use", type=int
    )
    args = parser.parse_args()

    if args.dry_run:
        dry_run = True
    else:
        dry_run = False

    if args.use_cache:
        use_cache = True
    else:
        use_cache = False

    nb_targets = args.nb_targets
    nb_vps = args.nb_vps

    # generate measurement UUID
    measurement_uuid = uuid.uuid4()

    # set logging utilities
    logging.basicConfig(
        filename=LOG_PATH / (str(measurement_uuid) + ".log"),
        filemode="a",
        format="%(asctime)s::%(name)s:%(levelname)s:%(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG,
    )

    logger = logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    logger = logging.getLogger()

    # load measurement datasets
    targets_per_prefix = load_prefix_hitlist()
    anchors = load_atlas_anchors()

    # select targets and vps from anchors
    targets = list(anchors.keys())[:nb_targets]
    vps = {}
    for i, anchor in enumerate(anchors):
        if len(vps) >= nb_vps:
            break
        vps[anchor] = anchors[anchor]

    # measurement configuration
    measurement_config = {
        "UUID": str(measurement_uuid),
        "is_dry_run": dry_run,
        "description": "measurement towards anchors with anchor as vps",
        "type": "prefix",
        "af": 4,
        "targets": targets,
        "vps": vps,
    }

    # save measurement configuration before starting measurement
    save_config_file(measurement_config)

    cbg = PINGRIPE_CREDENTIALS)

    logger.info(f"Starting measurements {measurement_uuid}")

    # get target prefixes
    target_prefixes = []
    for target_addr in targets:
        target_prefix = get_prefix_from_ip(target_addr)
        target_prefixes.append(target_prefix)

    try:
        with open(ANCHOR_PREFIX_ANCHOR_VP, "rb") as f:
            cached_results = pickle.load(f)

        logger.info(f"{len(set(target_prefixes))}")
        logger.info(
            f"initial length targets: {len(target_prefixes)}, cached measurements : {len(cached_results)}"
        )

        # get prefixes out of targets
        cached_results = [
            get_prefix_from_ip(target_addr) for target_addr in cached_results
        ]
        target_prefixes = list(
            set(target_prefixes).difference(set(cached_results)))

        logger.info(
            f"after removing cached: {len(target_prefixes)}, cached measurements : {len(cached_results)}"
        )
    except FileNotFoundError:
        logger.info("no cached results available")
        pass

    # measurement for 3 targets in every target prefixes
    (
        measurement_config["ids"],
        measurement_config["start_time"],
        measurement_config["end_time"],
    ) = cbg.ping_by_prefix(
        target_prefixes=target_prefixes,
        vps=vps,
        targets_per_prefix=targets_per_prefix,
        tag=measurement_uuid,
        dry_run=dry_run,
    )

    # save measurement configuration before starting measurement
    save_config_file(measurement_config)