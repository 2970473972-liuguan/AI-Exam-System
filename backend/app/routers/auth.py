"""Authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from database import db

from ..deps import get_current_user, get_db
from ..schemas import LoginIn, RegisterIn, TokenOut
from ..security import hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
def register(payload: RegisterIn, conn=Depends(get_db)):
    username = payload.username.strip()
    if len(username) < 2 or len(payload.password) < 4:
        raise HTTPException(status_code=400, detail="用户名至少 2 位，密码至少 4 位")
    user_id = db.create_user(conn, username, hash_password(payload.password))
    if not user_id:
        raise HTTPException(status_code=409, detail="用户名已存在")
    return {"token": db.create_token(conn, user_id), "username": username}


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, conn=Depends(get_db)):
    user = db.get_user_by_username(conn, payload.username.strip())
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {"token": db.create_token(conn, user["id"]), "username": user["username"]}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {"id": user["id"], "username": user["username"]}
