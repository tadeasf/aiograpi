from fastapi import APIRouter, HTTPException, Depends
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
from ...utils.session_manager import SessionManager
from ...utils.proxy_manager import ProxyManager

router = APIRouter()
logger = logging.getLogger(__name__)

session_manager = SessionManager()
proxy_manager = ProxyManager(
    [
        "vps1.example.com",
        "vps2.example.com",
        "vps3.example.com",
        "vps4.example.com",
        "vps5.example.com",
    ]
)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    session_id: Optional[str] = None


async def get_client():
    client = Client()
    client.delay_range = [1, 3]
    try:
        proxy = await proxy_manager.get_working_proxy()
        client.set_proxy(proxy)
        yield client
    except Exception as e:
        logger.exception(f"Failed to get working proxy: {e}")
        raise HTTPException(
            status_code=503,
            detail="No working proxies available. Please try again later.",
        )
    finally:
        client = None


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, client: Client = Depends(get_client)):
    try:
        success = await session_manager.login_user(
            request.username, request.password, client
        )
        if success:
            return LoginResponse(
                success=True, message="Login successful", session_id=client.sessionid
            )
        else:
            raise HTTPException(status_code=401, detail="Login failed")
    except ConnectProxyError as e:
        logger.exception(f"Proxy connection error: {e}")
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
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post("/logout")
async def logout(client: Client = Depends(get_client)):
    try:
        session_manager.save_session({})  # Clear the session
        return {"success": True, "message": "Logged out successfully"}
    except Exception as e:
        logger.exception(f"Unexpected error during logout: {e}")
        raise HTTPException(status_code=500, detail=str(e))
