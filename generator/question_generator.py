"""Deterministic original-question generators for simple knowledge points."""

import random


def generate_python_operators(count=10, seed=42):
    """Generate original Python arithmetic questions as unified dicts."""
    rng = random.Random(seed)
    ops = [
        ("+", lambda a, b: a + b),
        ("-", lambda a, b: a - b),
        ("*", lambda a, b: a * b),
        ("//", lambda a, b: a // b),
        ("%", lambda a, b: a % b),
        ("**", lambda a, b: a ** b),
    ]
    questions = []
    for i in range(count):
        symbol, func = ops[i % len(ops)]
        a = rng.randint(2, 30)
        b = rng.randint(2, 5)
        if symbol in ("//", "%"):
            b = rng.randint(2, 9)
            a = a - (a % b)
            if a == 0:
                a = b
        value = func(a, b)
        distractors = []
        for delta in (1, -1, 2):
            candidate = value + delta
            if candidate != value and candidate not in distractors:
                distractors.append(candidate)
        options = [str(value)] + [str(d) for d in distractors]
        rng.shuffle(options)
        questions.append(
            {
                "id": f"py-op-{i + 1:04d}",
                "subject": "Python",
                "category": "基础语法",
                "type": "单选",
                "difficulty": 1,
                "question": f"Python 中表达式 {a} {symbol} {b} 的值是？",
                "options": options,
                "answer": str(value),
                "analysis": f"{a} {symbol} {b} 的运算结果是 {value}。",
                "knowledge_points": ["运算符"],
                "source": "AI原创",
            }
        )
    return questions
