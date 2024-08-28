import aiohttp
from typing import List
import random
from src.fastapi_aiograpi.utils.config_secrets import Secrets
import sentry_sdk


class ProxyManager:
    def __init__(self, proxy_ips: List[str]):
        self.proxy_ips = proxy_ips

    async def check_proxy(self, proxy: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://www.instagram.com", proxy=proxy, timeout=5
                ) as response:
                    success = response.status == 200
                    sentry_sdk.add_breadcrumb(
                        category="proxy",
                        message=f"Proxy check: {'success' if success else 'fail'}",
                        data={"proxy": proxy, "status": response.status},
                    )
                    return success
        except Exception as e:
            sentry_sdk.capture_exception(e)
            sentry_sdk.add_breadcrumb(
                category="proxy",
                message="Proxy check failed",
                data={"proxy": proxy, "error": str(e)},
                level="error",
            )
            return False

    async def get_working_proxy(self) -> str:
        tried_proxies = []
        while self.proxy_ips:
            proxy = f"http://{random.choice(self.proxy_ips)}:6969"
            tried_proxies.append(proxy)
            if await self.check_proxy(proxy):
                sentry_sdk.add_breadcrumb(
                    category="proxy",
                    message="Working proxy found",
                    data={"proxy": proxy, "tried_proxies": tried_proxies},
                )
                return proxy
            self.proxy_ips.remove(proxy.split("//")[1].split(":")[0])
        sentry_sdk.add_breadcrumb(
            category="proxy",
            message="No working proxies available",
            data={"tried_proxies": tried_proxies},
            level="error",
        )
        raise Exception("No working proxies available")

    def get_random_proxy(self) -> str:
        proxy = f"http://{random.choice(self.proxy_ips)}:6969"
        sentry_sdk.add_breadcrumb(
            category="proxy",
            message="Random proxy selected",
            data={"proxy": proxy},
        )
        return proxy


proxy_manager = ProxyManager(Secrets.PROXY.PROXY_IPS)
