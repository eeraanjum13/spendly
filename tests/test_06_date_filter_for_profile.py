"""
Tests for Step 06: Date Filter for Profile Page
Spec: .claude/specs/06-date-filter-for-profile-page.md
"""
import pytest
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


# ------------------------------------------------------------------ #
# Auth guard                                                          #
# ------------------------------------------------------------------ #

class TestAuthGuard:
    def test_unauthenticated_redirects_to_login(self, flask_client):
        client, _ = flask_client
        r = client.get("/profile")
        assert r.status_code == 302
        assert "/login" in r.headers["Location"]

    def test_unauthenticated_with_date_params_redirects(self, flask_client):
        client, _ = flask_client
        r = client.get("/profile?from_date=2026-06-01&to_date=2026-06-05")
        assert r.status_code == 302
        assert "/login" in r.headers["Location"]


# ------------------------------------------------------------------ #
# Unfiltered view                                                     #
# ------------------------------------------------------------------ #

class TestUnfilteredView:
    def test_returns_200_when_authenticated(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile")
        assert r.status_code == 200

    def test_shows_all_eight_expenses(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile")
        html = r.data.decode()
        # All 8 expense descriptions from seed data should appear
        for desc in [
            "Grocery run", "Bus pass top-up", "Electricity bill",
            "Pharmacy", "Cinema ticket", "New shoes",
            "Miscellaneous", "Restaurant dinner",
        ]:
            assert desc in html, f"Expected '{desc}' in unfiltered profile"

    def test_shows_all_time_label(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile")
        assert b"All time" in r.data


# ------------------------------------------------------------------ #
# Filter bar HTML                                                     #
# ------------------------------------------------------------------ #

class TestFilterBarHTML:
    def test_has_from_date_input(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile")
        assert b'name="from_date"' in r.data

    def test_has_to_date_input(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile")
        assert b'name="to_date"' in r.data

    def test_has_apply_submit_button(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile")
        html = r.data.decode()
        assert 'type="submit"' in html or "Apply" in html

    def test_has_all_time_preset(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile")
        assert b"All Time" in r.data

    def test_has_this_month_preset(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile")
        assert b"This Month" in r.data

    def test_has_last_30_days_preset(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile")
        assert b"Last 30 Days" in r.data

    def test_filter_form_uses_get_method(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile")
        assert b'method="GET"' in r.data or b"method=GET" in r.data


# ------------------------------------------------------------------ #
# Valid date filter                                                   #
# ------------------------------------------------------------------ #

class TestValidDateFilter:
    def test_returns_200_with_valid_range(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile?from_date=2026-06-03&to_date=2026-06-05")
        assert r.status_code == 200

    def test_shows_only_in_range_expenses(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile?from_date=2026-06-03&to_date=2026-06-05")
        html = r.data.decode()
        # June 03-05: Bills, Health, Entertainment
        assert "Electricity bill" in html
        assert "Pharmacy" in html
        assert "Cinema ticket" in html

    def test_excludes_out_of_range_expenses(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile?from_date=2026-06-03&to_date=2026-06-05")
        html = r.data.decode()
        assert "Grocery run" not in html
        assert "Bus pass top-up" not in html
        assert "New shoes" not in html
        assert "Restaurant dinner" not in html

    def test_shows_date_range_in_showing_label(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile?from_date=2026-06-03&to_date=2026-06-05")
        html = r.data.decode()
        assert "2026-06-03" in html
        assert "2026-06-05" in html

    def test_does_not_show_all_time_when_filtered(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile?from_date=2026-06-03&to_date=2026-06-05")
        # "All time" label should not appear when a filter is active
        assert b"All time" not in r.data

    def test_filtered_stats_total_matches_range(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile?from_date=2026-06-03&to_date=2026-06-05")
        html = r.data.decode()
        # June 03-05: 120.00 + 30.00 + 25.00 = 175.00
        assert "175.00" in html

    def test_single_day_filter_returns_one_expense(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile?from_date=2026-06-01&to_date=2026-06-01")
        html = r.data.decode()
        assert "Grocery run" in html
        assert "Bus pass top-up" not in html

    def test_empty_range_returns_200_not_500(self, flask_client):
        client, _ = flask_client
        login(client)
        # No expenses on this date
        r = client.get("/profile?from_date=2025-01-01&to_date=2025-01-01")
        assert r.status_code == 200


# ------------------------------------------------------------------ #
# Invalid input fallback                                              #
# ------------------------------------------------------------------ #

class TestInvalidInputFallback:
    def test_only_from_date_falls_back_to_unfiltered(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile?from_date=2026-06-01")
        assert r.status_code == 200
        assert b"All time" in r.data

    def test_only_to_date_falls_back_to_unfiltered(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile?to_date=2026-06-05")
        assert r.status_code == 200
        assert b"All time" in r.data

    def test_reversed_dates_falls_back_to_unfiltered(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile?from_date=2026-06-10&to_date=2026-06-01")
        assert r.status_code == 200
        assert b"All time" in r.data

    def test_non_date_strings_returns_200(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile?from_date=abc&to_date=xyz")
        assert r.status_code == 200

    def test_non_date_strings_shows_all_time(self, flask_client):
        client, _ = flask_client
        login(client)
        r = client.get("/profile?from_date=abc&to_date=xyz")
        assert b"All time" in r.data

    @pytest.mark.parametrize("from_val,to_val", [
        ("", ""),
        ("  ", "  "),
        ("2026-13-01", "2026-13-05"),   # invalid month
        ("garbage", "garbage"),
        ("2026/06/01", "2026/06/05"),   # wrong separator
        ("1 OR 1=1", "1 OR 1=1"),       # SQL injection attempt
    ])
    def test_invalid_param_variants_fallback(self, flask_client, from_val, to_val):
        client, _ = flask_client
        login(client)
        r = client.get(f"/profile?from_date={from_val}&to_date={to_val}")
        assert r.status_code == 200
        assert b"All time" in r.data


# ------------------------------------------------------------------ #
# get_summary_stats unit tests                                        #
# ------------------------------------------------------------------ #

class TestGetSummaryStats:
    def test_returns_all_expenses_without_dates(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_summary_stats(uid)
        assert result["transactions"] == 8

    def test_filters_correctly_with_date_range(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_summary_stats(uid, "2026-06-03", "2026-06-05")
        assert result["transactions"] == 3

    def test_filtered_total_is_correct(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_summary_stats(uid, "2026-06-03", "2026-06-05")
        # 120.00 + 30.00 + 25.00 = 175.00
        assert "175.00" in result["total_spent"]

    def test_filtered_top_category(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_summary_stats(uid, "2026-06-03", "2026-06-05")
        assert result["top_category"] == "Bills"

    def test_returns_zero_stats_for_empty_range(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_summary_stats(uid, "2025-01-01", "2025-01-31")
        assert result["transactions"] == 0
        assert "0.00" in result["total_spent"]

    def test_unfiltered_when_only_from_date(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_summary_stats(uid, from_date="2026-06-03")
        assert result["transactions"] == 8

    def test_unfiltered_when_only_to_date(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_summary_stats(uid, to_date="2026-06-05")
        assert result["transactions"] == 8


# ------------------------------------------------------------------ #
# get_recent_transactions unit tests                                  #
# ------------------------------------------------------------------ #

class TestGetRecentTransactions:
    def test_returns_all_eight_without_dates(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_recent_transactions(uid)
        assert len(result) == 8

    def test_filters_to_three_in_range(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_recent_transactions(uid, from_date="2026-06-03", to_date="2026-06-05")
        assert len(result) == 3

    def test_filtered_descriptions_are_correct(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_recent_transactions(uid, from_date="2026-06-03", to_date="2026-06-05")
        descs = {r["description"] for r in result}
        assert descs == {"Electricity bill", "Pharmacy", "Cinema ticket"}

    def test_single_day_returns_one_row(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_recent_transactions(uid, from_date="2026-06-01", to_date="2026-06-01")
        assert len(result) == 1
        assert result[0]["description"] == "Grocery run"

    def test_empty_range_returns_empty_list(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_recent_transactions(uid, from_date="2025-01-01", to_date="2025-01-31")
        assert result == []

    def test_unfiltered_when_only_from_date(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_recent_transactions(uid, from_date="2026-06-03")
        assert len(result) == 8

    def test_required_keys_present(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_recent_transactions(uid)
        for row in result:
            assert "date" in row
            assert "description" in row
            assert "category" in row
            assert "amount" in row

    def test_ordered_newest_first(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_recent_transactions(uid)
        assert result[0]["description"] == "Restaurant dinner"
        assert result[-1]["description"] == "Grocery run"


# ------------------------------------------------------------------ #
# get_category_breakdown unit tests                                   #
# ------------------------------------------------------------------ #

class TestGetCategoryBreakdown:
    def test_returns_seven_categories_without_dates(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_category_breakdown(uid)
        assert len(result) == 7

    def test_filters_to_three_categories_in_range(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_category_breakdown(uid, "2026-06-03", "2026-06-05")
        assert len(result) == 3

    def test_filtered_category_names(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_category_breakdown(uid, "2026-06-03", "2026-06-05")
        names = {r["name"] for r in result}
        assert names == {"Bills", "Health", "Entertainment"}

    def test_percentages_sum_to_100(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_category_breakdown(uid)
        assert sum(r["pct"] for r in result) == 100

    def test_filtered_percentages_sum_to_100(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_category_breakdown(uid, "2026-06-03", "2026-06-05")
        assert sum(r["pct"] for r in result) == 100

    def test_ordered_by_descending_amount(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_category_breakdown(uid, "2026-06-03", "2026-06-05")
        # Bills (120) > Health (30) > Entertainment (25)
        assert result[0]["name"] == "Bills"

    def test_empty_range_returns_empty_list(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_category_breakdown(uid, "2025-01-01", "2025-01-31")
        assert result == []

    def test_unfiltered_when_only_from_date(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_category_breakdown(uid, from_date="2026-06-03")
        assert len(result) == 7

    def test_required_keys_present(self, app_with_db):
        uid = app_with_db["user_id"]
        result = queries_module.get_category_breakdown(uid)
        for row in result:
            assert "name" in row
            assert "amount" in row
            assert "pct" in row

    def test_empty_user_returns_empty_list(self, app_with_db):
        uid = app_with_db["empty_user_id"]
        result = queries_module.get_category_breakdown(uid)
        assert result == []
