"""get all credentials (Clickhouse and RIPE)"""
import json
import os

from logger import logger
from dotenv import load_dotenv


def get_clickhouse_credentials() -> dict:
    """return clickhouse credentials"""
    load_dotenv()

    # try to get credentials with env var directly
    try:
        return {
            "base_url": os.environ["CLICKHOUSE_BASE_URL"],
            "user": os.environ["CLICKHOUSE_USER"],
            "password": os.environ["CLICKHOUSE_PASSWORD"],
        }

    except KeyError as e:
        logger.error(
            f"Missing credentials for interacting with IRIS API (set: CLICKHOUSE_BASE_URL | CLICKHOUSE_USERNAME | CLICKHOUSE_PASSWORD): {e}"
        )


def get_ripe_atlas_credentials() -> dict:
    """return ripe credentials"""
    try:
        return {
            "username": os.environ["RIPE_USERNAME"],
            "secret_key": os.environ["RIPE_SECRET_KEY"],
        }

    except KeyError as e:
        logger.error(
            f"Missing credentials for interacting with IRIS API (set: CLICKHOUSE_BASE_URL | CLICKHOUSE_USERNAME | CLICKHOUSE_PASSWORD): {e}"
        )
