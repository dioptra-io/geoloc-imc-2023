"""functions for running measurements"""
import random

from datetime import datetime
from uuid import UUID
from pathlib import Path

from logger import logger
from scripts.utils.file_utils import load_json, dump_json
from scripts.ripe_atlas.atlas_api import get_prefix_from_ip, get_measurements_from_tag
from scripts.ripe_atlas.ping_and_traceroute_classes import PING

from default import (
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
    experiment_uuid: UUID,
    prefix_measurement_uuid: UUID,
    target_measurement_uuid: UUID,
    targets: list,
    target_prefixes: list,
    vps: dict,
    dry_run=False,
) -> dict:
    """return measurement config for future retrieval"""
    return {
        "experiment_uuid": str(experiment_uuid),
        "status": "ongoing",
        "start_time": str(datetime.now()),
        "end_time": None,
        "is_dry_run": dry_run,
        "nb_targets": len(targets),
        "nb_vps": len(vps),
        "description": "measurements from a set of vps towards all targets/target prefixes",
        "af": 4,
        "target_measurements": {
            "measurement_uuid": str(target_measurement_uuid),
            "targets": targets,
            "vps": vps,
        },
        "prefix_measurements": {
            "measurement_uuid": str(prefix_measurement_uuid),
            "targets": target_prefixes,
            "vps": vps,
        },
    }


def save_measurement_config(measurement_config: dict, out_path: Path) -> None:
    """save measurement config"""

    try:
        if (
            measurement_config["prefix_measurements"]["end_time"] is not None
            and measurement_config["target_measurements"]["end_time"] is not None
        ):
            measurement_config["end_time"] = str(datetime.now())
            measurement_config["status"] = "finished"
    except KeyError:
        pass

    config_file = out_path / f"{measurement_config['experiment_uuid']}.json"
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
        measurement_config["prefix_measurements"]["ids"],
        measurement_config["prefix_measurements"]["start_time"],
        measurement_config["prefix_measurements"]["end_time"],
    ) = pinger.ping_by_prefix(
        target_prefixes=target_prefixes,
        vps=vps,
        targets_per_prefix=targets_per_prefix,
        tag=measurement_uuid,
        dry_run=dry_run,
    )


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
        measurement_config["target_measurements"]["ids"],
        measurement_config["target_measurements"]["start_time"],
        measurement_config["target_measurements"]["end_time"],
    ) = pinger.ping_by_target(
        targets=targets, vps=vps, tag=measurement_uuid, dry_run=dry_run
    )


def get_latest_measurements(config_path: Path) -> dict:
    """retrieve latest measurement config"""
    try:
        assert config_path.is_dir()
    except AssertionError:
        logger.error(f"config path is not a dir: {config_path}")

    latest: datetime = None
    for file in config_path.iterdir():
        logger.info()


def retrieve_results(measurement_config: dict, out_file: Path) -> None:
    """query RIPE Atlas API to retrieve all measurement results"""

    # TODO: make it a loop and save csv

    measurement_results = get_measurements_from_tag(str(measurement_config["UUID"]))

    logger.info(f"nb measurements retrieved: {len(measurement_results)}")

    for i, (target_addr, results) in enumerate(measurement_results.items()):
        if i > 10:
            break
        logger.info(
            f"target: {target_addr} | number of measurement retrieved: {len(results)}"
        )

    # save results
    dump_json(measurement_results, out_file)
