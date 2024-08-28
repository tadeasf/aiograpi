from typing import List
import random


class ProxyManager:
    def __init__(self, proxy_ips: List[str]):
        self.proxy_ips = proxy_ips

    def get_random_proxy(self) -> str:
        return f"http://{random.choice(self.proxy_ips)}:6969"  # Using port 6969 as configured in Squid


proxy_manager = ProxyManager(
    [
        "45.90.120.30",
        "91.205.105.195",
        "38.242.244.36",
        "185.192.97.2",
        "185.234.71.120",
        "167.86.68.173",
        "194.5.152.243",
    ]
)
