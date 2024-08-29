from fastapi import Path, HTTPException, Depends
from aiograpi import Client
from aiograpi.exceptions import LoginRequired, ClientError
from .proxy_manager import proxy_manager
from ..database.postgresql_handler import get_session
from ..utils.session_manager import SessionStore
import sentry_sdk
import logging

logger = logging.getLogger(__name__)


async def get_client(
    password: str, username: str = Path(...), session=Depends(get_session)
):
    """
    Retrieves an aiograpi Client instance with session and proxy settings for the given username.
    """
    client = Client()
    client.delay_range = [1, 3]  # Add random delay between requests
    session_store = SessionStore(session)

    try:
        session_data = session_store.get_session(username)
        proxy = session_store.get_proxy_for_user(username)

        if not proxy:
            logger.info(
                f"No proxy found for user {username}, attempting to get a working proxy"
            )
            proxy = await proxy_manager.get_working_proxy()
            logger.info(f"Assigned proxy {proxy} to user {username}")
            session_store.assign_proxy(username, proxy)

        client.set_proxy(f"http://{proxy}")

        if session_data:
            logger.info(f"Using existing session for user {username}")
            client.set_settings(session_data)
            sentry_sdk.set_context(
                "session", {"username": username, "status": "existing"}
            )
            try:
                await client.get_timeline_feed()  # Check if session is valid
                logger.info("Session is valid")
                return client
            except (LoginRequired, ClientError) as e:
                logger.warning(
                    f"Session is invalid for user {username}, need to re-login: {str(e)}"
                )
                session_data = None  # Force re-login

        if not session_data:
            logger.info(f"No valid session for user {username}, attempting to login")
            # Here, instead of raising an exception, attempt to log in safely
            if not session_store.verify_password(username, password):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid credentials. Please log in via /auth/login endpoint.",
                )

            try:
                await client.login(username, password)
                logger.info(f"Login successful for user {username}")
                session_store.save_session(username, client.get_settings(), proxy)
                return client
            except Exception as e:
                logger.error(f"Login failed for user {username}: {str(e)}")
                raise HTTPException(
                    status_code=401,
                    detail="Authentication failed. Please log in via /auth/login endpoint.",
                )

        sentry_sdk.set_context("proxy", {"used": proxy})
        sentry_sdk.add_breadcrumb(
            category="auth",
            message="Client initialized",
            data={"username": username, "proxy": proxy},
        )
        return client
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to initialize client for user {username}: {e}")
        sentry_sdk.capture_exception(e)
        raise HTTPException(
            status_code=503,
            detail="Failed to initialize client. Please try again later.",
        )
