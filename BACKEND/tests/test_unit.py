"""
test_unit.py — Unit tests for auth.py and transactions.py.
No Flask server, no real database.
The models module is monkey-patched with stubs so that transaction
tests remain fast and deterministic.
"""

import sys
import os

# Allow imports from BACKEND
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import auth
import transactions


# ===========================================================================
# auth.py tests
# ===========================================================================

class TestHashPassword:
    def test_hash_is_not_plain_text(self):
        hashed = auth.hash_password("mypassword")
        assert hashed != "mypassword"

    def test_hash_is_non_empty_string(self):
        hashed = auth.hash_password("mypassword")
        assert isinstance(hashed, str) and len(hashed) > 0

    def test_two_hashes_of_same_password_differ(self):
        """Salted hashes must not be identical even for the same input."""
        h1 = auth.hash_password("same")
        h2 = auth.hash_password("same")
        assert h1 != h2


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        hashed = auth.hash_password("correct")
        assert auth.verify_password("correct", hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = auth.hash_password("correct")
        assert auth.verify_password("wrong", hashed) is False

    def test_empty_password_returns_false(self):
        hashed = auth.hash_password("correct")
        assert auth.verify_password("", hashed) is False


# ===========================================================================
# transactions.py tests — models is stubbed out
# ===========================================================================

FAKE_BALANCE = 1000.0


@pytest.fixture(autouse=True)
def stub_models(monkeypatch):
    """Replace models functions used by transactions with simple stubs."""
    balance_store = {"value": FAKE_BALANCE}

    def fake_get_balance(customer_id):
        return balance_store["value"]

    def fake_update_balance(customer_id, new_balance):
        balance_store["value"] = new_balance

    def fake_log_transaction(customer_id, txn_type, amount):
        pass  # no-op

    monkeypatch.setattr(transactions, "get_balance", fake_get_balance)
    monkeypatch.setattr(transactions, "update_balance", fake_update_balance)
    monkeypatch.setattr(transactions, "log_transaction", fake_log_transaction)


class TestProcessDeposit:
    def test_valid_deposit_returns_ok(self):
        result = transactions.process_deposit(1, "250.00")
        assert result["ok"] is True

    def test_valid_deposit_increases_balance(self):
        result = transactions.process_deposit(1, "250.00")
        assert result["balance"] == FAKE_BALANCE + 250.00

    def test_empty_amount_returns_error(self):
        result = transactions.process_deposit(1, "")
        assert result["ok"] is False
        assert "enter" in result["message"].lower()

    def test_none_amount_returns_error(self):
        result = transactions.process_deposit(1, None)
        assert result["ok"] is False

    def test_zero_amount_returns_error(self):
        result = transactions.process_deposit(1, "0")
        assert result["ok"] is False
        assert "greater than zero" in result["message"].lower()

    def test_negative_amount_returns_error(self):
        result = transactions.process_deposit(1, "-50")
        assert result["ok"] is False

    def test_non_numeric_amount_returns_error(self):
        result = transactions.process_deposit(1, "abc")
        assert result["ok"] is False
        assert "number" in result["message"].lower()


class TestProcessWithdrawal:
    def test_valid_withdrawal_returns_ok(self):
        result = transactions.process_withdrawal(1, "200.00")
        assert result["ok"] is True

    def test_valid_withdrawal_decreases_balance(self):
        result = transactions.process_withdrawal(1, "200.00")
        assert result["balance"] == FAKE_BALANCE - 200.00

    def test_exact_balance_withdrawal_succeeds(self):
        result = transactions.process_withdrawal(1, str(FAKE_BALANCE))
        assert result["ok"] is True
        assert result["balance"] == 0.0

    def test_overdraft_returns_error(self):
        result = transactions.process_withdrawal(1, "9999.00")
        assert result["ok"] is False
        assert "insufficient" in result["message"].lower()

    def test_zero_amount_returns_error(self):
        result = transactions.process_withdrawal(1, "0")
        assert result["ok"] is False

    def test_negative_amount_returns_error(self):
        result = transactions.process_withdrawal(1, "-100")
        assert result["ok"] is False

    def test_empty_amount_returns_error(self):
        result = transactions.process_withdrawal(1, "")
        assert result["ok"] is False

    def test_non_numeric_amount_returns_error(self):
        result = transactions.process_withdrawal(1, "hello")
        assert result["ok"] is False
        assert "number" in result["message"].lower()
