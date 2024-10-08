from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)

load_dotenv()


class Sentry:
    SENTRY_DSN = os.getenv("SENTRY_DSN")
    SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT")


class Proxy:
    PROXY_IPS = os.getenv("PROXY_IPS", "").split(",")
    logger.info(f"Loaded {len(PROXY_IPS)} proxies from environment")


class Postgres:
    POSTGRES_URL = os.getenv("POSTGRES_URL")


class Secrets:
    SENTRY = Sentry()
    PROXY = Proxy()
    POSTGRES = Postgres()


logger.info("Secrets loaded")
