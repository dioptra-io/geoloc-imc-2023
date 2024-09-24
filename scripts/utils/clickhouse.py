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
    CLICKHOUSE_CLIENT,
)


class Clickhouse:
    def __init__(
        self,
        host: str = CLICKHOUSE_HOST,
        database: str = CLICKHOUSE_DB,
        user: str = CLICKHOUSE_USER,
        password: str = CLICKHOUSE_PASSWORD,
        client_path: Path = CLICKHOUSE_CLIENT,
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

    def get_all_rtt_to_dst_address_query(self, table: str, target: str) -> str:
        return f"""
        SELECT src_addr, rtt, tstamp 
        FROM {self.database}.{table} 
        WHERE resp_addr = '{target}' AND dst_addr = '{target}'
        """

    def get_all_rtt_from_probe_to_targets_query(
        self, table: str, src: str, target1: str, target2: str
    ) -> str:
        return f"""
            SELECT resp_addr, dst_addr, rtt 
            FROM {self.database}.{table}  
            WHERE src_addr = '{src}' and (dst_addr =  '{target1}' or dst_addr = '{target2}')
        """

    def insert_street_lvl_traceroutes_query(self, table: str) -> str:
        return f"""
            INSERT 
            INTO {self.database}.{table} (
                src_addr, dst_prefix, dst_addr, resp_addr, 
                proto, hop, rtt, ttl, prb_id, msm_id, tstamp
            ) VALUES
        """

    def insert_native_query(self, table: str, infile_path: Path) -> str:
        """insert data using local clickhouse file"""
        return f"""
        INSERT INTO {self.database}.{table}
        FROM INFILE '{str(infile_path)}'
        FORMAT Native"""

    def insert_csv_query(self, table: str, infile_path: Path) -> str:
        """insert data from csv file"""
        return f"""
        INSERT INTO {self.database}.{table}
        FROM INFILE '{str(infile_path)}'
        FORMAT CSV
        """

    def insert_file(self, query: str) -> None:
        """execute clickhouse insert query as not supported by clickhouse-driver"""
        cmd = f"{str(self.client_path)} client"

        if self.password is not None and self.password != "":
            cmd += f"--password={self.password}"
        cmd += f' --query="{query}"'

        logger.info(f"executing query: {cmd}")

        ps = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if ps.stderr:
            raise RuntimeError(
                f"Could not insert data::{cmd}, failed with error: {ps.stderr}"
            )
        else:
            logger.info(f"{cmd}::Successfully executed")

    def execute(self, query: str, arg_lst=[]) -> None:
        """execute query using clickhouse driver"""
        if arg_lst == []:
            return self.client.execute(query, settings=self.settings)
        else:
            return self.client.execute(query, arg_lst, settings=self.settings)

    def insert_from_values_query(self, table: str, values_description: str) -> str:
        """insert data from csv file"""
        return f"""
        INSERT INTO {self.database}.{table}
        ({values_description})
        VALUES
        """

    def insert_from_values(self, query: str, data: list) -> None:
        return self.client.execute(query, data, settings=self.settings)

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

    def create_street_level_table(self, table_name: str) -> str:
        """create the street level traceroute table"""

        return f"""
        CREATE TABLE IF NOT EXISTS {self.database}.{table_name} 
        (
        `src_addr` String, 
        `dst_prefix` String, 
        `dst_addr` String, 
        `resp_addr` String, 
        `proto` Int16, 
        `hop` Int16, 
        `rtt` Float64, 
        `ttl` Int16, 
        `prb_id` Int64, 
        `msm_id` Int64,
        `tstamp` Datetime('UTC')
        )
        ENGINE = MergeTree()
        ORDER BY (dst_addr, src_addr, tstamp)
        """
