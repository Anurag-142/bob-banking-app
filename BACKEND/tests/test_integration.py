"""
test_integration.py — Integration tests for Flask routes + DB.
Uses Flask's test_client() with a temporary file-based SQLite database
so no real banking.db is touched during the test run.
Each test gets its own isolated DB file via pytest's tmp_path fixture.
"""

import sys
import os

# Allow imports from BACKEND
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import models
import app as flask_app
import auth

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db(tmp_path):
    """Create a fresh temp-file database and seed one test customer.
    Using a real file DB means each models.get_connection() open/close
    cycle works correctly with no shared-connection issues."""
    db_file = tmp_path / "test_banking.db"
    # Point models at the temp DB for this test.
    models.DB_PATH = str(db_file)

    # Initialise schema and seed one customer.
    models.init_db()
    models.insert_customer(
        username="testuser",
        password_hash=auth.hash_password("testpass"),
        full_name="Test User",
        balance=1000.0,
    )
    yield db_file
    # tmp_path cleanup is automatic after the test.


@pytest.fixture
def client(db):
    """Flask test client with the temp database active."""
    flask_app.app.config["TESTING"] = True
    flask_app.app.config["SECRET_KEY"] = "test-secret"
    with flask_app.app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def login(client, username="testuser", password="testpass"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


# ---------------------------------------------------------------------------
# Authentication tests
# ---------------------------------------------------------------------------

class TestLogin:
    def test_get_login_returns_200(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200

    def test_valid_credentials_redirect_to_dashboard(self, client):
        resp = login(client)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_wrong_password_stays_on_login(self, client):
        resp = client.post(
            "/login",
            data={"username": "testuser", "password": "wrongpass"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Invalid username or password" in resp.data

    def test_unknown_user_stays_on_login(self, client):
        resp = client.post(
            "/login",
            data={"username": "nobody", "password": "pass"},
            follow_redirects=True,
        )
        assert b"Invalid username or password" in resp.data

    def test_empty_fields_show_validation_error(self, client):
        resp = client.post(
            "/login",
            data={"username": "", "password": ""},
            follow_redirects=True,
        )
        assert b"Please enter your username and password" in resp.data


class TestLogout:
    def test_logout_clears_session_and_redirects(self, client):
        login(client)
        resp = client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_dashboard_inaccessible_after_logout(self, client):
        login(client)
        client.get("/logout")
        resp = client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


# ---------------------------------------------------------------------------
# Session guard tests
# ---------------------------------------------------------------------------

class TestSessionGuard:
    def test_dashboard_redirects_when_not_logged_in(self, client):
        resp = client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_deposit_redirects_when_not_logged_in(self, client):
        resp = client.get("/deposit", follow_redirects=False)
        assert resp.status_code == 302

    def test_withdraw_redirects_when_not_logged_in(self, client):
        resp = client.get("/withdraw", follow_redirects=False)
        assert resp.status_code == 302


# ---------------------------------------------------------------------------
# Dashboard tests
# ---------------------------------------------------------------------------

class TestDashboard:
    def test_dashboard_shows_customer_name(self, client):
        login(client)
        resp = client.get("/dashboard")
        assert b"Test User" in resp.data

    def test_dashboard_shows_balance(self, client):
        login(client)
        resp = client.get("/dashboard")
        assert b"1000.00" in resp.data


# ---------------------------------------------------------------------------
# Deposit tests
# ---------------------------------------------------------------------------

class TestDeposit:
    def test_valid_deposit_increases_balance(self, client):
        login(client)
        resp = client.post(
            "/deposit",
            data={"amount": "250"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Successfully deposited" in resp.data
        assert b"1250.00" in resp.data

    def test_deposit_zero_shows_error(self, client):
        login(client)
        resp = client.post("/deposit", data={"amount": "0"}, follow_redirects=True)
        assert b"greater than zero" in resp.data

    def test_deposit_negative_shows_error(self, client):
        login(client)
        resp = client.post("/deposit", data={"amount": "-10"}, follow_redirects=True)
        assert b"greater than zero" in resp.data

    def test_deposit_non_numeric_shows_error(self, client):
        login(client)
        resp = client.post("/deposit", data={"amount": "abc"}, follow_redirects=True)
        assert b"number" in resp.data.lower()

    def test_deposit_empty_shows_error(self, client):
        login(client)
        resp = client.post("/deposit", data={"amount": ""}, follow_redirects=True)
        assert b"enter" in resp.data.lower()


# ---------------------------------------------------------------------------
# Withdrawal tests
# ---------------------------------------------------------------------------

class TestWithdraw:
    def test_valid_withdrawal_decreases_balance(self, client):
        login(client)
        resp = client.post(
            "/withdraw",
            data={"amount": "300"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Successfully withdrew" in resp.data
        assert b"700.00" in resp.data

    def test_overdraft_shows_error(self, client):
        login(client)
        resp = client.post(
            "/withdraw",
            data={"amount": "99999"},
            follow_redirects=True,
        )
        assert b"Insufficient funds" in resp.data

    def test_withdraw_zero_shows_error(self, client):
        login(client)
        resp = client.post("/withdraw", data={"amount": "0"}, follow_redirects=True)
        assert b"greater than zero" in resp.data

    def test_withdraw_non_numeric_shows_error(self, client):
        login(client)
        resp = client.post("/withdraw", data={"amount": "xyz"}, follow_redirects=True)
        assert b"number" in resp.data.lower()

    def test_exact_balance_withdrawal_succeeds(self, client):
        login(client)
        resp = client.post(
            "/withdraw",
            data={"amount": "1000"},
            follow_redirects=True,
        )
        assert b"Successfully withdrew" in resp.data
        assert b"0.00" in resp.data
