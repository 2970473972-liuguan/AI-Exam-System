"""Request and response schemas."""

from pydantic import BaseModel


class RegisterIn(BaseModel):
    username: str
    password: str


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    token: str
    username: str


class StartPracticeIn(BaseModel):
    subject: str = ""
    mode: str = "practice"
    count: int = 10


class AnswerIn(BaseModel):
    session_id: str
    question_id: str
    chosen: str


class RefreshIn(BaseModel):
    subject: str = "C++"
    count: int = 20
