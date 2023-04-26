import logging
import time
import requests

logger = logging.getLogger()


class RIPEAtlas(object):
    def __init__(
            self, 
            account : str, 
            key: str,            
    ) -> None:

        self.account = account
        self.key = key

    def _wait_for(self, measurement_id, max_retry: int =60):
        for _ in range(max_retry):
            response = requests.get(
                "https://atlas.ripe.net/api/v2/"
                f"measurements/{measurement_id}/results/?key={self.key}"
            ).json()

            if response:
                return response
            time.sleep(2)

    def probe(self, target, vps, tag: str, nb_packets: int = 3, max_retry: int = 60):
        """start ping measurement towards target from vps, return Atlas measurement id"""
        
        for _ in range(max_retry):
            response = requests.post(
                f"https://atlas.ripe.net/api/v2/measurements/?key={self.key}",
                json={
                    "definitions": [
                        {
                            "target": target,
                            "af": 4,
                            "packets": nb_packets,
                            "size": 48,
                            "tags": [tag],
                            "description": f"Dioptra Geolocation of {target}",
                            "resolve_on_probe": False,
                            "skip_dns_check": True,
                            "include_probe_id": False,
                            "type": "ping",
                        }
                    ],
                    "probes": [
                        {"value": vp, "type": "probes", "requested": 1}
                        for vp in vps
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

        if not response:
            return

        try:
            return measurement_id
        except (IndexError, KeyError):
            return
    
    def __str__(self):
        return "RIPE Atlas"
    
