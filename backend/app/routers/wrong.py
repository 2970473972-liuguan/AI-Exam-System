"""Wrong-answer endpoints."""

from fastapi import APIRouter, Depends

from database import db

from ..deps import get_current_user, get_db
from ..serializers import question_dict

router = APIRouter(prefix="/api/wrong", tags=["wrong"])


@router.get("")
def wrong_questions(user=Depends(get_current_user), conn=Depends(get_db)):
    return [question_dict(r, include_answer=True) for r in db.wrong_questions(conn, user["id"])]


@router.get("/recommend")
def recommend(user=Depends(get_current_user), conn=Depends(get_db)):
    return [dict(r) for r in db.weak_knowledge(conn, user["id"])]


@router.delete("/{qid}")
def remove_wrong(qid: str, user=Depends(get_current_user), conn=Depends(get_db)):
    conn.execute(
        "DELETE FROM wrong_log WHERE user_id = ? AND question_id = ?", (user["id"], qid)
    )
    conn.commit()
    return {"ok": True}
