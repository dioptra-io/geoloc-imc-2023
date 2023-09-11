"""clickhouse client"""
import subprocess

from pathlib import Path
from clickhouse_driver import Client

from logger import logger
from default import (
    CLICKHOUSE_HOST,
    CLICKHOUSE_DB,
    CLICKHOUSE_USER,
    CLICKHOUSE_PASSWORD,
    CLICKHOUSE_CLIENT_PATH,
)


class Clickhouse:
    def __init__(
        self,
        host: str = CLICKHOUSE_HOST,
        database: str = CLICKHOUSE_DB,
        user: str = CLICKHOUSE_USER,
        password: str = CLICKHOUSE_PASSWORD,
        client_path: Path = CLICKHOUSE_CLIENT_PATH,
    ) -> None:
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.client_path = client_path

        self.client: Client = Client(
            host=self.host, user=self.user, password=self.password
        )

        self.settings = {"max_block_size": 100000}

    def get_min_rtt_per_src_dst_query(
        self, table: str, filter: str, threshold=10000
    ) -> str:
        return f"""
        WITH  arrayMin(groupArray(`min`)) as min_rtt
        SELECT IPv4NumToString(dst), IPv4NumToString(src), min_rtt
        FROM {self.database}.{table}
        WHERE `min` > -1 AND `min`< {threshold} AND dst != src {filter}
        GROUP BY (dst, src)
        """

    def get_min_rtt_per_src_dst_prefix_query(
        self, table: str, filter: str, threshold=10000
    ) -> str:
        return f"""
        WITH  arrayMin(groupArray(`min`)) as min_rtt
        SELECT IPv4NumToString(dst_prefix), IPv4NumToString(src), min_rtt
        FROM {self.database}.{table}
        WHERE `min` > -1 AND `min`< {threshold}
        AND dst_prefix != toIPv4(substring(cutIPv6(IPv4ToIPv6(src), 0, 1), 8))
        {filter}
        GROUP BY dst_prefix, src
        """

    def insert_native_query(self, table: str, infile_path: Path) -> str:
        """insert data using local clickhouse file"""
        return f"""
        INSERT INTO {self.database}.{table}
        FROM INFILE '{str(infile_path)}'
        FORMAT Native
        """

    def insert_file(self, query: str) -> None:
        """execute clickhouse insert query as not supported by clickhouse-driver"""
        cmd = [
            str(self.client_path),
            "client",
            f"--query={query}",
        ]

        logger.info(f"executing query: {cmd}")

        process = subprocess.Popen(cmd)
        process.wait()
        logger.info(f"query output: {process.stdout}, {process.stderr}")

    def execute(self, query: str) -> None:
        """execute query using clickhouse driver"""
        return self.client.execute(query, settings=self.settings)

    def execute_iter(self, query: str) -> None:
        """use clickhouse driver instead of subprocess"""
        return self.client.execute_iter(query, settings=self.settings)

    def create_prefixes_ping_tables(self, table_name: str) -> str:
        """create all ping tables"""
        return f"""
        CREATE TABLE IF NOT EXISTS {self.database}.{table_name} 
        (
        `src` IPv4,
        `dst` IPv4,
        `dst_prefix` IPv4 MATERIALIZED toIPv4(substring(cutIPv6(IPv4ToIPv6(dst), 0, 1), 8)),
        `prb_id` UInt32,
        `date` DateTime,
        `sent` UInt32,
        `rcvd` UInt32,
        `rtts` Array(Float64),
        `min` Float64,
        `mean` Float64,
        `msm_id` UInt64,
        `proto` UInt8
        ) 
        ENGINE=MergeTree() 
        ORDER BY (dst_prefix, dst, src, msm_id, date)
        """

    def create_target_ping_tables(self, table_name: str) -> str:
        """create table"""
        return f"""
        CREATE TABLE IF NOT EXISTS {self.database}.{table_name} 
        (
        `src` IPv4,
        `dst` IPv4,
        `prb_id` UInt32,
        `date` DateTime,
        `sent` UInt32,
        `rcvd` UInt32,
        `rtts` Array(Float64),
        `min` Float64,
        `mean` Float64,
        `msm_id` UInt64,
        `proto` UInt8
        ) 
        ENGINE=MergeTree() 
        ORDER BY (dst, src, msm_id, date)
        """

    def create_traceroutes_table(self, table_name: str) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS {self.database}.{table_name} 
        (
        `src_ip` String,
        `dst_prefix` String,
        `dst_ip` String,
        `reply_ip` String,
        `proto` Int16,
        `hop` Int16,
        `rtt` Float64,
        `ttl` Int16,
        `prb_id` Int64,
        `msm_id` Int64,
        `timestamp` DateTime('UTC')
        ) 
        ENGINE=MergeTree() 
        ORDER BY (dst_prefix, dst_ip, src_ip, reply_ip)
        """
