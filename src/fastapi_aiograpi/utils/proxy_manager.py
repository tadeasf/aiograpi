import httpx
from typing import List
from .config_secrets import Secrets
import sentry_sdk
import logging


logger = logging.getLogger(__name__)


class ProxyManager:
    def __init__(self, proxy_ips: List[str]):
        self.proxy_ips = proxy_ips
        logger.info(f"Initialized ProxyManager with {len(proxy_ips)} proxies")

    async def check_proxy(self, proxy: str) -> bool:
        try:
            proxy_url = f"http://{proxy}"
            async with httpx.AsyncClient(
                proxies={"https://": proxy_url}, timeout=10, verify=False
            ) as client:
                response = await client.get(
                    "https://www.instagram.com", follow_redirects=True
                )
                success = response.status_code < 400
                logger.info(
                    f"Proxy check: {'success' if success else 'fail'} for {proxy_url}. Status: {response.status_code}"
                )
                sentry_sdk.add_breadcrumb(
                    category="proxy",
                    message=f"Proxy check: {'success' if success else 'fail'}",
                    data={"proxy": proxy_url, "status": response.status_code},
                )
                return success
        except httpx.TimeoutException:
            logger.error(f"Proxy check timed out for {proxy}")
            return False
        except Exception as e:
            logger.error(f"Proxy check failed for {proxy}: {str(e)}")
            sentry_sdk.capture_exception(e)
            sentry_sdk.add_breadcrumb(
                category="proxy",
                message="Proxy check failed",
                data={"proxy": proxy, "error": str(e)},
                level="error",
            )
            return False

    async def get_working_proxy(self) -> str:
        """
        Returns a working proxy from the list, checking its validity.
        If no working proxies are found, raises an exception.
        """
        logger.info("Attempting to get a working proxy")
        for proxy in self.proxy_ips:
            if await self.check_proxy(proxy):
                logger.info(f"Working proxy found: {proxy}")
                sentry_sdk.add_breadcrumb(
                    category="proxy",
                    message="Working proxy found",
                    data={"proxy": proxy},
                )
                return proxy
        logger.error("No working proxies available")
        sentry_sdk.add_breadcrumb(
            category="proxy",
            message="No working proxies available",
            level="error",
        )
        raise Exception("No working proxies available")


proxy_manager = ProxyManager(Secrets.PROXY.PROXY_IPS)
logger.info(f"ProxyManager initialized with {len(proxy_manager.proxy_ips)} proxies")
