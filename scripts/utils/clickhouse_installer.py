"""clickhouse client"""
from scripts.utils.clickhouse import Clickhouse
from logger import logger

from default import (
    ANCHORS_MESHED_PING_TABLE,
    PROBES_TO_ANCHORS_PING_TABLE,
    ANCHORS_TO_PREFIX_TABLE,
    PROBES_TO_PREFIX_TABLE,
    ANCHORS_MESHED_TRACEROUTE_TABLE,
    TARGET_TO_LANDMARKS_PING_TABLE,
    PROBES_TO_ANCHORS_PING_FILE,
    ANCHORS_TO_PREFIX_FILE,
    PROBES_TO_PREFIX_FILE,
    TARGET_TO_LANDMARKS_PING_FILE,
    ANCHORS_MESHED_PING_FILE,
    ANCHORS_MESHED_TRACEROUTE_FILE,
)


if __name__ == "__main__":
    clickhouse_driver = Clickhouse()

    # create anchors_meshed_table
    query = clickhouse_driver.create_target_ping_tables(ANCHORS_MESHED_PING_TABLE)
    logger.info(f"create table with query: {query}")
    clickhouse_driver.execute(query)

    query = clickhouse_driver.create_target_ping_tables(PROBES_TO_ANCHORS_PING_TABLE)
    logger.info(f"create table with query: {query}")
    clickhouse_driver.execute(query)

    # create prefixes ping table
    query = clickhouse_driver.create_prefixes_ping_tables(ANCHORS_TO_PREFIX_TABLE)
    logger.info(f"create table with query: {query}")
    clickhouse_driver.execute(query)

    query = clickhouse_driver.create_prefixes_ping_tables(PROBES_TO_PREFIX_TABLE)
    logger.info(f"create table with query: {query}")
    clickhouse_driver.execute(query)

    query = clickhouse_driver.create_prefixes_ping_tables(
        TARGET_TO_LANDMARKS_PING_TABLE
    )
    logger.info(f"create table with query: {query}")
    clickhouse_driver.execute(query)

    # create traceroute table
    query = clickhouse_driver.create_traceroutes_table(ANCHORS_MESHED_TRACEROUTE_TABLE)
    clickhouse_driver.execute(query)

    # TODO: why do we need this table
    # query = create_street_level_table()

    # table names
    tables = [
        ANCHORS_MESHED_TRACEROUTE_TABLE,
        PROBES_TO_ANCHORS_PING_TABLE,
        ANCHORS_TO_PREFIX_TABLE,
        PROBES_TO_PREFIX_TABLE,
        ANCHORS_MESHED_PING_TABLE,
        TARGET_TO_LANDMARKS_PING_TABLE,
    ]

    # measurements files_path
    file_paths = [
        ANCHORS_MESHED_TRACEROUTE_FILE,
        PROBES_TO_ANCHORS_PING_FILE,
        ANCHORS_TO_PREFIX_FILE,
        PROBES_TO_PREFIX_FILE,
        ANCHORS_MESHED_PING_FILE,
        TARGET_TO_LANDMARKS_PING_FILE,
    ]

    for table_name, file_path in zip(tables, file_paths):
        print(table_name, file_path)
        insert_query = clickhouse_driver.insert_native_query(table_name, file_path)

        clickhouse_driver.insert_file(insert_query)
