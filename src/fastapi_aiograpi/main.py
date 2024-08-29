from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from .utils.config_secrets import Secrets
from .utils.session_store import session_store
from .routes.auth import auth
from .routes.profiles import profile_stats, highlights
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error occurred: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception("An unexpected error occurred")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(profile_stats.router, prefix="/profiles", tags=["profiles"])
app.include_router(highlights.router, prefix="/highlights", tags=["highlights"])


@app.on_event("startup")
async def startup_event():
    session_store.load_sessions()


@app.get("/")
async def root():
    return {"message": "Welcome to the Instagram API"}


@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0  # noqa: F841
