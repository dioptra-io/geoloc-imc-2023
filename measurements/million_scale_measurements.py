"""perform a meshed ping measurement where each VP is probed by every others"""

from logger import logger

from scripts.utils.file_utils import load_json
from scripts.utils.measurement_utils import (
    load_targets,
    load_vps,
    get_measurement_config,
    save_measurement_config,
    get_target_prefixes,
    ping_prefixes,
    ping_targets,
    retrieve_results,
    insert_prefix_results,
    insert_target_results,
)
from default import (
    USER_ANCHORS_FILE,
    USER_HITLIST_FILE,
    PREFIX_MEASUREMENT_RESULTS,
    TARGET_MEASUREMENT_RESULTS,
    MEASUREMENT_CONFIG_PATH,
)

# Small number of targets and VPs for testing
# Change to real Anchors and VPs values for complete measurement
NB_TARGETS = 5
NB_VPS = 10

# measurement configuration for retrieval,
# replace if you want to create new batch of measurements
EXPERIMENT_UUID = "3992e46c-73cf-4a7b-9428-3198856039a9"
TARGET_MESAUREMENT_UUID = "03eb9559-88fe-41cb-b62c-4c07d1d5acb8"
PREFIX_MESAUREMENT_UUID = "a09709aa-be76-4687-852e-64e8090bee70"
CONFIG_PATH = MEASUREMENT_CONFIG_PATH / f"{EXPERIMENT_UUID}.json"


def main_measurements() -> None:
    """perform all measurements related with million scale"""
    # set any of these var to execute the corresponding fct
    do_target_pings = True
    do_target_prefix_pings = True

    # load targets and VPs
    targets = load_targets(USER_ANCHORS_FILE, nb_target=NB_TARGETS)
    vps = load_vps(USER_ANCHORS_FILE, nb_vps=NB_VPS)

    # every anchors /24 subnet
    target_addrs = [t["address_v4"] for t in targets]
    target_prefixes = get_target_prefixes(target_addrs)
    # responsive IP addresses in all /24 prefixes
    targets_per_prefix = load_json(USER_HITLIST_FILE)

    logger.info(f"Starting experiment with uuid :: {EXPERIMENT_UUID}")
    logger.info(f"Config output                 :: {CONFIG_PATH}")

    # check if measurements measurement under this config uuid already exists
    if CONFIG_PATH.exists():
        logger.info(f"Loading existing measurement config:: {EXPERIMENT_UUID}")
        measurement_config = load_json(CONFIG_PATH)
    else:
        # create a new config is no existing one
        measurement_config = get_measurement_config(
            targets=targets,
            vps=vps,
            target_prefixes=target_prefixes,
            experiment_uuid=EXPERIMENT_UUID,
            target_measurement_uuid=TARGET_MESAUREMENT_UUID,
            prefix_measurement_uuid=PREFIX_MESAUREMENT_UUID,
        )
        save_measurement_config(measurement_config, CONFIG_PATH)

    if do_target_pings:
        vps.extend(targets)

        logger.info(f"Starting targets pigns :: {TARGET_MESAUREMENT_UUID}")
        logger.info(f"Nb targets             :: {len(targets)}")
        logger.info(f"Nb vps                 :: {len(vps)}")

        # measurement configuration for retrieval
        ping_targets(
            measurement_uuid=TARGET_MESAUREMENT_UUID,
            measurement_config=measurement_config,
            targets=targets,
            vps=vps,
            use_cache=True,
        )

        # update config
        save_measurement_config(measurement_config, CONFIG_PATH)

    if do_target_prefix_pings:
        logger.info(f"Starting prefix pigns :: {PREFIX_MESAUREMENT_UUID}")
        logger.info(f"Nb targets             :: {len(targets)}")
        logger.info(f"Nb prefixes            :: {len(target_prefixes)}")
        logger.info(f"Nb vps                 :: {len(vps)}")

        ping_prefixes(
            vps=vps,
            target_prefixes=target_prefixes,
            targets_per_prefix=targets_per_prefix,
            measurement_uuid=PREFIX_MESAUREMENT_UUID,
            measurement_config=measurement_config,
        )


def main_retrieve_results() -> None:
    """retrieve all measurement results related with million scale"""
    retrieve_target_measurements = True
    retrieve_prefix_measurements = True

    measurement_config = load_json(CONFIG_PATH)
    logger.info(f"{measurement_config}")

    if retrieve_target_measurements:
        target_measurement_uuid = measurement_config["target_measurements"][
            "measurement_uuid"
        ]

        logger.info(
            f"retrieving results for measurement ids: {target_measurement_uuid}"
        )

        # sometimes, not all probes give output, reduce timeout if you do not want to wait for too long
        response = retrieve_results(TARGET_MESAUREMENT_UUID, TARGET_MEASUREMENT_RESULTS)

        # will output into user tables
        insert_target_results(response)

    if retrieve_prefix_measurements:
        prefix_measurement_uuid = measurement_config["prefix_measurements"][
            "measurement_uuid"
        ]

        logger.info(
            f"retrieving results for measurement ids: {prefix_measurement_uuid}"
        )

        # sometimes, not all probes give output, reduce timeout if you do not want to wait for too long
        response = retrieve_results(TARGET_MESAUREMENT_UUID, PREFIX_MEASUREMENT_RESULTS)

        # will output into user tables
        insert_prefix_results(response)


if __name__ == "__main__":
    do_measurements = True
    do_retrieve_results = True

    if do_measurements:
        main_measurements()

    if do_retrieve_results:
        main_retrieve_results()
