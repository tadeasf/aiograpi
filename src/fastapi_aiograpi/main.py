from fastapi import FastAPI
from src.fastapi_aiograpi.routes.auth import router as auth_router
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from src.fastapi_aiograpi.utils.config_secrets import Secrets

sentry_sdk.init(
    dsn=Secrets.SENTRY.SENTRY_DSN,
    traces_sample_rate=0.5,  # Capture 100% of transactions for performance monitoring
    profiles_sample_rate=0.5,  # Capture 100% of profiles for performance monitoring
    environment=Secrets.SENTRY.SENTRY_ENVIRONMENT,
    integrations=[
        FastApiIntegration(
            transaction_style="url",
        ),
        StarletteIntegration(),
        AsyncioIntegration(),
    ],
    # Enable performance monitoring
    enable_tracing=True,
    # Enable profiling
    _experiments={"profiles_sample_rate": 0.2},
    # Add release information
    release=__import__("tomllib").load(open("pyproject.toml", "rb"))["project"][
        "version"
    ],  # Dynamically grab version from pyproject.toml
    # Add server name
    server_name="fastapi_aiograpi_server",
    # Add custom data to events
    default_integrations=True,
    attach_stacktrace=True,
    send_default_pii=True,
    # Add context for better error grouping
    before_send=lambda event, hint: {
        **event,
        "tags": {**event.get("tags", {}), "app": "fastapi_aiograpi"},
    },
)

app = FastAPI()

app.include_router(auth_router, prefix="/auth", tags=["auth"])


@app.get("/")
async def root():
    return {"message": "Welcome to the Instagram API"}


@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0  # noqa: F841
