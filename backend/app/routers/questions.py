"""Question browsing endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from database import db

from ..deps import get_current_user, get_db
from ..serializers import question_dict

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.get("")
def list_questions(
    subject: str = "",
    category: str = "",
    difficulty: int = 0,
    limit: int = 20,
    offset: int = 0,
    user=Depends(get_current_user),
    conn=Depends(get_db),
):
    rows = db.list_questions(
        conn, subject or None, category or None, difficulty or None, min(limit, 100), offset
    )
    return [question_dict(r, include_answer=True) for r in rows]


@router.get("/subjects")
def list_subjects(conn=Depends(get_db)):
    return [dict(r) for r in db.subjects(conn)]


@router.get("/{qid}")
def get_one(qid: str, conn=Depends(get_db)):
    row = db.get_question(conn, qid)
    if not row:
        raise HTTPException(status_code=404, detail="题目不存在")
    return question_dict(row, include_answer=True)
