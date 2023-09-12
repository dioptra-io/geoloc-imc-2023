"""functions for running measurements"""
import random

from uuid import UUID
from pathlib import Path

from logger import logger
from scripts.utils.file_utils import load_json, dump_json
from scripts.ripe_atlas.atlas_api import get_prefix_from_ip, get_measurements_from_tag
from scripts.ripe_atlas.ping_and_traceroute_classes import PING

from default import (
    MEASUREMENT_CONFIG_PATH,
    PREFIX_MEASUREMENT_RESULTS,
    TARGET_MEASUREMENT_RESULTS,
)


def load_targets(target_file_path: Path, nb_target: int) -> list:
    """get a file as entry, return a list of ip target"""
    targets = load_json(target_file_path)

    if nb_target > len(targets) or nb_target < 0:
        nb_target = len(targets)

    subset_targets = random.sample(targets, k=nb_target)

    measurement_targets = [target["address_v4"] for target in subset_targets]

    return measurement_targets


def load_vps(vps_file_path: Path, nb_vps: int) -> dict:
    """load vps from file, return list of vps"""
    vps = load_json(vps_file_path)

    if nb_vps > len(vps) or nb_vps < 0:
        nb_vps = len(vps)

    subset_vps = random.sample(vps, k=nb_vps)

    measurement_vps = {}
    for vp in subset_vps:
        measurement_vps[vp["address_v4"]] = vp

    return measurement_vps


def get_measurement_config(
    measurement_uuid: UUID, targets: list, vps: dict, dry_run=False
) -> dict:
    """return measurement config for future retrieval"""
    return {
        "UUID": str(measurement_uuid),
        "is_dry_run": dry_run,
        "description": "measurement towards all anchors with all anchors as vps",
        "type": "prefix",
        "af": 4,
        "targets": targets,
        "vps": vps,
    }


def save_measurement_config(measurement_config: dict) -> None:
    """save measurement config"""

    config_file = MEASUREMENT_CONFIG_PATH / f"{measurement_config['UUID']}.json"
    dump_json(measurement_config, config_file)


def get_target_prefixes(targets: list) -> list:
    """from a set of targets ip addresses return their /24 prefixes"""
    return [get_prefix_from_ip(target_addr) for target_addr in targets]


def ping_prefixes(
    measurement_uuid: UUID,
    measurement_config: dict,
    target_prefixes: list,
    targets_per_prefix: list,
    vps: dict,
    dry_run: bool = False,
    use_cache: bool = True,
    cache_file: Path = PREFIX_MEASUREMENT_RESULTS,
) -> None:
    """ping all targets prefixes from all vps"""

    pinger = PING()

    try:
        # load cached prefix results in case measurement was interrupted
        if use_cache:
            cached_results = load_json(cache_file)
            logger.info(
                f"initial length targets: {len(targets_per_prefix)}, cached measurements : {len(cached_results)}"
            )

            # get prefixes out of targets
            cached_results = [
                get_prefix_from_ip(target_addr) for target_addr in cached_results
            ]
            targets_per_prefix = list(
                set(targets_per_prefix).difference(set(cached_results))
            )

            logger.info(
                f"after removing cached: {len(targets_per_prefix)}, cached measurements : {len(cached_results)}"
            )
    except FileNotFoundError:
        logger.info("No cached results available")
        pass

    logger.info(
        f"Starting measurements {str(measurement_uuid)} with parameters: dry_run={dry_run}; nb_targets={len(targets_per_prefix)}; nb_vps={len(vps)}."
    )

    # measurement for 3 targets in every target prefixes
    (
        measurement_config["ids"],
        measurement_config["start_time"],
        measurement_config["end_time"],
    ) = pinger.ping_by_prefix(
        target_prefixes=target_prefixes,
        vps=vps,
        targets_per_prefix=targets_per_prefix,
        tag=measurement_uuid,
        dry_run=dry_run,
    )

    save_measurement_config(measurement_config)


def ping_targets(
    measurement_uuid: UUID,
    measurement_config: dict,
    targets: list,
    vps: dict,
    dry_run: bool = False,
    use_cache: bool = True,
    cache_file: Path = TARGET_MEASUREMENT_RESULTS,
) -> None:
    """ping all targets using all vps"""

    pinger = PING()

    try:
        if use_cache:
            cached_results = load_json(cache_file)
            logger.info(
                f"initial length targets: {len(targets)}, cached measurements : {len(cached_results)}"
            )

            targets = list(set(targets).difference(set(cached_results)))

            logger.info(
                f"after removing cached: {len(targets)}, cached measurements : {len(cached_results)}"
            )
    except FileNotFoundError:
        logger.info("No cached results available")
        pass

    logger.info(
        f"Starting measurements {str(measurement_uuid)} with parameters: dry_run={dry_run}; nb_targets={len(targets)}; nb_vps={len(vps)}."
    )

    (
        measurement_config["ids"],
        measurement_config["start_time"],
        measurement_config["end_time"],
    ) = pinger.ping_by_target(
        targets=targets, vps=vps, tag=measurement_uuid, dry_run=dry_run
    )

    save_measurement_config(measurement_config)


def retrieve_results(measurement_config: dict, out_file: Path) -> None:
    """query RIPE Atlas API to retrieve all measurement results"""

    measurement_results = get_measurements_from_tag(str(measurement_config["UUID"]))

    # test that everything is alright
    logger.info(f"nb measurements retrieved: {len(measurement_results)}")

    for i, (target_addr, results) in enumerate(measurement_results.items()):
        if i > 10:
            break
        logger.info(
            f"target: {target_addr} | number of measurement retrieved: {len(results)}"
        )

    # save results
    dump_json(measurement_results, out_file)
