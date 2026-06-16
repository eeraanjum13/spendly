import tempfile
import os
import pytest
from werkzeug.security import generate_password_hash

import database.db as db_module
import database.queries as queries_module


@pytest.fixture
def app_with_db(monkeypatch):
    """Patch DB_PATH to an isolated temp database and seed known test data."""
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    test_path = tmp.name

    monkeypatch.setattr(db_module, "DB_PATH", test_path)
    monkeypatch.setattr(queries_module, "get_db", db_module.get_db)

    db_module.init_db()

    conn = db_module.get_db()

    ph = generate_password_hash("password", method="pbkdf2:sha256")

    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Test User", "test@example.com", ph),
    )
    user_id = cur.lastrowid

    cur2 = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Empty User", "empty@example.com", ph),
    )
    empty_user_id = cur2.lastrowid

    expenses = [
        (user_id, 42.50,  "Food",          "2026-06-01", "Grocery run"),
        (user_id, 15.00,  "Transport",     "2026-06-02", "Bus pass top-up"),
        (user_id, 120.00, "Bills",         "2026-06-03", "Electricity bill"),
        (user_id, 30.00,  "Health",        "2026-06-04", "Pharmacy"),
        (user_id, 25.00,  "Entertainment", "2026-06-05", "Cinema ticket"),
        (user_id, 85.00,  "Shopping",      "2026-06-06", "New shoes"),
        (user_id, 10.00,  "Other",         "2026-06-07", "Miscellaneous"),
        (user_id, 55.00,  "Food",          "2026-06-08", "Restaurant dinner"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses,
    )
    conn.commit()
    conn.close()

    yield {"user_id": user_id, "empty_user_id": empty_user_id, "db_path": test_path}

    os.unlink(test_path)


@pytest.fixture
def flask_client(app_with_db, monkeypatch):
    """Flask test client with the patched database."""
    import database.db as db_module
    monkeypatch.setattr(db_module, "DB_PATH", app_with_db["db_path"])

    import app as app_module
    app_module.app.config["TESTING"] = True
    app_module.app.config["SECRET_KEY"] = "test-secret"

    with app_module.app.test_client() as client:
        yield client, app_with_db
