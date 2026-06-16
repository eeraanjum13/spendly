import pytest
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)


# ------------------------------------------------------------------ #
# get_user_by_id                                                      #
# ------------------------------------------------------------------ #

def test_get_user_by_id_valid(app_with_db):
    uid = app_with_db["user_id"]
    user = get_user_by_id(uid)
    assert user is not None
    assert user["name"] == "Test User"
    assert user["email"] == "test@example.com"
    assert "member_since" in user
    assert user["member_since"] != ""


def test_get_user_by_id_missing(app_with_db):
    assert get_user_by_id(99999) is None


# ------------------------------------------------------------------ #
# get_summary_stats                                                   #
# ------------------------------------------------------------------ #

def test_summary_stats_with_expenses(app_with_db):
    stats = get_summary_stats(app_with_db["user_id"])
    assert stats["total_spent"] == "₹382.50"
    assert stats["transactions"] == 8
    assert stats["top_category"] == "Bills"


def test_summary_stats_no_expenses(app_with_db):
    stats = get_summary_stats(app_with_db["empty_user_id"])
    assert stats["total_spent"] == "₹0.00"
    assert stats["transactions"] == 0
    assert stats["top_category"] == "—"


# ------------------------------------------------------------------ #
# get_recent_transactions                                             #
# ------------------------------------------------------------------ #

def test_recent_transactions_order(app_with_db):
    txns = get_recent_transactions(app_with_db["user_id"])
    assert len(txns) == 8
    # newest first: Jun 8 before Jun 7
    assert txns[0]["description"] == "Restaurant dinner"
    assert txns[1]["description"] == "Miscellaneous"
    for txn in txns:
        assert "date" in txn
        assert "description" in txn
        assert "category" in txn
        assert txn["amount"].startswith("₹")


def test_recent_transactions_limit(app_with_db):
    txns = get_recent_transactions(app_with_db["user_id"], limit=3)
    assert len(txns) == 3


def test_recent_transactions_empty(app_with_db):
    assert get_recent_transactions(app_with_db["empty_user_id"]) == []


# ------------------------------------------------------------------ #
# get_category_breakdown                                              #
# ------------------------------------------------------------------ #

def test_category_breakdown_pcts_sum_to_100(app_with_db):
    breakdown = get_category_breakdown(app_with_db["user_id"])
    assert len(breakdown) == 7
    assert sum(item["pct"] for item in breakdown) == 100


def test_category_breakdown_ordered_by_amount(app_with_db):
    breakdown = get_category_breakdown(app_with_db["user_id"])
    assert breakdown[0]["name"] == "Bills"
    for item in breakdown:
        assert isinstance(item["pct"], int)
        assert item["amount"].startswith("₹")


def test_category_breakdown_empty(app_with_db):
    assert get_category_breakdown(app_with_db["empty_user_id"]) == []


# ------------------------------------------------------------------ #
# Route tests                                                         #
# ------------------------------------------------------------------ #

def test_profile_unauthenticated(flask_client):
    client, _ = flask_client
    resp = client.get("/profile")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_profile_authenticated(flask_client):
    client, ids = flask_client
    uid = ids["user_id"]

    with client.session_transaction() as sess:
        sess["user_id"] = uid

    resp = client.get("/profile")
    assert resp.status_code == 200
    body = resp.data.decode("utf-8")
    assert "Test User" in body
    assert "test@example.com" in body
    assert "₹" in body
