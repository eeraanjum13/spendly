from datetime import datetime
from database.db import get_db

VALID_CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]


def _date_clause(from_date, to_date):
    if from_date and to_date:
        return " AND date BETWEEN ? AND ?", [from_date, to_date]
    return "", []


def get_user_by_id(user_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    member_since = datetime.strptime(row["created_at"][:10], "%Y-%m-%d").strftime("%B %Y")
    return {
        "id":           row["id"],
        "name":         row["name"],
        "email":        row["email"],
        "created_at":   row["created_at"],
        "member_since": member_since,
    }


def get_summary_stats(user_id, from_date=None, to_date=None):
    conn = get_db()
    date_filter, date_params = _date_clause(from_date, to_date)
    try:
        totals = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS cnt FROM expenses WHERE user_id = ?" + date_filter,
            [user_id] + date_params,
        ).fetchone()
        top = conn.execute(
            "SELECT category FROM expenses WHERE user_id = ?" + date_filter + " GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
            [user_id] + date_params,
        ).fetchone()
    finally:
        conn.close()

    return {
        "total_spent":  f"₹{totals['total']:.2f}",
        "transactions": totals["cnt"],
        "top_category": top["category"] if top else "—",
    }


def get_recent_transactions(user_id, limit=10, from_date=None, to_date=None):
    conn = get_db()
    date_filter, date_params = _date_clause(from_date, to_date)
    try:
        rows = conn.execute(
            "SELECT id, date, description, category, amount FROM expenses"
            " WHERE user_id = ?" + date_filter + " ORDER BY date DESC, id DESC LIMIT ?",
            [user_id] + date_params + [limit],
        ).fetchall()
    finally:
        conn.close()

    result = []
    for row in rows:
        display_date = datetime.strptime(row["date"], "%Y-%m-%d").strftime("%b %-d, %Y")
        result.append({
            "id":          row["id"],
            "date":        display_date,
            "description": row["description"],
            "category":    row["category"],
            "amount":      f"₹{row['amount']:.2f}",
        })
    return result


def insert_expense(user_id, amount, category, date, description):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description),
        )
        conn.commit()
    finally:
        conn.close()


def get_expense_by_id(expense_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, user_id, amount, category, date, description FROM expenses WHERE id = ?",
            (expense_id,),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def update_expense(expense_id, amount, category, date, description):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ?",
            (amount, category, date, description, expense_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_category_breakdown(user_id, from_date=None, to_date=None):
    conn = get_db()
    date_filter, date_params = _date_clause(from_date, to_date)
    try:
        rows = conn.execute(
            "SELECT category AS name, SUM(amount) AS total FROM expenses"
            " WHERE user_id = ?" + date_filter + " GROUP BY category ORDER BY total DESC",
            [user_id] + date_params,
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    grand_total = sum(row["total"] for row in rows)
    breakdown = []
    for row in rows:
        breakdown.append({
            "name":   row["name"],
            "amount": f"₹{row['total']:.2f}",
            "pct":    round(row["total"] / grand_total * 100),
        })

    # Adjust largest category so pcts sum to exactly 100
    diff = 100 - sum(item["pct"] for item in breakdown)
    if diff != 0:
        breakdown[0]["pct"] += diff

    return breakdown
