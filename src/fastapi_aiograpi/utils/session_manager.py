from typing import Optional
import logging
from sqlmodel import Session, select
from ..models.models import User
import bcrypt

logger = logging.getLogger(__name__)


class SessionStore:
    def __init__(self, session: Session):
        self.session = session

    def load_sessions(self):
        statement = select(User)
        users = self.session.exec(statement).all()
        self.sessions = {user.username: user.session for user in users}
        self.user_proxy_map = {user.username: user.proxy for user in users}
        self.passwords = {user.username: user.password for user in users}

    def save_session(
        self,
        username: str,
        session_data: dict,
        proxy: str,
        password: Optional[str] = None,
    ):
        user = self.session.exec(select(User).where(User.username == username)).first()
        if user:
            user.session = session_data
            user.proxy = proxy
            if password:
                hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
                user.password = hashed_password.decode()
        else:
            hashed_password = (
                bcrypt.hashpw(password.encode(), bcrypt.gensalt()) if password else None
            )
            user = User(
                username=username,
                session=session_data,
                proxy=proxy,
                password=hashed_password.decode() if hashed_password else None,
            )
            self.session.add(user)
        self.session.commit()

    def get_session(self, username: str) -> Optional[dict]:
        user = self.session.exec(select(User).where(User.username == username)).first()
        if user:
            return user.session
        return None

    def get_password_hash(self, username: str) -> Optional[str]:
        user = self.session.exec(select(User).where(User.username == username)).first()
        if user:
            return user.password
        return None

    def verify_password(self, username: str, password: str) -> bool:
        user_password_hash = self.get_password_hash(username)
        if user_password_hash:
            return bcrypt.checkpw(password.encode(), user_password_hash.encode())
        return False

    def get_proxy_for_user(self, username: str) -> Optional[str]:
        user = self.session.exec(select(User).where(User.username == username)).first()
        if user:
            return user.proxy
        return None
