from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from aiograpi import Client
from aiograpi.exceptions import (
    BadPassword,
    ReloginAttemptExceeded,
    ChallengeRequired,
    SelectContactPointRecoveryForm,
    RecaptchaChallengeForm,
    FeedbackRequired,
    PleaseWaitFewMinutes,
    LoginRequired,
)
import json
import os
import logging
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    username: str
    password: str
    proxy: Optional[str] = None


class LoginResponse(BaseModel):
    success: bool
    message: str
    session_id: Optional[str] = None


async def get_client():
    client = Client()
    client.delay_range = [1, 3]
    yield client
    await client.close()


async def handle_exception(client: Client, e: Exception):
    if isinstance(e, BadPassword):
        logger.exception(e)
        client.set_proxy(client.next_proxy().href)
        if client.relogin_attempt > 0:
            raise ReloginAttemptExceeded(str(e))
        client.settings = client.rebuild_client_settings()
        return client.get_settings()
    elif isinstance(e, LoginRequired):
        logger.exception(e)
        await client.relogin()
        return client.get_settings()
    elif isinstance(e, ChallengeRequired):
        api_path = client.last_json.get("challenge", {}).get("api_path")
        if api_path == "/challenge/":
            client.set_proxy(client.next_proxy().href)
            client.settings = client.rebuild_client_settings()
        else:
            try:
                await client.challenge_resolve(client.last_json)
            except (
                ChallengeRequired,
                SelectContactPointRecoveryForm,
                RecaptchaChallengeForm,
            ) as challenge_error:
                raise HTTPException(status_code=403, detail=str(challenge_error))
        return client.get_settings()
    elif isinstance(e, FeedbackRequired):
        message = client.last_json["feedback_message"]
        if "This action was blocked. Please try again later" in message:
            raise HTTPException(status_code=429, detail=message)
        elif "We restrict certain activity to protect our community" in message:
            raise HTTPException(status_code=429, detail=message)
        elif "Your account has been temporarily blocked" in message:
            raise HTTPException(status_code=403, detail=message)
    elif isinstance(e, PleaseWaitFewMinutes):
        raise HTTPException(status_code=429, detail=str(e))
    raise HTTPException(status_code=500, detail=str(e))


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, client: Client = Depends(get_client)):
    try:
        if os.path.exists("session.json"):
            with open("session.json", "r") as f:
                session = json.load(f)
            client.set_settings(session)
            try:
                await client.get_timeline_feed()
                return LoginResponse(
                    success=True,
                    message="Logged in using session",
                    session_id=client.sessionid,
                )
            except LoginRequired:
                logger.info("Session is invalid, logging in with username and password")

        if request.proxy:
            client.set_proxy(request.proxy)

        await client.login(request.username, request.password)

        with open("session.json", "w") as f:
            json.dump(client.get_settings(), f)

        return LoginResponse(
            success=True, message="Login successful", session_id=client.sessionid
        )
    except Exception as e:
        return await handle_exception(client, e)


@router.post("/logout")
async def logout(session_id: str, client: Client = Depends(get_client)):
    try:
        client.sessionid = session_id
        await client.login_by_sessionid(session_id)
        await client.logout()
        if os.path.exists("session.json"):
            os.remove("session.json")
        return {"success": True, "message": "Logout successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
