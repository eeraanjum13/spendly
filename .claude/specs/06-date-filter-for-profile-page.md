# Spec: Date Filter for Profile Page

## Overview
This step adds a date-range filter to the profile page so users can narrow the
transaction list, summary stats, and category breakdown to a specific period.
The filter is a simple HTML form submitted via GET, appending `from_date` and
`to_date` query parameters to `/profile`. The route reads those params and
passes them to the query helpers in `database/queries.py`, which apply a
`WHERE date BETWEEN ? AND ?` clause. Preset buttons ("This Month", "Last 30
Days", "All Time") let users jump to common ranges without typing dates
manually. All three data sections — transactions, stats, and category
breakdown — update together when the filter changes.

## Depends on
- Step 1: Database setup (`get_db`, `expenses` table with `date` column)
- Step 2: Registration (users exist)
- Step 3: Login / Logout (`session["user_id"]` set on login)
- Step 4: Profile page UI (template structure with all four sections)
- Step 5: Backend connection (live query helpers in `database/queries.py`)

## Routes
No new routes. `GET /profile` is modified to read optional query parameters:
- `from_date` (YYYY-MM-DD string, optional)
- `to_date` (YYYY-MM-DD string, optional)

If both are absent, the route defaults to showing all expenses (no date filter
applied). If only one is provided, it is ignored and the unfiltered view is
shown.

## Database changes
No database changes. The `expenses.date` column (YYYY-MM-DD text) already
supports range queries.

## Templates
- **Modify:** `templates/profile.html`
  - Add a filter bar above the stats row containing:
    - A `<form method="GET" action="{{ url_for('profile') }}">` with two date
      inputs (`name="from_date"`, `name="to_date"`) and a Submit button
    - Three preset links that build the query string for "This Month",
      "Last 30 Days", and "All Time" (`from_date` + `to_date` pairs, or no
      params for All Time)
    - Display the active range below the filter bar:
      `Showing: <from_date> – <to_date>` (or "All time" when no filter)
  - All three data sections (stats, transactions, category breakdown) already
    consume Jinja variables — no structural changes needed beyond adding the
    filter bar

## Files to change
- `app.py` — update the `profile()` view to:
  1. Read `request.args.get("from_date")` and `request.args.get("to_date")`
  2. Validate both are present and parseable as YYYY-MM-DD dates; if invalid
     or only one is provided, default to `None, None` (unfiltered)
  3. Pass the validated dates to all four query helpers
  4. Pass `from_date` and `to_date` into the template context for the filter
     bar and the "Showing:" label
- `database/queries.py` — add an optional `(from_date, to_date)` parameter
  pair to:
  - `get_summary_stats(user_id, from_date=None, to_date=None)`
  - `get_recent_transactions(user_id, limit=10, from_date=None, to_date=None)`
  - `get_category_breakdown(user_id, from_date=None, to_date=None)`

  When both dates are provided, append `AND date BETWEEN ? AND ?` to each
  query. `get_user_by_id` does not need changes.

## Files to create
- `static/css/filter.css` — styles for the filter bar and preset buttons only;
  no inline styles, no hex values

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never string-format dates into SQL
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No inline styles
- Date validation must use `datetime.strptime(value, "%Y-%m-%d")` wrapped in
  a try/except; on failure, silently fall back to the unfiltered view
- `from_date` must be ≤ `to_date`; if `from_date > to_date`, treat as invalid
  and show the unfiltered view
- Preset links must use `url_for("profile", from_date=..., to_date=...)` —
  never hardcode `/profile?...` strings in the template
- The filter form must use `method="GET"` — do not use POST for filters
- "All Time" preset must link to `url_for("profile")` with no query params
- The active date range label ("Showing: …") must always be visible in the
  filter bar; when no filter is active, show "Showing: All time"
- Do not change the `get_user_by_id` function signature

## Definition of done
- [ ] Visiting `/profile` without query params shows all expenses (unfiltered)
- [ ] The filter bar is visible on the profile page with two date inputs and a Submit button
- [ ] Submitting valid `from_date` and `to_date` returns only expenses within that range
- [ ] Summary stats (total spent, transaction count, top category) reflect the filtered range
- [ ] Category breakdown reflects the filtered range
- [ ] Submitting with only `from_date` or only `to_date` shows the unfiltered view without an error
- [ ] Submitting with `from_date > to_date` shows the unfiltered view without an error
- [ ] Submitting a non-date string (e.g. "abc") shows the unfiltered view without a 500 error
- [ ] "This Month" preset filters to the first and last day of the current calendar month
- [ ] "Last 30 Days" preset filters from today minus 30 days through today
- [ ] "All Time" preset clears the filter and shows all expenses
- [ ] The "Showing:" label updates correctly for each state (filtered range or "All time")
- [ ] No hex colour values appear in the new template markup — only CSS variables
- [ ] The seed user (demo@spendly.com / demo123) with 8 expenses can filter to a single day and see exactly the expenses on that date
