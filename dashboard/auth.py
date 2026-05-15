from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException, status
from pwdlib import PasswordHash
from sqlmodel import Session, select

from dashboard.models import User


password_hash = PasswordHash.recommended()


class AuthService:
    def __init__(self, engine, secret: str):
        self.engine = engine
        self.secret = secret

    def bootstrap_admin(self, password: str) -> None:
        with Session(self.engine) as session:
            user = session.exec(select(User).where(User.username == "admin")).first()
            if user is None:
                session.add(User(username="admin", password_hash=password_hash.hash(password), is_admin=True))
                session.commit()

    def authenticate(self, username: str, password: str) -> User | None:
        with Session(self.engine) as session:
            user = session.exec(select(User).where(User.username == username)).first()
            if user is None or not password_hash.verify(password, user.password_hash):
                return None
            return user

    def create_token(self, user: User) -> str:
        payload = {
            "sub": user.username,
            "is_admin": user.is_admin,
            "exp": datetime.now(UTC) + timedelta(hours=8),
        }
        return jwt.encode(payload, self.secret, algorithm="HS256")

    def require_user(self, authorization: str | None) -> dict:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        try:
            return jwt.decode(authorization.split(" ", 1)[1], self.secret, algorithms=["HS256"])
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
