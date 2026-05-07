from typing import Optional
from fastapi import Request
from passlib.hash import pbkdf2_sha256
from sqlalchemy.orm import Session
from . import models


SESSION_KEY = "user_id"


def hash_password(password: str) -> str:
    return pbkdf2_sha256.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pbkdf2_sha256.verify(password, password_hash)


def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_current_user(request: Request, db: Session) -> Optional[models.User]:
    user_id = request.session.get(SESSION_KEY)
    if not user_id:
        return None
    return db.query(models.User).filter(models.User.id == user_id).first()


def require_admin(user: models.User) -> bool:
    return user.role == "admin"