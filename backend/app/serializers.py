"""Convert SQLite rows to JSON-friendly dicts."""

import json


def question_dict(row, include_answer=True):
    data = dict(row)
    data["options"] = json.loads(data.get("options") or "[]")
    data["knowledge_points"] = json.loads(data.get("knowledge_points") or "[]")
    if not include_answer:
        data.pop("answer", None)
        data.pop("analysis", None)
    return data
