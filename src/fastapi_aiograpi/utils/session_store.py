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

    def save_session(self, username: str, session: Dict, proxy: str):
        self.sessions[username] = session
        self.user_proxy_map[username] = proxy
        self.proxy_user_count[proxy] = self.proxy_user_count.get(proxy, 0) + 1
        with open(os.path.join(self.storage_dir, f"{username}.json"), "w") as f:
            json.dump(
                {
                    "session": session,
                    "proxy": proxy,
                    "timestamp": datetime.now().isoformat(),
                },
                f,
            )

    def get_session(self, username: str) -> Optional[Dict]:
        session_file = os.path.join(self.storage_dir, f"{username}.json")
        if os.path.exists(session_file):
            with open(session_file, "r") as f:
                data = json.load(f)
                timestamp = datetime.fromisoformat(data["timestamp"])
                if datetime.now() - timestamp < timedelta(hours=24):
                    return data["session"]
        return None

    def get_proxy_for_user(self, username: str) -> Optional[str]:
        return self.user_proxy_map.get(username)

    def assign_proxy(self, username: str, available_proxies: list) -> str:
        for proxy in available_proxies:
            if self.proxy_user_count.get(proxy, 0) < 5:
                self.user_proxy_map[username] = proxy
                self.proxy_user_count[proxy] = self.proxy_user_count.get(proxy, 0) + 1
                return proxy
        raise Exception("No available proxies")


session_store = SessionStore()
