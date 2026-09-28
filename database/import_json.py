"""Import a question bank JSON file into SQLite."""

import json

from database.db import get_conn, init_db, insert_question


def _as_list(raw):
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and isinstance(raw.get("categories"), list):
        out = []
        for cat in raw["categories"]:
            for q in cat.get("questions") or []:
                q = dict(q)
                q.setdefault("subject", cat.get("name") or cat.get("id"))
                q.setdefault("category", cat.get("name") or "")
                out.append(q)
        return out
    if isinstance(raw, dict) and isinstance(raw.get("questions"), list):
        return raw["questions"]
    return []


def import_file(path):
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    conn = get_conn()
    init_db(conn)
    added = 0
    for item in _as_list(raw):
        if insert_question(conn, item):
            added += 1
    conn.commit()
    conn.close()
    return added
