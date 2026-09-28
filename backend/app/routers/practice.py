"""Practice session endpoints."""

import random

from fastapi import APIRouter, Depends, HTTPException

from database import db

from ..deps import get_current_user, get_db
from ..schemas import AnswerIn, StartPracticeIn
from ..serializers import question_dict

router = APIRouter(prefix="/api/practice", tags=["practice"])


@router.post("/start")
def start(payload: StartPracticeIn, user=Depends(get_current_user), conn=Depends(get_db)):
    rows = db.list_questions(conn, payload.subject or None, None, None, 500, 0)
    if not rows:
        raise HTTPException(status_code=404, detail="该科目暂无题目")
    chosen = random.sample(rows, min(max(1, payload.count), len(rows)))
    session_id = db.create_session(
        conn, user["id"], payload.subject, payload.mode, [r["id"] for r in chosen]
    )
    return {
        "session_id": session_id,
        "questions": [question_dict(r, include_answer=False) for r in chosen],
    }


@router.post("/answer")
def answer(payload: AnswerIn, user=Depends(get_current_user), conn=Depends(get_db)):
    session = db.get_session(conn, payload.session_id)
    if not session or session["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="会话不存在")
    q = db.get_question(conn, payload.question_id)
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")
    is_correct = payload.chosen == q["answer"]
    db.record_answer(conn, session["id"], payload.question_id, payload.chosen, is_correct)
    if not is_correct:
        db.record_wrong(conn, user["id"], payload.question_id, payload.chosen)
    return {
        "is_correct": is_correct,
        "correct_answer": q["answer"],
        "analysis": q["analysis"],
    }


@router.get("/session/{sid}")
def session_result(sid: str, user=Depends(get_current_user), conn=Depends(get_db)):
    session = db.get_session(conn, sid)
    if not session or session["user_id"] != user["id"]:
        raise HTTPException(status_code=404, detail="会话不存在")
    items = []
    for ans in db.session_answers(conn, sid):
        q = db.get_question(conn, ans["question_id"])
        if not q:
            continue
        items.append(
            {
                "question_id": q["id"],
                "question": q["question"],
                "chosen": ans["chosen"],
                "correct_answer": q["answer"],
                "is_correct": bool(ans["is_correct"]),
                "analysis": q["analysis"],
            }
        )
    return {
        "session_id": sid,
        "subject": session["subject"],
        "mode": session["mode"],
        "score": session["score"],
        "total": session["total"],
        "answers": items,
    }
