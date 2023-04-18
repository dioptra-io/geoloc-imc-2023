import pandas as pd
import requests
import time
import logging

from utils.helpers import haversine


logger = logging.getLogger()


class RIPEAtlas(object):
    def __init__(self, account, key):
        self.account = account
        self.key = key

    def _wait_for(self, measurement, timeout=60):
        for _ in range(timeout):
            response = requests.get(
                "https://atlas.ripe.net/api/v2/"
                f"measurements/{measurement}/results/?key={self.key}"
            )

            response = response.json()
            if response:
                return response
            time.sleep(2)

    def probe(self, target, anchors, nb_packets: int = 3):
        timeout = 60
        for _ in range(timeout):
            response = requests.post(
                f"https://atlas.ripe.net/api/v2/measurements/?key={self.key}",
                json={
                    "definitions": [
                        {
                            "target": target,
                            "af": 4,
                            "packets": nb_packets,
                            "size": 48,
                            "description": f"Dioptra Geolocation of {target}",
                            "resolve_on_probe": False,
                            "skip_dns_check": True,
                            "include_probe_id": False,
                            "type": "ping",
                        }
                    ],
                    "probes": [
                        {"value": anchor, "type": "probes", "requested": 1}
                        for anchor in anchors
                    ],
                    "is_oneoff": True,
                    "bill_to": self.account,
                },
            ).json()

            try:
                measurement_id = response["measurements"][0]
                break
            except KeyError:
                logger.info(response)
                logger.info("Warning!", "Too much measurements.", "Waiting.")
                time.sleep(60)
        else:
            raise Exception("Too much measurements. Stopping.")

        response = self._wait_for(measurement_id, timeout=timeout)
        if not response:
            return

        try:
            return measurement_id, response
        except (IndexError, KeyError):
            return

    def __str__(self):
        return "RIPE Atlas"
