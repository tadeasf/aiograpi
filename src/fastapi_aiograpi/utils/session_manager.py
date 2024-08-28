import json
import os
from typing import Optional
from aiograpi import Client
from aiograpi.exceptions import LoginRequired
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self, session_file: str = "session.json"):
        self.session_file = session_file

    def load_session(self) -> Optional[dict]:
        if os.path.exists(self.session_file):
            with open(self.session_file, "r") as f:
                return json.load(f)
        return None

    def save_session(self, session: dict):
        with open(self.session_file, "w") as f:
            json.dump(session, f)

    async def login_user(self, username: str, password: str, client: Client) -> bool:
        session = self.load_session()

        if session:
            try:
                client.set_settings(session)
                await client.login(username, password)

                try:
                    await client.get_timeline_feed()
                    logger.info("Logged in using session")
                    return True
                except LoginRequired:
                    logger.info(
                        "Session is invalid, logging in with username and password"
                    )
            except Exception as e:
                logger.info(f"Couldn't login user using session information: {e}")

        try:
            logger.info(
                f"Attempting to login via username and password. username: {username}"
            )
            if await client.login(username, password):
                self.save_session(client.get_settings())
                return True
        except Exception as e:
            logger.info(f"Couldn't login user using username and password: {e}")

        return False
