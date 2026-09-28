"""Shared FastAPI dependencies."""

from fastapi import Depends, Header, HTTPException

from database import db


def get_db():
    conn = db.get_conn()
    try:
        yield conn
    finally:
        conn.close()


def get_current_user(authorization: str = Header(default=""), conn=Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    user = db.get_user_by_token(conn, authorization[7:])
    if not user:
        raise HTTPException(status_code=401, detail="登录已失效")
    return user
