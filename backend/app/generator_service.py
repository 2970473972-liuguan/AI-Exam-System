"""Question generation service.

LLM providers (OpenAI, DeepSeek, Ollama) are configured through LLM_PROVIDER.
Until a provider is wired up, a deterministic fallback produces original
questions locally so the full loop can be verified without external services.
"""

import hashlib
import random

from database import db


def _qid(subject, question):
    digest = hashlib.sha1(f"{subject}|{question}".encode("utf-8")).hexdigest()
    return f"ai-{digest[:14]}"


def _options(correct, distractors, rng):
    opts = [str(correct)]
    for item in distractors:
        value = str(item)
        if value not in opts:
            opts.append(value)
    extra = 1
    while len(opts) < 4:
        value = str(correct + extra)
        if value not in opts:
            opts.append(value)
        extra += 1
    rng.shuffle(opts)
    return opts


def _concept_templates():
    return [
        {
            "category": "基础语法",
            "type": "单选",
            "difficulty": 1,
            "question": "每个 C++ 程序从哪个函数开始执行？",
            "options": ["main()", "start()", "run()", "init()"],
            "answer": "main()",
            "analysis": "C++ 程序的入口是 main 函数，程序启动后从 main 开始执行。",
            "knowledge_points": ["程序入口"],
        },
        {
            "category": "指针",
            "type": "单选",
            "difficulty": 1,
            "question": "指针变量中存储的内容是？",
            "options": ["变量的地址", "变量的值", "变量的类型", "变量的名称"],
            "answer": "变量的地址",
            "analysis": "指针保存的是另一个对象的内存地址。",
            "knowledge_points": ["指针"],
        },
        {
            "category": "引用",
            "type": "单选",
            "difficulty": 1,
            "question": "语句 int& r = x; 中 r 是？",
            "options": ["x 的别名", "x 的副本", "指针", "常量"],
            "answer": "x 的别名",
            "analysis": "引用是已有变量的别名，r 与 x 指向同一存储空间。",
            "knowledge_points": ["引用"],
        },
        {
            "category": "类与对象",
            "type": "单选",
            "difficulty": 2,
            "question": "类 class 的成员默认访问权限是？",
            "options": ["private", "public", "protected", "friend"],
            "answer": "private",
            "analysis": "class 默认成员为 private，体现封装性。",
            "knowledge_points": ["访问控制"],
        },
        {
            "category": "类与对象",
            "type": "单选",
            "difficulty": 2,
            "question": "结构体 struct 的成员默认访问权限是？",
            "options": ["public", "private", "protected", "friend"],
            "answer": "public",
            "analysis": "struct 默认成员为 public。",
            "knowledge_points": ["访问控制"],
        },
        {
            "category": "继承",
            "type": "单选",
            "difficulty": 2,
            "question": "class B : public A 中的 public 表示？",
            "options": ["继承方式", "返回类型", "成员类型", "构造方式"],
            "answer": "继承方式",
            "analysis": "public 是继承方式，决定基类成员在派生类中的可见性。",
            "knowledge_points": ["继承方式"],
        },
        {
            "category": "多态",
            "type": "单选",
            "difficulty": 2,
            "question": "声明虚函数使用的关键字是？",
            "options": ["virtual", "static", "const", "friend"],
            "answer": "virtual",
            "analysis": "virtual 声明虚函数，是实现运行时多态的基础。",
            "knowledge_points": ["虚函数"],
        },
        {
            "category": "多态",
            "type": "单选",
            "difficulty": 2,
            "question": "声明纯虚函数的写法是？",
            "options": ["= 0", "= null", "{}", "default"],
            "answer": "= 0",
            "analysis": "纯虚函数形如 virtual void f() = 0;，使类成为抽象类。",
            "knowledge_points": ["纯虚函数"],
        },
        {
            "category": "STL",
            "type": "单选",
            "difficulty": 2,
            "question": "std::map 的底层通常采用的数据结构是？",
            "options": ["红黑树", "哈希表", "链表", "栈"],
            "answer": "红黑树",
            "analysis": "std::map 通常是平衡二叉搜索树（红黑树），按键有序。",
            "knowledge_points": ["map"],
        },
        {
            "category": "STL",
            "type": "单选",
            "difficulty": 2,
            "question": "std::vector 在末尾添加元素应使用？",
            "options": ["push_back", "append", "add", "insert"],
            "answer": "push_back",
            "analysis": "push_back 在 vector 末尾追加元素。",
            "knowledge_points": ["vector"],
        },
        {
            "category": "内存管理",
            "type": "单选",
            "difficulty": 2,
            "question": "运算符 new 分配的动态内存位于？",
            "options": ["堆区", "栈区", "静态区", "代码区"],
            "answer": "堆区",
            "analysis": "new 在堆上分配内存，需用 delete 手动释放。",
            "knowledge_points": ["动态内存"],
        },
        {
            "category": "内存管理",
            "type": "单选",
            "difficulty": 2,
            "question": "使用 new[] 分配的数组，释放时应使用？",
            "options": ["delete[]", "delete", "free", "不需要释放"],
            "answer": "delete[]",
            "analysis": "new[] 与 delete[] 必须成对使用。",
            "knowledge_points": ["数组释放"],
        },
        {
            "category": "智能指针",
            "type": "单选",
            "difficulty": 3,
            "question": "std::unique_ptr 的特点是？",
            "options": ["独占所有权且不可拷贝", "可被多个指针共享", "无需释放内存", "必须手动 delete"],
            "answer": "独占所有权且不可拷贝",
            "analysis": "unique_ptr 独占对象所有权，只可移动不可拷贝。",
            "knowledge_points": ["unique_ptr"],
        },
        {
            "category": "算法",
            "type": "单选",
            "difficulty": 3,
            "question": "使用 std::sort 排序需要包含的头文件是？",
            "options": ["<algorithm>", "<sort>", "<vector>", "<utility>"],
            "answer": "<algorithm>",
            "analysis": "std::sort 定义在 <algorithm> 头文件中。",
            "knowledge_points": ["算法库"],
        },
    ]


