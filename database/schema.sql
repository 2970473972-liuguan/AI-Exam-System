PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS tokens (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    subject TEXT NOT NULL,
    category TEXT DEFAULT '',
    type TEXT DEFAULT '单选',
    difficulty INTEGER DEFAULT 1,
    question TEXT NOT NULL,
    options TEXT DEFAULT '[]',
    answer TEXT DEFAULT '',
    analysis TEXT DEFAULT '',
    knowledge_points TEXT DEFAULT '[]',
    source TEXT DEFAULT 'AI原创',
    create_time TEXT,
    wrong_count INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS wrong_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    question_id TEXT NOT NULL,
    chosen TEXT DEFAULT '',
    wrong_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS knowledge (
    user_id INTEGER NOT NULL,
    subject TEXT NOT NULL,
    knowledge_point TEXT NOT NULL,
    wrong_count INTEGER DEFAULT 0,
    last_trained_at TEXT,
    PRIMARY KEY (user_id, subject, knowledge_point),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    subject TEXT DEFAULT '',
    mode TEXT DEFAULT 'practice',
    total INTEGER DEFAULT 0,
    score INTEGER DEFAULT 0,
    created_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    chosen TEXT DEFAULT '',
    is_correct INTEGER DEFAULT 0,
    answered_at TEXT,
    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS refresh_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT DEFAULT '',
    mode TEXT DEFAULT 'manual',
    generated INTEGER DEFAULT 0,
    created_at TEXT
);
