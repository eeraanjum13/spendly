# Spec: Registration

## Overview
This step implements user account creation for Spendly. It introduces the `users` table, the `database/db.py` helper functions (`get_db`, `init_db`), and a `POST /register` route that validates input, hashes the password, and persists the new user. On success the user is redirected to the login page; on failure, flash messages surface the error inline. This is the first step that touches the database and establishes the auth foundation all later steps build on.

## Depends on
- Step 1 — Database Setup must be complete (get_db, init_db, users table). If Step 1 has not been implemented, implement the required db.py helpers as part of this step.

## Routes
- `POST /register` — receives form data, validates, hashes password, inserts user — public

## Database changes
New table required (create in `init_db()`):

```sql
CREATE TABLE IF NOT EXISTS users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT    NOT NULL UNIQUE,
    email    TEXT    NOT NULL UNIQUE,
    password TEXT    NOT NULL,
    created_at TEXT  NOT NULL DEFAULT (datetime('now'))
);
```

`get_db()` must set `PRAGMA foreign_keys = ON` and `row_factory = sqlite3.Row` on every connection.

## Templates
- **Modify:** `templates/register.html` — add `method="POST"` and `action="{{ url_for('register') }}"` to the form; add field names (`username`, `email`, `password`, `confirm_password`); render flash messages for errors and success.

## Files to change
- `app.py` — add `POST` method to the `/register` route; import `flash`, `redirect`, `url_for`, `request`, `session`; set `app.secret_key`; call `init_db()` at startup via `with app.app_context()`
- `database/db.py` — implement `get_db()` and `init_db()` (create users table)
- `templates/register.html` — wire up the form as described above

## Files to create
- None

## New dependencies
No new dependencies — `werkzeug.security` ships with Flask.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders — never f-strings in SQL)
- Passwords hashed with `werkzeug.security.generate_password_hash`; never store plaintext
- `app.secret_key` must be set before any flash/session usage; use `os.urandom(24)` or a hardcoded dev string — flag that production needs an env var
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic stays in `database/db.py` — route functions must not contain raw SQL
- Validate: username non-empty, email non-empty, password ≥ 8 characters, password matches confirm_password, username/email not already taken (catch `IntegrityError`)
- On validation failure: `flash()` the error and re-render `register.html` (do not redirect)
- On success: `flash()` a success message and `redirect(url_for('login'))`

## Definition of done
- [ ] Visiting `/register` renders the registration form (GET still works)
- [ ] Submitting the form with valid data creates a row in the `users` table (verifiable via SQLite CLI or seed script)
- [ ] The new user's password is stored as a hash, not plaintext
- [ ] Submitting with mismatched passwords shows an inline error and does not create a user
- [ ] Submitting with a duplicate username or email shows an inline error and does not create a duplicate user
- [ ] Submitting with a password shorter than 8 characters shows an inline error
- [ ] Successful registration redirects to `/login`
- [ ] All flash error messages are visible in the browser without a page reload
