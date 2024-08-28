import aiohttp
from typing import List
import random


class ProxyManager:
    def __init__(self, proxy_ips: List[str]):
        self.proxy_ips = proxy_ips

    async def check_proxy(self, proxy: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://www.instagram.com", proxy=proxy, timeout=5
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"Proxy connection error: {e}")
            return False

    async def get_working_proxy(self) -> str:
        while self.proxy_ips:
            proxy = f"http://{random.choice(self.proxy_ips)}:6969"
            if await self.check_proxy(proxy):
                return proxy
            self.proxy_ips.remove(proxy.split("//")[1].split(":")[0])
        raise Exception("No working proxies available")

    def get_random_proxy(self) -> str:
        return f"http://{random.choice(self.proxy_ips)}:6969"


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
