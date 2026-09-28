"""Canonical SQLite storage layer for the AI exam training system."""

import json
import os
import secrets
import sqlite3
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")
DB_PATH = os.path.join(BASE_DIR, "questions.db")


def get_conn(path=None):
    conn = sqlite3.connect(path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn=None):
    owns = conn is None
    conn = conn or get_conn()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        conn.executescript(fh.read())
    conn.commit()
    if owns:
        conn.close()


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def parse_difficulty(value):
    if isinstance(value, int):
        return max(1, min(5, value))
    text = str(value or "1")
    digits = "".join(ch for ch in text if ch.isdigit())
    if digits:
        return max(1, min(5, int(digits)))
    return 1


def normalize_question(raw):
    options = raw.get("options") or []
    if not isinstance(options, list):
        options = []
    answer = raw.get("answer")
    if isinstance(answer, int):
        answer = options[answer] if 0 <= answer < len(options) else ""
    elif answer is None:
        answer = ""
    else:
        answer = str(answer)
    knowledge = raw.get("knowledge_points") or raw.get("knowledge") or []
    if isinstance(knowledge, str):
        knowledge = [knowledge]
    analysis = str(raw.get("analysis") or "")
    if raw.get("mistakes"):
        analysis = f"{analysis} 易错：{raw.get('mistakes')}".strip()
    source = str(raw.get("source") or raw.get("source_type") or "AI原创")
    if source in ("原创生成", ""):
        source = "AI原创"
    return {
        "id": str(raw.get("id") or ""),
        "subject": str(raw.get("subject") or ""),
        "category": str(raw.get("category") or ""),
        "type": str(raw.get("type") or "单选"),
        "difficulty": parse_difficulty(raw.get("difficulty")),
        "question": str(raw.get("question") or ""),
        "options": json.dumps(options, ensure_ascii=False),
        "answer": answer,
        "analysis": analysis,
        "knowledge_points": json.dumps([str(k) for k in knowledge], ensure_ascii=False),
        "source": source,
        "create_time": str(raw.get("create_time") or now_iso()),
    }


def insert_question(conn, raw):
    q = normalize_question(raw)
    if not q["id"] or not q["question"]:
        return False
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO questions
        (id, subject, category, type, difficulty, question, options, answer,
         analysis, knowledge_points, source, create_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            q["id"], q["subject"], q["category"], q["type"], q["difficulty"],
            q["question"], q["options"], q["answer"], q["analysis"],
            q["knowledge_points"], q["source"], q["create_time"],
        ),
    )
    return cur.rowcount == 1


def count_questions(conn, subject=None):
    if subject:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM questions WHERE subject = ?", (subject,)
        ).fetchone()
    else:
        row = conn.execute("SELECT COUNT(*) AS n FROM questions").fetchone()
    return row["n"]


# ---------- users and auth ----------

def create_user(conn, username, password_hash):
    now = now_iso()
    try:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, password_hash, now),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None


def get_user_by_username(conn, username):
    return conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()


def get_user_by_id(conn, user_id):
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def create_token(conn, user_id):
    token = secrets.token_urlsafe(32)
    conn.execute(
        "INSERT INTO tokens (token, user_id, created_at) VALUES (?, ?, ?)",
        (token, user_id, now_iso()),
    )
    conn.commit()
    return token


def get_user_by_token(conn, token):
    row = conn.execute(
        "SELECT users.* FROM tokens JOIN users ON users.id = tokens.user_id WHERE tokens.token = ?",
        (token,),
    ).fetchone()
    return row


# ---------- questions ----------

def list_questions(conn, subject=None, category=None, difficulty=None, limit=20, offset=0):
    sql = "SELECT * FROM questions WHERE 1=1"
    params = []
    if subject:
        sql += " AND subject = ?"
        params.append(subject)
    if category:
        sql += " AND category = ?"
        params.append(category)
    if difficulty:
        sql += " AND difficulty = ?"
        params.append(int(difficulty))
    sql += " ORDER BY id LIMIT ? OFFSET ?"
    params.extend([int(limit), int(offset)])
    return conn.execute(sql, params).fetchall()


