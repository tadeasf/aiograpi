from fastapi import APIRouter, HTTPException, Depends, Body, Path
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
from ...utils.session_store import session_store
from ...utils.rate_limiter import rate_limiter
from ...utils.dependencies import get_client
import sentry_sdk

router = APIRouter()
logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    session_id: str


@router.post("/login/{username}", response_model=LoginResponse)
async def login(
    username: str = Path(...),
    request: LoginRequest = Body(...),
    client: Client = Depends(get_client),
):
    """
    Logs in a user with the given username and password, managing sessions and proxies.
    """
    try:
        rate_limiter.check_rate_limit(username)
        session = session_store.get_session(username)

        login_via_session = False
        login_via_pw = False

        if session:
            try:
                client.set_settings(session)
                await client.login(username, request.password)

                try:
                    await client.get_timeline_feed()  # Check if session is valid
                    login_via_session = True
                    logger.info(f"Logged in using session for user {username}")
                except LoginRequired:
                    logger.info(
                        f"Session is invalid for user {username}, logging in with username and password"
                    )
                    old_session = client.get_settings()

                    # Use the same device UUIDs across logins
                    client.set_settings({})
                    client.set_uuids(old_session["uuids"])

                    await client.login(username, request.password)
                    login_via_pw = True
            except Exception as e:
                logger.info(f"Couldn't login user {username} using session: {str(e)}")

        if not login_via_session and not login_via_pw:
            logger.info(
                f"Attempting to login via username and password for user {username}"
            )
            if await client.login(username, request.password):
                login_via_pw = True

        if not login_via_pw and not login_via_session:
            raise Exception(
                f"Couldn't login user {username} with either password or session"
            )

        # Save the session
        session_store.save_session(
            username, client.get_settings(), client.proxy, request.password
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


@router.post("/logout/{username}")
async def logout(username: str = Path(...), client: Client = Depends(get_client)):
    """
    Logs out a user, clearing their session data.
    """
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
