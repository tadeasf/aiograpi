import json
import os
from typing import Dict, Optional
from datetime import datetime, timedelta


class SessionStore:
    def __init__(self, storage_dir: str = "sessions"):
        self.storage_dir = storage_dir
        self.sessions: Dict[str, Dict] = {}
        self.user_proxy_map: Dict[str, str] = {}
        self.proxy_user_count: Dict[str, int] = {}
        self.passwords: Dict[str, str] = {}  # Added for storing passwords
        os.makedirs(storage_dir, exist_ok=True)
        self.load_sessions()

    def load_sessions(self):
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                username = filename[:-5]
                with open(os.path.join(self.storage_dir, filename), "r") as f:
                    data = json.load(f)
                    self.sessions[username] = data["session"]
                    self.user_proxy_map[username] = data["proxy"]
                    self.proxy_user_count[data["proxy"]] = (
                        self.proxy_user_count.get(data["proxy"], 0) + 1
                    )
                    if "password" in data:  # Load password if it exists
                        self.passwords[username] = data["password"]

    def save_session(
        self, username: str, session: Dict, proxy: str, password: Optional[str] = None
    ):
        self.sessions[username] = session
        self.user_proxy_map[username] = proxy
        self.proxy_user_count[proxy] = self.proxy_user_count.get(proxy, 0) + 1
        if password:
            self.passwords[username] = password
        with open(os.path.join(self.storage_dir, f"{username}.json"), "w") as f:
            data = {
                "session": session,
                "proxy": proxy,
                "timestamp": datetime.now().isoformat(),
            }
            if password:
                data["password"] = password
            json.dump(data, f)

    def get_session(self, username: str) -> Optional[Dict]:
        session_file = os.path.join(self.storage_dir, f"{username}.json")
        if os.path.exists(session_file):
            with open(session_file, "r") as f:
                data = json.load(f)
                timestamp = datetime.fromisoformat(data["timestamp"])
                if datetime.now() - timestamp < timedelta(hours=24):
                    return data["session"]
        return None

    def update_session(self, username: str, session: Dict):
        existing_data = self.get_session(username)
        if existing_data:
            proxy = self.get_proxy_for_user(username)
            self.save_session(username, session, proxy)
        else:
            raise Exception(f"No existing session found for user {username}")

    def get_password(self, username: str) -> Optional[str]:
        return self.passwords.get(username)

    def get_proxy_for_user(self, username: str) -> Optional[str]:
        return self.user_proxy_map.get(username)

    def assign_proxy(self, username: str, proxy: str):
        self.user_proxy_map[username] = proxy
        self.proxy_user_count[proxy] = self.proxy_user_count.get(proxy, 0) + 1


session_store = SessionStore()
