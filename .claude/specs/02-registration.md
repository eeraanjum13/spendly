# Spec: Registration

## Overview

Implement user account creation for Spendly. This step adds the `POST /register`
route that accepts the sign-up form, validates input, hashes the password, inserts
the new user into the database, and redirects to the login page on success. It also
adds the two `database/db.py` helpers needed: `create_user()` and `get_user_by_email()`.
The `register.html` template already has the correct form markup and error display — only
minor wiring (form action uses `url_for`, CSS link) is needed.

## Depends on

- Step 1 — Database Setup (`get_db()`, `init_db()`, `users` table)

## Routes

- `GET  /register` — render registration form — public *(already exists, keep as-is)*
- `POST /register` — process form submission, create user, redirect to login — public *(new)*

## Database changes

No new tables or columns. Two new helper functions in `database/db.py`:

- `get_user_by_email(email)` — returns the users row matching the email, or `None`
- `create_user(name, email, password_hash)` — inserts a new user row, returns the new `id`

Both use parameterised queries and `get_db()`.


## Templates

- **Modify:** `templates/register.html`
  - Change hardcoded `action="/register"` → `action="{{ url_for('register') }}"`
  - Add `<link>` for `auth.css` in the `{% block head %}` (or equivalent block in `base.html`)

## Files to change

- `database/db.py` — add `get_user_by_email()` and `create_user()`
- `app.py` — add `POST` method to existing `/register` route; import new db helpers; set `app.secret_key`
- `templates/register.html` — swap hardcoded action URL; link auth.css

## Files to create

- `static/css/auth.css` — styles for `.auth-section`, `.auth-container`, `.auth-card`,
  `.auth-header`, `.auth-title`, `.auth-subtitle`, `.auth-error`, `.auth-switch`,
  `.form-group`, `.form-input`, `.btn-submit`
  (these classes are already used in the template but have no stylesheet yet)

## New dependencies

No new dependencies. Uses:
- `werkzeug.security.generate_password_hash` (already installed)
- `flask.session`, `flask.redirect`, `flask.url_for`, `flask.request`, `flask.flash` (all in Flask)

## Rules for implementation

- No SQLAlchemy or ORMs — raw `sqlite3` only
- Parameterised queries only — no f-strings in SQL
- Hash passwords with `werkzeug.security.generate_password_hash` before storing
- Use CSS variables — never hardcode hex values in `auth.css`
- All templates extend `base.html`
- All internal links use `url_for()` — never hardcode paths
- DB logic belongs in `database/db.py` — the route function only calls helpers
- On duplicate email → re-render `register.html` with `error="An account with that email already exists."`
- On successful registration → `redirect(url_for('login'))` — do not auto-login (that is Step 3)
- `app.secret_key` must be set before any session/flash usage; use a fixed dev string for now
- Validate in this order: name non-empty → valid email format → password ≥ 8 chars → email not taken

## Definition of done

- [ ] `POST /register` with valid new data creates a user row and redirects to `/login`
- [ ] Submitting a duplicate email re-renders the form with an error message (no new row inserted)
- [ ] Password is stored as a `werkzeug` hash — never plaintext
- [ ] Submitting with empty name, email, or password shows a validation error
- [ ] Submitting with a password shorter than 8 characters shows a validation error
- [ ] The registration form renders without browser console errors or missing stylesheet 404s
- [ ] All links in `register.html` use `url_for()` — no hardcoded paths remain
- [ ] `GET /register` still works after adding `POST` (route accepts both methods)
- [ ] Existing routes (`/`, `/login`, stubs) are unaffected