def _numeric_generators():
    def precedence(rng):
        a, b, c = rng.randint(2, 9), rng.randint(2, 9), rng.randint(2, 9)
        value = a + b * c
        return {
            "category": "基础语法",
            "type": "单选",
            "difficulty": 1,
            "question": f"表达式 {a} + {b} * {c} 的值是？",
            "options": _options(value, [value + 1, value - 1, (a + b) * c], rng),
            "answer": str(value),
            "analysis": f"先算 {b} * {c} = {b * c}，再算 {a} + {b * c} = {value}。",
            "knowledge_points": ["运算符优先级"],
        }

    def modulo(rng):
        a = rng.randint(11, 50)
        b = rng.randint(2, 9)
        value = a % b
        return {
            "category": "基础语法",
            "type": "单选",
            "difficulty": 1,
            "question": f"表达式 {a} % {b} 的值是？",
            "options": _options(value, [value + 1, value - 1, a // b], rng),
            "answer": str(value),
            "analysis": f"{a} 除以 {b} 的余数是 {value}。",
            "knowledge_points": ["取余运算"],
        }

    def integer_division(rng):
        b = rng.randint(2, 9)
        a = b * rng.randint(2, 9)
        value = a // b
        return {
            "category": "基础语法",
            "type": "单选",
            "difficulty": 1,
            "question": f"整数除法表达式 {a} / {b} 的值是？",
            "options": _options(value, [value + 1, value - 1, value + 2], rng),
            "answer": str(value),
            "analysis": f"两个 int 相除为整数除法，{a} / {b} = {value}。",
            "knowledge_points": ["整数除法"],
        }

    def loop(rng):
        n = rng.randint(2, 8)
        return {
            "category": "流程控制",
            "type": "单选",
            "difficulty": 1,
            "question": f"循环 for(int i = 0; i < {n}; i++) 的循环体执行几次？",
            "options": _options(n, [n - 1, n + 1, 0], rng),
            "answer": str(n),
            "analysis": f"i 依次取 0 到 {n - 1}，共执行 {n} 次。",
            "knowledge_points": ["for 循环"],
        }

    def compound_assign(rng):
        a = rng.randint(2, 9)
        b = rng.randint(2, 9)
        value = a * b
        return {
            "category": "基础语法",
            "type": "单选",
            "difficulty": 1,
            "question": f"int x = {a}; x *= {b}; 之后 x 的值是？",
            "options": _options(value, [value + 1, value - 1, value + 2], rng),
            "answer": str(value),
            "analysis": f"x *= {b} 等价于 x = x * {b}，结果为 {value}。",
            "knowledge_points": ["复合赋值"],
        }

    def array_index(rng):
        n = rng.randint(3, 8)
        return {
            "category": "数组",
            "type": "单选",
            "difficulty": 1,
            "question": f"数组 int a[{n}]; 的最后一个元素下标是？",
            "options": _options(n - 1, [n, n - 2, 0], rng),
            "answer": str(n - 1),
            "analysis": f"数组下标从 0 开始，长度为 {n} 时最后一个下标为 {n - 1}。",
            "knowledge_points": ["数组下标"],
        }

    return [precedence, modulo, integer_division, loop, compound_assign, array_index]


def generate_fallback(subject, count):
    rng = random.Random()
    out = []
    for template in _concept_templates():
        question = {**template, "subject": subject, "source": "AI原创"}
        question["id"] = _qid(subject, question["question"])
        out.append(question)

    seen = {q["question"] for q in out}
    attempts = 0
    while len(out) < count and attempts < count * 6:
        attempts += 1
        generator = rng.choice(_numeric_generators())
        question = generator(rng)
        question = {**question, "subject": subject, "source": "AI原创"}
        question["id"] = _qid(subject, question["question"])
        if question["question"] not in seen:
            seen.add(question["question"])
            out.append(question)
    return out[:count]


def generate_and_save(conn, subject, count):
    subject = subject or "C++"
    items = generate_fallback(subject, count)
    added = 0
    for item in items:
        if db.insert_question(conn, item):
            added += 1
    conn.commit()
    return added
