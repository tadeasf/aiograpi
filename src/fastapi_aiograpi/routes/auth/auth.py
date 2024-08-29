from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel
from aiograpi import Client
from aiograpi.exceptions import (
    BadPassword,
    ChallengeRequired,
    FeedbackRequired,
    PleaseWaitFewMinutes,
    LoginRequired,
    ConnectProxyError,
)
import logging
from typing import Optional
from ...utils.session_store import session_store
from ...utils.proxy_manager import proxy_manager
from ...utils.rate_limiter import rate_limiter
import sentry_sdk

router = APIRouter()
logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    session_id: Optional[str] = None


async def get_client(username: str = Query(...)):
    client = Client()
    client.delay_range = [1, 3]
    try:
        session = session_store.get_session(username)
        if session:
            client.set_settings(session)
            proxy = session_store.get_proxy_for_user(username)
            sentry_sdk.set_context(
                "session", {"username": username, "status": "existing"}
            )
        else:
            proxy = await proxy_manager.get_working_proxy()
            session_store.assign_proxy(username, [proxy])
            sentry_sdk.set_context("session", {"username": username, "status": "new"})
        client.set_proxy(proxy)
        sentry_sdk.set_context("proxy", {"used": proxy})
        sentry_sdk.add_breadcrumb(
            category="auth",
            message="Client initialized",
            data={"username": username, "proxy": proxy},
        )
        yield client
    except Exception as e:
        logger.exception(f"Failed to get working proxy: {e}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(
            status_code=503,
            detail="No working proxies available. Please try again later.",
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    username: str = Query(...),
    request: LoginRequest = Body(...),
    client: Client = Depends(get_client),
):
    try:
        rate_limiter.check_rate_limit(username)
        session = session_store.get_session(username)
        if session:
            client.set_settings(session)
            sentry_sdk.add_breadcrumb(
                category="auth",
                message="Using existing session",
                data={"username": username},
            )
        await client.login(username, request.password)
        if not session:
            session_store.save_session(username, client.get_settings(), client.proxy)
            sentry_sdk.add_breadcrumb(
                category="auth",
                message="Created new session",
                data={"username": username},
            )
        sentry_sdk.add_breadcrumb(
            category="auth",
            message="Login successful",
            data={"username": username, "proxy": client.proxy},
        )
        return LoginResponse(
            success=True, message="Login successful", session_id=client.sessionid
        )
    except ConnectProxyError as e:
        logger.exception(f"Proxy connection error: {e}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(
            status_code=503,
            detail="Unable to connect to proxy. Please try again later.",
        )
    except (
        BadPassword,
        LoginRequired,
        ChallengeRequired,
        FeedbackRequired,
        PleaseWaitFewMinutes,
    ) as e:
        logger.exception(f"Login error: {e}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error during login: {e}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/logout")
async def logout(username: str = Query(...), client: Client = Depends(get_client)):
    try:
        rate_limiter.check_rate_limit(username)
        session_store.save_session(username, {}, client.proxy)  # Clear the session
        sentry_sdk.add_breadcrumb(
            category="auth",
            message="Logout successful",
            data={"username": username, "proxy": client.proxy},
        )
        return {"success": True, "message": "Logged out successfully"}
    except Exception as e:
        logger.exception(f"Unexpected error during logout: {e}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(status_code=500, detail=str(e))
