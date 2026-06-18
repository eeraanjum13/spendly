# Spec: Edit Expense

## Overview
Step 8 lets a logged-in user edit an existing expense through a pre-populated
form at `/expenses/<id>/edit`. The route already exists as a stub returning a
plain string; this step upgrades it to a full GET + POST handler. On GET, the
form is pre-filled with the expense's current values. On POST, the submitted
values are validated and the row is updated in the database. Ownership is
enforced: a user may only edit their own expenses. Two new query helpers are
added to `database/queries.py`: `get_expense_by_id` and `update_expense`. The
profile page's transaction list also needs the expense `id` exposed so that
edit (and future delete) links can be rendered per row.

## Depends on
- Step 1: Database setup (`expenses` table with all required columns)
- Step 3: Login / Logout (`session["user_id"]` is set and checked)
- Step 4 / 5: Profile page exists and is the natural redirect target after saving
- Step 7: Add Expense form (establishes the form pattern and `VALID_CATEGORIES`)

## Routes
- `GET /expenses/<int:id>/edit` — render edit form pre-filled with existing expense data — logged-in only
- `POST /expenses/<int:id>/edit` — validate and update the expense row — logged-in only

## Database changes
No schema changes. All required columns (`id`, `user_id`, `amount`, `category`,
`date`, `description`) already exist in the `expenses` table.

The `get_recent_transactions` query in `database/queries.py` currently does
**not** select `id`. It must be updated to include `id` in its SELECT so that
edit and delete links can be rendered on the profile page.

## Templates
- **Create**: `templates/edit_expense.html`
  - Extends `base.html`
  - Form with `method="POST"` and `action` pointing to the current edit URL
  - Pre-populated fields (values come from the route):
    - `amount` — number input, step="0.01", min="0.01", required
    - `category` — `<select>` with the 7 fixed options (selected option matches current value)
    - `date` — `<input type="date">`, required, pre-filled with current date
    - `description` — text input, optional, pre-filled with current value
  - Submit button ("Save Changes") and a cancel link back to `/profile`
  - Display error message on validation failure, re-populating submitted values
- **Modify**: `templates/profile.html`
  - Add an "Action" column header (`<th>Action</th>`) to the recent transactions table
  - Add an Edit link per row in the Action column pointing to
    `url_for("edit_expense", id=expense["id"])`
- **Modify**: `static/css/profile.css`
  - Add `.txn-actions` — `text-align: right`, `padding-left: 1rem`, `white-space: nowrap` to separate the Action cell from the Amount column
  - Add `.edit-link` — uses `var(--accent)` color, no underline by default, underline on hover

## Files to change
- `app.py`
  - Replace the GET-only stub at `/expenses/<int:id>/edit` with a GET + POST handler:
    - GET: fetch the expense row; abort(404) if not found; abort(403) if `user_id` doesn't match session; render `edit_expense.html`
    - POST: read form fields, validate (same rules as add_expense), call `update_expense`, redirect to `url_for("profile")` with 303
- `database/queries.py`
  - Add `get_expense_by_id(expense_id)` — returns one row dict or `None`
  - Add `update_expense(expense_id, amount, category, date, description)` — updates the row
  - Update `get_recent_transactions` to include `id` in its SELECT clause

## Files to create
- `templates/edit_expense.html` — the edit form template

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`
- Parameterised queries only — never string-format values into SQL
- Ownership check is mandatory: if the fetched expense's `user_id` != `session["user_id"]`, call `abort(403)` — do not silently redirect
- If the expense `id` does not exist, call `abort(404)`
- Unauthenticated access to both GET and POST must redirect to `/login`
- Validation rules for POST (identical to add_expense):
  - `amount`: required, must be a positive finite number (parse with `float()`; catch `ValueError`)
  - `category`: required, must be one of the 7 fixed categories from `queries.VALID_CATEGORIES`
  - `date`: required, must be a valid `YYYY-MM-DD` date (parse with `datetime.strptime`)
  - `description`: optional; strip whitespace; store `None` if blank
  - On any validation error, re-render the form with the error message and the submitted values pre-filled (not the original DB values)
- After successful update, redirect to `url_for("profile")` with status 303 — do NOT re-render the form
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No inline styles
- Currency must always display as ₹ — never £ or $

## Definition of done
- [ ] Visiting `/expenses/<id>/edit` while logged out redirects to `/login`
- [ ] Visiting `/expenses/<id>/edit` for a non-existent id returns 404
- [ ] Visiting `/expenses/<id>/edit` for an expense owned by a different user returns 403
- [ ] Visiting `/expenses/<id>/edit` while logged in renders a form pre-filled with the expense's current amount, category, date, and description
- [ ] Submitting valid changes redirects to `/profile` (303) and the updated values appear in the transaction list
- [ ] Submitting with a missing or zero amount re-renders the form with an error and retains the submitted values
- [ ] Submitting with an invalid category re-renders the form with an error
- [ ] Submitting with an invalid date re-renders the form with an error
- [ ] Submitting without a description saves the expense with `description = NULL` (no error)
- [ ] The profile page transaction list shows an Edit link per row that navigates to the correct edit URL
