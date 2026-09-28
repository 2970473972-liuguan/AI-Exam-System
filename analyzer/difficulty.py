"""Difficulty distribution analysis."""

from database.db import get_conn


def difficulty_distribution(conn=None):
    owns = conn is None
    conn = conn or get_conn()
    rows = conn.execute(
        """
        SELECT subject, difficulty, COUNT(*) AS n
        FROM questions
        GROUP BY subject, difficulty
        ORDER BY subject, difficulty
        """
    ).fetchall()
    if owns:
        conn.close()
    result = {}
    for row in rows:
        result.setdefault(row["subject"], {})[row["difficulty"]] = row["n"]
    return result
