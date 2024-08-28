from dotenv import load_dotenv
import os

load_dotenv()


class Sentry:
    SENTRY_DSN = os.getenv("SENTRY_DSN")
    SENTRY_ENVIRONMENT = os.getenv("SENTRY_ENVIRONMENT")


class Proxy:
    PROXY_IPS = os.getenv("PROXY_IPS").split(",")


class Secrets:
    SENTRY = Sentry()
    PROXY = Proxy()
