from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db, get_user_by_email, create_user, get_user_by_id

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

    user = get_user_by_id(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("login"))
    stats = {
        "total_spent": "₹382.50",
        "transactions": 8,
        "top_category": "Food",
    }
    expenses = [
        {"date": "Jun 8, 2026", "description": "Restaurant dinner",  "category": "Food",          "amount": "₹55.00"},
        {"date": "Jun 6, 2026", "description": "New shoes",           "category": "Shopping",      "amount": "₹85.00"},
        {"date": "Jun 5, 2026", "description": "Cinema ticket",       "category": "Entertainment", "amount": "₹25.00"},
        {"date": "Jun 4, 2026", "description": "Pharmacy",            "category": "Health",        "amount": "₹30.00"},
        {"date": "Jun 3, 2026", "description": "Electricity bill",    "category": "Bills",         "amount": "₹120.00"},
        {"date": "Jun 2, 2026", "description": "Bus pass top-up",     "category": "Transport",     "amount": "₹15.00"},
        {"date": "Jun 1, 2026", "description": "Grocery run",         "category": "Food",          "amount": "₹42.50"},
        {"date": "Jun 7, 2026", "description": "Miscellaneous",       "category": "Other",         "amount": "₹10.00"},
    ]
    categories = [
        {"name": "Bills",         "amount": "₹120.00", "pct": 31},
        {"name": "Food",          "amount": "₹97.50",  "pct": 25},
        {"name": "Shopping",      "amount": "₹85.00",  "pct": 22},
        {"name": "Health",        "amount": "₹30.00",  "pct": 8},
        {"name": "Entertainment", "amount": "₹25.00",  "pct": 7},
        {"name": "Transport",     "amount": "₹15.00",  "pct": 4},
        {"name": "Other",         "amount": "₹10.00",  "pct": 3},
    ]
    member_since = datetime.strptime(
        user["created_at"][:10], "%Y-%m-%d"
    ).strftime("%B %-d, %Y")
    return render_template("profile.html", user=user, member_since=member_since,
                           stats=stats, expenses=expenses, categories=categories)


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