def get_question(conn, qid):
    return conn.execute("SELECT * FROM questions WHERE id = ?", (qid,)).fetchone()


def subjects(conn):
    return conn.execute(
        "SELECT subject, COUNT(*) AS n, MIN(difficulty) AS min_d, MAX(difficulty) AS max_d "
        "FROM questions GROUP BY subject ORDER BY subject"
    ).fetchall()


def difficulty_distribution(conn):
    rows = conn.execute(
        "SELECT subject, difficulty, COUNT(*) AS n FROM questions "
        "GROUP BY subject, difficulty ORDER BY subject, difficulty"
    ).fetchall()
    result = {}
    for row in rows:
        result.setdefault(row["subject"], {})[row["difficulty"]] = row["n"]
    return result


# ---------- practice sessions ----------

def create_session(conn, user_id, subject, mode, question_ids):
    session_id = secrets.token_urlsafe(16)
    conn.execute(
        "INSERT INTO sessions (id, user_id, subject, mode, total, score, created_at) "
        "VALUES (?, ?, ?, ?, ?, 0, ?)",
        (session_id, user_id, subject or "", mode, len(question_ids), now_iso()),
    )
    conn.commit()
    return session_id


def get_session(conn, session_id):
    return conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()


def record_answer(conn, session_id, question_id, chosen, is_correct):
    conn.execute(
        "INSERT INTO answers (session_id, question_id, chosen, is_correct, answered_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (session_id, question_id, chosen, 1 if is_correct else 0, now_iso()),
    )
    if is_correct:
        conn.execute(
            "UPDATE sessions SET score = score + 1 WHERE id = ?", (session_id,)
        )
    conn.commit()


def session_answers(conn, session_id):
    return conn.execute(
        "SELECT * FROM answers WHERE session_id = ? ORDER BY id", (session_id,)
    ).fetchall()


# ---------- wrong answers ----------

def record_wrong(conn, user_id, question_id, chosen):
    conn.execute(
        "INSERT INTO wrong_log (user_id, question_id, chosen, wrong_at) VALUES (?, ?, ?, ?)",
        (user_id, question_id, chosen, now_iso()),
    )
    conn.execute(
        "UPDATE questions SET wrong_count = wrong_count + 1 WHERE id = ?", (question_id,)
    )
    row = conn.execute(
        "SELECT subject, knowledge_points FROM questions WHERE id = ?", (question_id,)
    ).fetchone()
    if row:
        for point in json.loads(row["knowledge_points"] or "[]"):
            conn.execute(
                """
                INSERT INTO knowledge (user_id, subject, knowledge_point, wrong_count)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(user_id, subject, knowledge_point)
                DO UPDATE SET wrong_count = wrong_count + 1
                """,
                (user_id, row["subject"], point),
            )
    conn.commit()


def wrong_questions(conn, user_id):
    return conn.execute(
        """
        SELECT questions.*, MAX(wrong_log.wrong_at) AS last_wrong_at
        FROM wrong_log JOIN questions ON questions.id = wrong_log.question_id
        WHERE wrong_log.user_id = ?
        GROUP BY questions.id
        ORDER BY last_wrong_at DESC
        """,
        (user_id,),
    ).fetchall()


def weak_knowledge(conn, user_id):
    return conn.execute(
        """
        SELECT subject, knowledge_point, wrong_count
        FROM knowledge WHERE user_id = ?
        ORDER BY wrong_count DESC, subject, knowledge_point
        """,
        (user_id,),
    ).fetchall()


# ---------- refresh ----------

def log_refresh(conn, subject, mode, generated):
    conn.execute(
        "INSERT INTO refresh_log (subject, mode, generated, created_at) VALUES (?, ?, ?, ?)",
        (subject, mode, generated, now_iso()),
    )
    conn.commit()


def refresh_log(conn, limit=20):
    return conn.execute(
        "SELECT * FROM refresh_log ORDER BY id DESC LIMIT ?", (int(limit),)
    ).fetchall()
