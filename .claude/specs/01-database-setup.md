# Plan: 01 — Database Setup

## Context

`database/db.py` is currently a stub (comment-only file). All future features — auth, profile, expenses — depend on a working SQLite data layer. This step implements the three core helpers and wires them into `app.py` startup.

---

## Files to Change

- `database/db.py` — implement all three functions (currently empty stub)
- `app.py` — add imports and call `init_db()` / `seed_db()` on startup

---

## Implementation

### `database/db.py`

```python
import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'spendly.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


def seed_db():
    conn = get_db()
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        conn.close()
        return

    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
    )
    user_id = cur.lastrowid

    expenses = [
        (user_id, 42.50,  "Food",          "2026-06-01", "Grocery run"),
        (user_id, 15.00,  "Transport",     "2026-06-02", "Bus pass top-up"),
        (user_id, 120.00, "Bills",         "2026-06-03", "Electricity bill"),
        (user_id, 30.00,  "Health",        "2026-06-04", "Pharmacy"),
        (user_id, 25.00,  "Entertainment", "2026-06-05", "Cinema ticket"),
        (user_id, 85.00,  "Shopping",      "2026-06-06", "New shoes"),
        (user_id, 10.00,  "Other",         "2026-06-07", "Miscellaneous"),
        (user_id, 55.00,  "Food",          "2026-06-08", "Restaurant dinner"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses,
    )
    conn.commit()
    conn.close()
```

**Key decisions:**
- `DB_PATH` uses `os.path` relative to `db.py` location → resolves to `database/spendly.db` in project root
- `PRAGMA foreign_keys = ON` called inside `get_db()` so every connection enforces FK constraints
- `seed_db()` checks row count before inserting — idempotent across restarts
- All SQL uses `?` placeholders — no f-strings or string formatting
- Amounts stored as `REAL`; dates as `TEXT` in `YYYY-MM-DD` format

---

### `app.py`

Add three lines at the top (imports) and a startup block before `if __name__ == "__main__"`:

```python
# Add to imports
from database.db import get_db, init_db, seed_db

# Add before if __name__ == "__main__":
with app.app_context():
    init_db()
    seed_db()
```

No existing routes change.

---

## Verification

1. `python app.py` — app starts without errors, `database/spendly.db` file appears
2. Open a Python shell:
   ```python
   from database.db import get_db
   db = get_db()
   print(list(db.execute("SELECT * FROM users").fetchall()))
   print(list(db.execute("SELECT * FROM expenses").fetchall()))
   ```
   Expect: 1 user row, 8 expense rows
3. Run `python app.py` a second time — no duplicate rows (seed guard works)
4. `pytest` — existing tests remain green
