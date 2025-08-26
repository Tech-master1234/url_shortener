CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS url_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    long_url TEXT NOT NULL,
    short_url TEXT NOT NULL UNIQUE,
    clicks INTEGER DEFAULT 0,
    user_id INTEGER,
    usage_limit INTEGER,
    password TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);