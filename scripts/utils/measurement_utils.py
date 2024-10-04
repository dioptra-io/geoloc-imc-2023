"""functions for running measurements"""

import random
import time

from datetime import datetime
from uuid import UUID
from pathlib import Path
from dateutil import parser

from logger import logger
from scripts.utils.file_utils import load_json, dump_json
from scripts.ripe_atlas.atlas_api import get_prefix_from_ip, get_measurements_from_tag
from scripts.ripe_atlas.ping_and_traceroute_classes import PING
from scripts.utils.clickhouse import Clickhouse

from default import (
    PREFIX_MEASUREMENT_RESULTS,
    TARGET_MEASUREMENT_RESULTS,
    USER_VPS_TO_PREFIX_TABLE,
    USER_VPS_TO_TARGET_TABLE,
)


def load_targets(target_file_path: Path, nb_target: int = -1) -> list:
    """get a file as entry, return a list of ip target"""
    targets = load_json(target_file_path)

    if nb_target > len(targets) or nb_target < 0:
        nb_target = len(targets)

    subset_targets = random.sample(targets, k=nb_target)

    return subset_targets


def load_vps(vps_file_path: Path, nb_vps: int = -1) -> list:
    """load vps from file, return list of vps"""
    vps = load_json(vps_file_path)

    if nb_vps > len(vps) or nb_vps < 0:
        nb_vps = len(vps)

    subset_vps = random.sample(vps, k=nb_vps)

    return subset_vps


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
            "end_time": None,
        },
        "prefix_measurements": {
            "measurement_uuid": str(prefix_measurement_uuid),
            "targets": target_prefixes,
            "vps": vps,
            "end_time": None,
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

    dump_json(measurement_config, out_path)


def get_target_prefixes(targets: list) -> list:
    """from a set of targets ip addresses return their /24 prefixes"""
    return [get_prefix_from_ip(target_addr) for target_addr in targets]


def ping_prefixes(
    measurement_uuid: UUID,
    measurement_config: dict,
    target_prefixes: list,
    targets_per_prefix: dict[list],
    vps: list[dict],
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

            if cached_results:
                logger.info(
                    f"initial length targets: {len(targets_per_prefix)}, cached measurements : {len(cached_results)}"
                )

                # get prefixes out of targets
                cached_results = [
                    get_prefix_from_ip(target["dst_addr"]) for target in cached_results
                ]
                for subnet in cached_results:
                    if subnet not in targets_per_prefix:
                        continue
                    targets_per_prefix.pop(subnet)

                logger.info(
                    f"after removing cached: {len(targets_per_prefix)}, cached measurements : {len(cached_results)}"
                )
    except FileNotFoundError:
        logger.info("No cached results available")
        pass

    logger.info(
        f"Starting measurements {str(measurement_uuid)} with parameters: dry_run={dry_run}; nb_targets={len(target_prefixes)}; nb_vps={len(vps)}."
    )

    # measurement for 3 targets in every target prefixes
    ids, start_time, end_time = pinger.ping_by_prefix(
        target_prefixes=target_prefixes,
        vps=vps,
        targets_per_prefix=targets_per_prefix,
        tag=measurement_uuid,
        dry_run=dry_run,
    )

    # overwrite ids
    if "ids" in measurement_config["prefix_measurements"]:
        ids.extend(measurement_config["prefix_measurements"]["ids"])

    measurement_config["prefix_measurements"]["start_time"] = start_time
    measurement_config["prefix_measurements"]["end_time"] = end_time


def ping_targets(
    measurement_uuid: UUID,
    measurement_config: dict,
    targets: list[dict],
    vps: list[dict],
    dry_run: bool = False,
    use_cache: bool = True,
    cache_file: Path = TARGET_MEASUREMENT_RESULTS,
) -> None:
    """ping all targets using all vps"""

    pinger = PING()

    targets = [t["address_v4"] for t in targets]

    try:
        if use_cache:
            cached_results = load_json(cache_file)
            logger.info(
                f"initial length targets: {len(targets)}, cached measurements : {len(cached_results)}"
            )

            cached_results = [c["dst_addr"] for c in cached_results]

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

    ids, start_time, end_time = pinger.ping_by_target(
        targets=targets, vps=vps, tag=measurement_uuid, dry_run=dry_run
    )

    # overwrite ids
    if "ids" in measurement_config["target_measurements"]:
        ids.extend(measurement_config["target_measurements"]["ids"])

    measurement_config["target_measurements"]["start_time"] = start_time
    measurement_config["target_measurements"]["end_time"] = end_time


def get_latest_measurements(config_path: Path) -> dict:
    """retrieve latest measurement config"""
    try:
        assert config_path.is_dir()
    except AssertionError:
        logger.error(f"config path is not a dir: {config_path}")

    latest: datetime = None
    for file in config_path.iterdir():
        measurement_config = load_json(file)
        if latest:
            if latest < parser.isoparse(measurement_config["start_time"]):
                latest_config = measurement_config
        else:
            latest = parser.isoparse(measurement_config["start_time"])
            latest_config = measurement_config

    return latest_config


def retrieve_results(
    measurement_uuid: str,
    out_file: Path,
) -> None:
    """query RIPE Atlas API to retrieve all measurement results"""
    # fetch results on API
    measurement_results = get_measurements_from_tag(measurement_uuid)

    logger.info(
        f"nb measurements retrieved: {len(measurement_results)} for measurement_uuid : {measurement_uuid}"
    )

    # save results in cache file
    dump_json(measurement_results, out_file)

    return measurement_results


def insert_prefix_results(results: list) -> None:
    """insert prefixes results with CSV value method"""
    rows = []
    values_description = (
        "src, dst, prb_id, date, sent, rcvd, rtts, min, mean, msm_id, proto"
    )

    if not results:
        raise RuntimeError(f"no data to insert, data = {result}")

    for result in results:
        try:
            # parse response
            src = result["src_addr"]
            dst = result["dst_addr"]
            prb_id = result["prb_id"]
            date = result["timestamp"]
            sent = result["sent"]
            rcvd = result["rcvd"]
            rtts = (
                [rtt["rtt"] for rtt in result["result"]]
                if "rtt" in result["result"]
                else [-1]
            )
            min = result["min"]
            mean = result["avg"]
            msm_id = result["msm_id"]
            proto = 0

            row = [src, dst, prb_id, date, sent, rcvd, rtts, min, mean, msm_id, proto]

            rows.append(row)
        except KeyError as e:
            logger.warning(f"Some measurements does not contain results: {e}")

    clickhouse = Clickhouse()
    query = clickhouse.insert_from_values_query(
        USER_VPS_TO_PREFIX_TABLE, values_description
    )
    clickhouse.insert_from_values(query, rows)

    logger.info(
        f"Prefix measurements successfully inserted in table : {USER_VPS_TO_PREFIX_TABLE}"
    )


def insert_target_results(results: list) -> None:
    """insert prefixes results with CSV value method"""
    rows = []
    values_description = (
        "src, dst, prb_id, date, sent, rcvd, rtts, min, mean, msm_id, proto"
    )
    for result in results:
        # parse response
        src = result["src_addr"]
        dst = result["dst_addr"]
        prb_id = result["prb_id"]
        date = result["timestamp"]
        sent = result["sent"]
        rcvd = result["rcvd"]
        rtts = (
            [rtt["rtt"] for rtt in result["result"]]
            if "rtt" in result["result"]
            else [-1]
        )
        min = result["min"]
        mean = result["avg"]
        msm_id = result["msm_id"]
        proto = 0

        row = [src, dst, prb_id, date, sent, rcvd, rtts, min, mean, msm_id, proto]

        rows.append(row)

    clickhouse = Clickhouse()
    query = clickhouse.insert_from_values_query(
        USER_VPS_TO_TARGET_TABLE, values_description
    )
    clickhouse.insert_from_values(query, rows)

    logger.info(
        f"Target measurements successfully inserted in table : {USER_VPS_TO_TARGET_TABLE}"
    )
