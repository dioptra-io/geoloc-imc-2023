from atlas_probing import RIPEAtlas

class CGB():
    def __init__(
            self,
            targets: list,
            vps: list,
            ripe_credentials: dict[str, str],
        ) -> None:
        self.targets = targets
        self.vps = vps
        self.ripe_credentials = ripe_credentials

        self.driver = RIPEAtlas(ripe_credentials['username'], ripe_credentials['key'])
    
    def get_ip_in_target_prefixes(self) -> dict:
        target_prefix_ips = {}
        for target in 
    def initialization(self):
        """probe each targets for each vantage points"""
        for target in self.targets:
            vp_ids = [vp['id'] for vp in self.vps]
            measurement_ids = self.driver.probe(target, vp_ids)

            