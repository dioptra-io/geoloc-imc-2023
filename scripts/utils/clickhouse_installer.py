"""clickhouse client"""

from scripts.utils.clickhouse import Clickhouse
from logger import logger

from default import *


if __name__ == "__main__":
    clickhouse_driver = Clickhouse()

    ##################################################################################################
    # CREATE REPRO TABLES                                                                            #
    ##################################################################################################

    # create anchors_meshed_table
    query = clickhouse_driver.create_target_ping_tables(ANCHORS_MESHED_PING_TABLE)
    clickhouse_driver.execute(query)
    logger.info(f"table {ANCHORS_MESHED_PING_TABLE} created")

    query = clickhouse_driver.create_target_ping_tables(PROBES_TO_ANCHORS_PING_TABLE)
    clickhouse_driver.execute(query)
    logger.info(f"table {PROBES_TO_ANCHORS_PING_TABLE} created")

    # create prefixes ping table
    query = clickhouse_driver.create_prefixes_ping_tables(ANCHORS_TO_PREFIX_TABLE)
    clickhouse_driver.execute(query)
    logger.info(f"table {ANCHORS_TO_PREFIX_TABLE} created")

    query = clickhouse_driver.create_prefixes_ping_tables(PROBES_TO_PREFIX_TABLE)
    clickhouse_driver.execute(query)
    logger.info(f"table {PROBES_TO_PREFIX_TABLE} created")

    query = clickhouse_driver.create_prefixes_ping_tables(
        TARGET_TO_LANDMARKS_PING_TABLE
    )
    clickhouse_driver.execute(query)
    logger.info(f"table {TARGET_TO_LANDMARKS_PING_TABLE} created")

    # create traceroute table
    query = clickhouse_driver.create_traceroutes_table(ANCHORS_MESHED_TRACEROUTE_TABLE)
    clickhouse_driver.execute(query)
    logger.info(f"table {ANCHORS_MESHED_TRACEROUTE_TABLE} created")

    # Create street level db
    query = clickhouse_driver.create_street_level_table(STREET_LEVEL_TRACEROUTES_TABLE)
    clickhouse_driver.execute(query)
    logger.info(f"table {STREET_LEVEL_TRACEROUTES_TABLE} created")

    ##################################################################################################
    # INSERT REPRO DATA                                                                              #
    ##################################################################################################

    # table names
    tables = [
        ANCHORS_MESHED_TRACEROUTE_TABLE,
        PROBES_TO_ANCHORS_PING_TABLE,
        ANCHORS_TO_PREFIX_TABLE,
        PROBES_TO_PREFIX_TABLE,
        ANCHORS_MESHED_PING_TABLE,
        TARGET_TO_LANDMARKS_PING_TABLE,
        STREET_LEVEL_TRACEROUTES_TABLE,
    ]

    # measurements files_path
    file_paths = [
        ANCHORS_MESHED_TRACEROUTE_FILE,
        PROBES_TO_ANCHORS_PING_FILE,
        ANCHORS_TO_PREFIX_FILE,
        PROBES_TO_PREFIX_FILE,
        ANCHORS_MESHED_PING_FILE,
        TARGET_TO_LANDMARKS_PING_FILE,
        STREET_LEVEL_TRACEROUTES_FILE,
    ]

    for table_name, file_path in zip(tables, file_paths):
        logger.info(f"inserting data into {table_name} from {file_path}")
        insert_query = clickhouse_driver.insert_native_query(table_name, file_path)

        clickhouse_driver.insert_file(insert_query)

    ##################################################################################################
    # CREATE USER MEASUREMENT TABLES                                                                 #
    ##################################################################################################

    query = clickhouse_driver.create_target_ping_tables(USER_VPS_TO_TARGET_TABLE)
    clickhouse_driver.execute(query)
    logger.info(f"table {USER_VPS_TO_TARGET_TABLE} created")

    query = clickhouse_driver.create_target_ping_tables(USER_MESHED_TABLE)
    clickhouse_driver.execute(query)
    logger.info(f"table {USER_MESHED_TABLE} created")

    # create prefixes ping table
    query = clickhouse_driver.create_prefixes_ping_tables(USER_VPS_TO_PREFIX_TABLE)
    clickhouse_driver.execute(query)
    logger.info(f"table {USER_VPS_TO_PREFIX_TABLE} created")

    query = clickhouse_driver.create_prefixes_ping_tables(
        USER_TARGET_TO_LANDMARKS_PING_TABLE
    )
    clickhouse_driver.execute(query)
    logger.info(f"table {USER_TARGET_TO_LANDMARKS_PING_TABLE} created")

    # create traceroute table
    query = clickhouse_driver.create_traceroutes_table(
        USER_ANCHORS_MESHED_TRACEROUTE_TABLE
    )
    clickhouse_driver.execute(query)
    logger.info(f"table {USER_ANCHORS_MESHED_TRACEROUTE_TABLE} created")

    # Create street level db
    query = clickhouse_driver.create_street_level_table(
        USER_STREET_LEVEL_TRACEROUTES_TABLE
    )
    clickhouse_driver.execute(query)
    logger.info(f"table {USER_STREET_LEVEL_TRACEROUTES_TABLE} created")
