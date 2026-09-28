"""Learning statistics endpoint."""

from fastapi import APIRouter, Depends

from database import db

from ..deps import get_current_user, get_db

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
def stats(user=Depends(get_current_user), conn=Depends(get_db)):
    answered_row = conn.execute(
        """
        SELECT COUNT(*) AS n, COALESCE(SUM(a.is_correct), 0) AS c
        FROM answers a JOIN sessions s ON s.id = a.session_id
        WHERE s.user_id = ?
        """,
        (user["id"],),
    ).fetchone()
    answered = answered_row["n"]
    correct = answered_row["c"] or 0
    wrong = len(db.wrong_questions(conn, user["id"]))
    return {
        "total_questions": db.count_questions(conn),
        "answered": answered,
        "correct": correct,
        "accuracy": round(correct / answered * 100) if answered else 0,
        "wrong_count": wrong,
        "subjects": [dict(r) for r in db.subjects(conn)],
        "difficulty": db.difficulty_distribution(conn),
        "weak": [dict(r) for r in db.weak_knowledge(conn, user["id"])],
    }
