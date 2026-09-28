"""Wrong-answer analysis and weak-point recommendations."""

from database.db import get_conn


def recommend(conn=None):
    owns = conn is None
    conn = conn or get_conn()
    rows = conn.execute(
        """
        SELECT subject, knowledge_point, wrong_count
        FROM knowledge
        ORDER BY wrong_count DESC, subject, knowledge_point
        """
    ).fetchall()
    if owns:
        conn.close()
    return [dict(row) for row in rows]


def recommend_questions(conn, subject, limit=5):
    """Pick the questions whose knowledge points are weakest for a subject."""
    weak = conn.execute(
        "SELECT knowledge_point, wrong_count FROM knowledge WHERE subject = ? ORDER BY wrong_count DESC",
        (subject,),
    ).fetchall()
    if not weak:
        return []
    points = [row["knowledge_point"] for row in weak]
    placeholders = ",".join("?" for _ in points)
    rows = conn.execute(
        f"""
        SELECT id FROM questions
        WHERE subject = ? AND knowledge_points != '[]'
        ORDER BY wrong_count DESC, id
        LIMIT ?
        """,
        (subject, limit),
    ).fetchall()
    return [row["id"] for row in rows]
