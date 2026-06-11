# Spec: Login and Logout

## Overview
This step wires up session-based user authentication for Spendly. `GET /login` already renders the form and `GET /logout` is a stub. The real work is: a `POST /login` handler that verifies credentials and writes the user into `session`, a `GET /logout` handler that clears the session, and a DB helper `get_user_by_id()` for loading the logged-in user in later steps. On successful login the user is redirected to `/profile`; on failure the form re-renders with an inline error. `login.html` gets its hardcoded `action` fixed to use `url_for`.

## Depends on
- Step 1 — Database Setup (users table, `get_db`)
- Step 2 — Registration (`get_user_by_email`, `create_user`, hashed passwords)

## Routes
- `GET /login` - render login form - public
- `POST /login` — verifies email + password, writes `session['user_id']`, redirects to `/profile` — public
- `GET /logout` — clears session, redirects to `/` — logged-in

## Database changes
No database changes. The `users` table and `get_user_by_email()` from Step 2 are sufficient.

## Templates
- **Modify:** `templates/login.html` — fix hardcoded `action="/login"` → `action="{{ url_for('login') }}"`

## Files to change
- `database/db.py` — add `get_user_by_id(user_id)`
- `app.py` — import `session`, `check_password_hash`; add `POST` to `/login`; replace `/logout` stub with real handler
- `templates/login.html` — fix hardcoded action URL

## Files to create
No new files.

## New dependencies
No new dependencies — `werkzeug.security.check_password_hash` ships with Flask.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders — never f-strings in SQL)
- Passwords verified with `werkzeug.security.check_password_hash` — never compare plaintext
- Store only `user_id` in session — never store the full user row or password hash
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- DB logic stays in `database/db.py` — no raw SQL in route functions
- Login error must be generic: "Invalid email or password." — never reveal which field was wrong
- Logout must redirect to `/` (landing), not `/login`
- Successful login with the right credentials should redirect to the homepage.
- User should not be able to access \login and \register when they are logged in. 

## Definition of done
- [ ]  Visiting`GET /login` renders the login form with email and password fields
- [ ] `POST /login` with correct credentials sets `session['user_id']` and redirects to `/profile`
- [ ] `POST /login` with wrong password re-renders `login.html` with "Invalid email or password."
- [ ] `POST /login` with unknown email re-renders `login.html` with "Invalid email or password."
- [ ] `GET /logout` clears the session and redirects to `/`
- [ ] After logout, `session['user_id']` is no longer set (visiting `/profile` no longer shows user data)
- [ ] `login.html` uses `url_for('login')` in the form action — no hardcoded URLs
- [ ] Demo seed user (`demo@spendly.com` / `demo123`) can log in successfully
