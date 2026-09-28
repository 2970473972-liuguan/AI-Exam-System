# AI Exam Training System

个人 AI 智能题库系统（V1.0）。所有题目均为 AI 原创，不复制受版权保护的真题。

## 目录

```text
AI-Exam-System/
|-- database/   SQLite 数据库与导入脚本
|-- modules/    各科目题库规划目录
|-- generator/  原创题生成器
|-- analyzer/   难度分析与错题分析
`-- interface/  命令行入口
```

## 快速开始

```bash
python interface/cli.py init
python interface/cli.py import ../cpp_100.json
python interface/cli.py stats
python interface/cli.py gen-python 10
python interface/cli.py recommend
```

数据库文件位于 `database/questions.db`。错题记录写入 `wrong_log`，知识薄弱点汇总到 `knowledge`。
