"""End-to-end API smoke test for the Phase 1 loop."""

import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient

from app.main import app


def run():
    with TestClient(app) as client:
        r = client.post(
            "/api/auth/register", json={"username": "tester", "password": "pass1234"}
        )
        assert r.status_code == 200, r.text
        token = r.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        r = client.get("/api/questions/subjects", headers=headers)
        assert r.status_code == 200
        print("subjects:", r.json())

        r = client.post(
            "/api/practice/start", json={"subject": "C++", "count": 5}, headers=headers
        )
        assert r.status_code == 200, r.text
        body = r.json()
        session_id = body["session_id"]
        questions = body["questions"]
        assert len(questions) == 5
        assert "answer" not in questions[0], "answers must not leak before answering"
        print("started practice:", session_id, "questions:", len(questions))

        r = client.post(
            "/api/practice/answer",
            json={"session_id": session_id, "question_id": questions[0]["id"], "chosen": "__none__"},
            headers=headers,
        )
        print("wrong answer:", r.json()["is_correct"], r.json()["correct_answer"])

        full = client.get(f"/api/questions/{questions[1]['id']}", headers=headers).json()
        r = client.post(
            "/api/practice/answer",
            json={
                "session_id": session_id,
                "question_id": questions[1]["id"],
                "chosen": full["answer"],
            },
            headers=headers,
        )
        print("correct answer:", r.json()["is_correct"])

        r = client.get("/api/wrong", headers=headers)
        print("wrong book size:", len(r.json()))
        assert len(r.json()) == 1

        r = client.get("/api/wrong/recommend", headers=headers)
        print("weak points:", r.json())

        r = client.get("/api/stats", headers=headers)
        print("stats:", {k: r.json()[k] for k in ("answered", "correct", "accuracy")})

        r = client.get(f"/api/practice/session/{session_id}", headers=headers)
        print("session score:", r.json()["score"], "/", r.json()["total"])
        assert r.json()["score"] == 1

        r = client.post(
            "/api/admin/refresh", json={"subject": "C++", "count": 20}, headers=headers
        )
        print("manual refresh:", r.json())

        r = client.get("/api/admin/refresh-log", headers=headers)
        print("refresh log entries:", len(r.json()))


if __name__ == "__main__":
    run()
    print("ALL PHASE 1 API TESTS PASSED")
