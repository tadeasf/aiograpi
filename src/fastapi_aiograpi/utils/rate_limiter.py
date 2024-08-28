from fastapi import HTTPException
from datetime import datetime, timedelta
from collections import defaultdict


class RateLimiter:
    def __init__(self, requests_per_minute: int = 5):
        self.requests_per_minute = requests_per_minute
        self.user_requests = defaultdict(list)

    def check_rate_limit(self, username: str):
        now = datetime.now()
        user_reqs = self.user_requests[username]
        user_reqs = [req for req in user_reqs if now - req < timedelta(minutes=1)]
        self.user_requests[username] = user_reqs

        if len(user_reqs) >= self.requests_per_minute:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        self.user_requests[username].append(now)


rate_limiter = RateLimiter()
