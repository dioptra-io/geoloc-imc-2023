import logging

logging.basicConfig(
    format="%(asctime)s::%(levelname)s:%(name)s:%(module)s:: %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger()
