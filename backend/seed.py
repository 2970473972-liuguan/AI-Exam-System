"""Seed the database with the existing original C++ question bank."""

import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from database import db


def seed_cpp(path=None):
    db.init_db()
    if path is None:
        path = os.path.join(os.path.dirname(PROJECT_ROOT), "cpp_100.json")
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    conn = db.get_conn()
    added = 0
    for item in raw:
        if db.insert_question(conn, item):
            added += 1
    conn.commit()
    conn.close()
    return added


if __name__ == "__main__":
    print("seeded", seed_cpp())
