import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID
from dotenv import dotenv_values

from iris_client import IrisClient
from pych_client import ClickHouseClient

from diamond_miner.defaults import UNIVERSE_SUBSET
from diamond_miner.queries.query import ResultsQuery, results_table
from diamond_miner.typing import IPNetwork


IRIS_CREDENTIAL_PATH = "~/.config/iris/credentials.json"

logger = logging.getLogger()

def get_iris_credentials() -> dict:
    """retrieve credentials from env variables and return them"""
    # try to get credentials with .env file
    try:
        dotenv_path = Path.cwd() / ".env"

        config = dotenv_values(str(dotenv_path))

        return {
            "base_url": config["IRIS_BASE_URL"],
            "username": config["IRIS_USERNAME"],
            "password": config["IRIS_PASSWORD"],
        }

    except KeyError as e:
        logger.warning(
            "no .env file was set within the repository, trying with env variables"
        )

    # try to get credentials with env var directly
    try:

        return {
            "base_url": os.environ["IRIS_BASE_URL"],
            "username": os.environ["IRIS_USERNAME"],
            "password": os.environ["IRIS_PASSWORD"],
        }

    except KeyError as e:
        logger.error(
            f"Missing credentials for interacting with IRIS API (set: IRIS_BASE_URL | IRIS_USERNAME | IRIS_PASSWORD): {e}"
        )

    # try to get credentials from configuration
    try:
        with open(IRIS_CREDENTIAL_PATH, "r+") as cfg_file:
            config = json.load(cfg_file)

        return {
            "base_url": config["IRIS_BASE_URL"],
            "username": config["IRIS_USERNAME"],
            "password": config["IRIS_PASSWORD"],
        }

    except FileExistsError as e:
        logger.error(
            f"no credentials found, credentials should be stored within: {IRIS_CREDENTIAL_PATH}"
        )
    except KeyError:
        logger.error(f"Some credentials are missing: {e}")

    raise RuntimeError(
        "Neither config nor env var was setup for Iris credentials, abort"
    )


class IrisProber:
    """Yarrp prober tool"""

    def __init__(
        self,
        probing_rates: Dict[UUID, int],
        input_file_path: Path = Path("."),
        tags: List[str] = ["atlas_ping_validation"],
        tool : str = "ping",
        prefix_len: int = 32,
        idle_time: int = 60,
        dry_run: bool = False,
    ) -> None:

        self.tags = tags
        self.probing_rates: Dict[UUID, int] = probing_rates
        self.dry_run = True
        self.input_file_path = input_file_path
        self.idle_time = idle_time
        self.dry_run = dry_run
        self.tool = tool

        self.prefix_len = prefix_len

        self.prefixes = {}
        self.measurement_uuid = None

        self.credentials = get_iris_credentials()

    def wait_until_complete(self, measurement_uuid) -> None:
        """
        Wait until the end of the measurement.
        """

        logger.debug("waiting for measurement to finish...")

        while True:
            try:
                with IrisClient(
                    timeout=None,
                    base_url=self.credentials["base_url"],
                    username=self.credentials["username"],
                    password="Vader411!",
                ) as client:

                    req = client.get(f"/measurements/{measurement_uuid}")
                    if req.json()["state"] == "finished":
                        return
            except Exception as e:
                logger.warning("WARNING!!", e)

            time.sleep(10)

    def probe(
        self,
        probing_rate = None
    ) -> Optional[UUID]:
        """
        Perform measurement using Iris.
        Returns measurement UUID.
        """
        file_paths = {}
        for agent_uuid in self.probing_rates:
            file_paths[agent_uuid] = self.input_file_path

        if self.dry_run:
            return None

        with IrisClient(
            timeout=None,
            base_url="https://api.iris.dioptra.io",
            username="hugorimlinger4@gmail.com",
            password="Vader411!",
        ) as client:

            # Upload the probes files
            for file_path in file_paths.values():
                with file_path.open("rb") as fd:
                    req = client.post("/targets/", files={"target_file": fd})
                if req.status_code != 201:
                    logger.error(req.text)
                    raise RuntimeError("Unable to upload the probe file")
                else:
                    logger.debug("Target file successfully uploaded")

            # Launch the measurement
            req = client.post(
                "/measurements/",
                json={
                    "tool": self.tool,
                    "agents": [
                        {
                            "uuid": str(agent_uuid),
                            "target_file": file_path.name,
                            "probing_rate": probing_rate if probing_rate else self.probing_rates[agent_uuid],
                            "tool_parameters": {
                                "prefix_len_v4": 32,
                                "prefix_len_v6" : 128,
                            }
                        }
                        for agent_uuid, file_path in file_paths.items()
                    ],
                    "tags": self.tags,
                },
            )
            if req.status_code != 201:
                logger.error(req.text)
                raise RuntimeError("Unable to launch the measurement")
            else:
                measurement_uuid = req.json()["uuid"]

        return measurement_uuid


class QueryPingResults(ResultsQuery):
    def statement(
        self,
        measurement_id: str,
        subsets: IPNetwork = UNIVERSE_SUBSET
    ) -> str:
        return f"""
        SELECT *
        FROM {results_table(measurement_id)}
        """

class PingResults:
    """get all links discovered during the measurement"""
    def __init__(self, measurement_uuid: str):

        self.measurement_uuid: str = measurement_uuid

    def measurement_id(self, agent_uuid: str):
        return f"{self.measurement_uuid}__{agent_uuid}"

    def query(
        self,
        agent_uuid: str,
    ) -> dict:
        """
        return dict with all routes to every destination for a measurement
        """
        ping_results = []

        with IrisClient() as iris:
            credentials = iris.get(
                "/users/me/services", params={"measurement_uuid": self.measurement_uuid}
            ).json()

            measurement_id = self.measurement_id(agent_uuid)

        with ClickHouseClient(**credentials["clickhouse"]) as clickhouse:

            # retrieve data from clichouse and parse
            for row in QueryPingResults().execute(
                clickhouse, measurement_id
            ):
                ping_results.append(row)

        return ping_results