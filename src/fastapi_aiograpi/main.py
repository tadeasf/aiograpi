from fastapi import FastAPI
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from src.fastapi_aiograpi.utils.config_secrets import Secrets
from src.fastapi_aiograpi.utils.session_store import session_store
from src.fastapi_aiograpi.routes import (
    auth_router,
)
from src.fastapi_aiograpi.routes.profiles import profile_stats_router, highlights_router

sentry_sdk.init(
    dsn=Secrets.SENTRY.SENTRY_DSN,
    traces_sample_rate=1.0,
    profiles_sample_rate=0.5,
    environment=Secrets.SENTRY.SENTRY_ENVIRONMENT,
    integrations=[
        FastApiIntegration(transaction_style="url"),
        StarletteIntegration(),
        AsyncioIntegration(),
    ],
    enable_tracing=True,
    _experiments={"profiles_sample_rate": 0.2},
    release=__import__("tomllib").load(open("pyproject.toml", "rb"))["project"][
        "version"
    ],
    server_name="fastapi_aiograpi_server",
    default_integrations=True,
    attach_stacktrace=True,
    send_default_pii=True,
    before_send=lambda event, hint: {
        **event,
        "tags": {**event.get("tags", {}), "app": "fastapi_aiograpi"},
    },
)

app = FastAPI()

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(
    profile_stats_router, prefix="/profile_stats", tags=["profile_stats"]
)
app.include_router(highlights_router, prefix="/profiles", tags=["highlights"])


@app.on_event("startup")
async def startup_event():
    session_store.load_sessions()


@app.get("/")
async def root():
    return {"message": "Welcome to the Instagram API"}


@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0  # noqa: F841
