"""
Tests for Step 07: Add Expense
Spec: .claude/specs/07-add-expense.md
"""
import pytest
import database.db as db_module
import database.queries as queries_module


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def login(client, email="test@example.com", password="password"):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )


VALID_CATEGORIES = [
    "Food", "Transport", "Bills", "Health",
    "Entertainment", "Shopping", "Other",
]

VALID_FORM_DATA = {
    "amount":      "50.0",
    "category":    "Food",
    "date":        "2026-03-20",
    "description": "Lunch",
}


# ------------------------------------------------------------------ #
# Unit tests: insert_expense                                          #
# ------------------------------------------------------------------ #

class TestInsertExpense:
    def test_insert_with_description_creates_row(self, app_with_db):
        uid = app_with_db["user_id"]
        queries_module.insert_expense(uid, 50.0, "Food", "2026-03-20", "Lunch")

        conn = db_module.get_db()
        try:
            row = conn.execute(
                "SELECT * FROM expenses WHERE user_id = ? AND description = ? AND date = ?",
                (uid, "Lunch", "2026-03-20"),
            ).fetchone()
        finally:
            conn.close()

        assert row is not None
        assert row["amount"] == 50.0
        assert row["category"] == "Food"
        assert row["date"] == "2026-03-20"
        assert row["description"] == "Lunch"

    def test_insert_with_none_description_stores_null(self, app_with_db):
        uid = app_with_db["user_id"]
        queries_module.insert_expense(uid, 20.0, "Transport", "2026-03-21", None)

        conn = db_module.get_db()
        try:
            row = conn.execute(
                "SELECT * FROM expenses WHERE user_id = ? AND category = ? AND date = ?",
                (uid, "Transport", "2026-03-21"),
            ).fetchone()
        finally:
            conn.close()

        assert row is not None
        assert row["description"] is None


# ------------------------------------------------------------------ #
# Route tests: GET /expenses/add                                      #
# ------------------------------------------------------------------ #

class TestGetAddExpense:
    def test_unauthenticated_redirects_to_login(self, flask_client):
        client, _ = flask_client
        r = client.get("/expenses/add")
        assert r.status_code == 302
        assert "/login" in r.headers["Location"]

    def test_authenticated_returns_200(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/expenses/add")
        assert r.status_code == 200

    def test_response_contains_form_tag(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/expenses/add")
        assert b"<form" in r.data

    def test_response_contains_select_element(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/expenses/add")
        assert b"<select" in r.data

    def test_all_seven_categories_present(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/expenses/add")
        html = r.data.decode()
        for category in VALID_CATEGORIES:
            assert category in html, f"Expected category '{category}' in the dropdown"


# ------------------------------------------------------------------ #
# Route tests: POST /expenses/add                                     #
# ------------------------------------------------------------------ #

class TestPostAddExpense:
    def test_unauthenticated_redirects_to_login(self, flask_client):
        client, _ = flask_client
        r = client.post("/expenses/add", data=VALID_FORM_DATA)
        assert r.status_code == 302
        assert "/login" in r.headers["Location"]

    def test_valid_data_redirects_to_profile(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.post("/expenses/add", data=VALID_FORM_DATA, follow_redirects=False)
        assert r.status_code in (302, 303)
        assert "/profile" in r.headers["Location"]

    def test_valid_data_inserts_row_in_db(self, flask_client):
        client, ctx = flask_client
        login(client)
        client.post("/expenses/add", data=VALID_FORM_DATA, follow_redirects=False)

        conn = db_module.get_db()
        try:
            row = conn.execute(
                "SELECT * FROM expenses WHERE user_id = ? AND description = ? AND date = ?",
                (ctx["user_id"], "Lunch", "2026-03-20"),
            ).fetchone()
        finally:
            conn.close()

        assert row is not None
        assert row["amount"] == 50.0
        assert row["category"] == "Food"

    def test_missing_amount_returns_200_with_error(self, flask_client):
        client, _ = flask_client
        login(client)
        data = {**VALID_FORM_DATA, "amount": ""}
        r = client.post("/expenses/add", data=data)
        assert r.status_code == 200
        html = r.data.decode()
        assert any(p in html for p in ["error", "Error", "Amount", "amount", "positive"])

    def test_amount_zero_returns_200_with_error(self, flask_client):
        client, _ = flask_client
        login(client)
        data = {**VALID_FORM_DATA, "amount": "0"}
        r = client.post("/expenses/add", data=data)
        assert r.status_code == 200
        html = r.data.decode()
        assert any(p in html for p in ["error", "Error", "Amount", "amount", "positive"])

    def test_non_numeric_amount_returns_200_with_error(self, flask_client):
        client, _ = flask_client
        login(client)
        data = {**VALID_FORM_DATA, "amount": "abc"}
        r = client.post("/expenses/add", data=data)
        assert r.status_code == 200
        html = r.data.decode()
        assert any(p in html for p in ["error", "Error", "Amount", "amount", "positive", "number"])

    def test_invalid_category_returns_200_with_error(self, flask_client):
        client, _ = flask_client
        login(client)
        data = {**VALID_FORM_DATA, "category": "Gadgets"}
        r = client.post("/expenses/add", data=data)
        assert r.status_code == 200
        html = r.data.decode()
        assert any(p in html for p in ["error", "Error", "category", "Category", "valid"])

    def test_invalid_date_returns_200_with_error(self, flask_client):
        client, _ = flask_client
        login(client)
        data = {**VALID_FORM_DATA, "date": "not-a-date"}
        r = client.post("/expenses/add", data=data)
        assert r.status_code == 200
        html = r.data.decode()
        assert any(p in html for p in ["error", "Error", "date", "Date", "valid"])

    def test_no_description_redirects_to_profile(self, flask_client):
        client, _ = flask_client
        login(client)
        data = {**VALID_FORM_DATA, "description": ""}
        r = client.post("/expenses/add", data=data, follow_redirects=False)
        assert r.status_code in (302, 303)
        assert "/profile" in r.headers["Location"]

    def test_no_description_stores_null_in_db(self, flask_client):
        client, ctx = flask_client
        login(client)
        data = {**VALID_FORM_DATA, "description": "", "date": "2026-04-01"}
        client.post("/expenses/add", data=data, follow_redirects=False)

        conn = db_module.get_db()
        try:
            row = conn.execute(
                "SELECT * FROM expenses WHERE user_id = ? AND category = ? AND date = ?",
                (ctx["user_id"], "Food", "2026-04-01"),
            ).fetchone()
        finally:
            conn.close()

        assert row is not None
        assert row["description"] is None
