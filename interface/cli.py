"""Command-line interface for the AI exam training system."""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.difficulty import difficulty_distribution
from analyzer.wrong_analysis import recommend
from database.db import get_conn, init_db, insert_question, record_wrong
from database.import_json import import_file
from generator.question_generator import generate_python_operators


def main(argv=None):
    parser = argparse.ArgumentParser(prog="exam-system", description="AI 题库系统")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="初始化数据库")

    p_import = sub.add_parser("import", help="导入题库 JSON")
    p_import.add_argument("path")

    sub.add_parser("stats", help="查看题目统计")

    p_wrong = sub.add_parser("wrong", help="记录一道错题")
    p_wrong.add_argument("question_id")
    p_wrong.add_argument("--chosen", default="", help="用户选择的答案")

    sub.add_parser("recommend", help="查看薄弱知识点")

    p_gen = sub.add_parser("gen-python", help="生成 Python 基础运算符原创题")
    p_gen.add_argument("count", nargs="?", type=int, default=10)

    args = parser.parse_args(argv)

    if args.command == "init":
        init_db()
        print("数据库已初始化")
    elif args.command == "import":
        added = import_file(args.path)
        print(f"导入完成，新增 {added} 道题")
    elif args.command == "stats":
        print(json.dumps(difficulty_distribution(), ensure_ascii=False, indent=2))
    elif args.command == "wrong":
        conn = get_conn()
        record_wrong(conn, args.question_id, args.chosen)
        conn.close()
        print(f"已记录错题 {args.question_id}")
    elif args.command == "recommend":
        print(json.dumps(recommend(), ensure_ascii=False, indent=2))
    elif args.command == "gen-python":
        conn = get_conn()
        init_db(conn)
        added = 0
        for q in generate_python_operators(args.count):
            if insert_question(conn, q):
                added += 1
        conn.commit()
        conn.close()
        print(f"已生成并保存 {added} 道 Python 原创题")


if __name__ == "__main__":
    main(sys.argv[1:])
