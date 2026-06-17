import calendar
from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db, get_user_by_email, create_user
from database import queries

app = Flask(__name__)
app.secret_key = "spendly-dev-secret"

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))
    if request.method == "GET":
        return render_template("register.html")

    name     = request.form.get("name", "").strip()
    email    = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not name:
        return render_template("register.html", error="Full name is required.")
    if not email or "@" not in email:
        return render_template("register.html", error="A valid email address is required.")
    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters.")
    if get_user_by_email(email):
        return render_template("register.html", error="An account with that email already exists.")

    create_user(name, email, generate_password_hash(password))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))
    if request.method == "GET":
        return render_template("login.html")

    email    = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = get_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password.")

    session["user_id"] = user["id"]
    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = queries.get_user_by_id(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("login"))

    raw_from = request.args.get("from_date", "").strip()
    raw_to   = request.args.get("to_date", "").strip()

    from_date = to_date = None
    if raw_from and raw_to:
        try:
            from_date = datetime.strptime(raw_from, "%Y-%m-%d").date()
            to_date   = datetime.strptime(raw_to,   "%Y-%m-%d").date()
            if from_date > to_date:
                from_date = to_date = None
        except ValueError:
            pass

    from_str = from_date.isoformat() if from_date else None
    to_str   = to_date.isoformat()   if to_date   else None

    today        = date.today()
    today_str    = today.isoformat()
    month_start  = today.replace(day=1).isoformat()
    month_end    = today.replace(day=calendar.monthrange(today.year, today.month)[1]).isoformat()
    last30_start = (today - timedelta(days=30)).isoformat()

    user_id    = session["user_id"]
    stats      = queries.get_summary_stats(user_id, from_str, to_str)
    expenses   = queries.get_recent_transactions(user_id, from_date=from_str, to_date=to_str)
    categories = queries.get_category_breakdown(user_id, from_str, to_str)

    return render_template(
        "profile.html",
        user=user,
        member_since=user["member_since"],
        stats=stats,
        expenses=expenses,
        categories=categories,
        from_date=from_str,
        to_date=to_str,
        month_start=month_start,
        month_end=month_end,
        last30_start=last30_start,
        last30_end=today_str,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
