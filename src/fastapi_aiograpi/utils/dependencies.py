from fastapi import Depends, Path, HTTPException
from aiograpi import Client
from aiograpi.exceptions import LoginRequired, ClientError
from .session_store import session_store
from .proxy_manager import proxy_manager
import sentry_sdk
import logging

logger = logging.getLogger(__name__)


async def get_client(username: str = Path(...)):
    """
    Retrieves an aiograpi Client instance with session and proxy settings for the given username.
    """
    client = Client()
    client.delay_range = [1, 3]  # Add random delay between requests
    try:
        session = session_store.get_session(username)
        proxy = session_store.get_proxy_for_user(username)

        if not proxy:
            logger.info(
                f"No proxy found for user {username}, attempting to get a working proxy"
            )
            proxy = await proxy_manager.get_working_proxy()
            logger.info(f"Assigned proxy {proxy} to user {username}")
            session_store.assign_proxy(username, proxy)

        client.set_proxy(f"http://{proxy}")

        if session:
            logger.info(f"Using existing session for user {username}")
            client.set_settings(session)
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
                session = None  # Force re-login

        if not session:
            logger.info(f"No valid session for user {username}, attempting to login")
            # Here, instead of raising an exception, we should attempt to log in
            # You need to implement a secure way to store and retrieve passwords
            password = session_store.get_password(username)
            if not password:
                raise HTTPException(
                    status_code=401,
                    detail="No stored credentials. Please log in via /auth/login endpoint.",
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
