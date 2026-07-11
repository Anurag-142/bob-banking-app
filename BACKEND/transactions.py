"""
transactions.py — Business logic for deposits and withdrawals.
Rules live here; SQL lives in models.py.
Each function returns a dict: {"ok": bool, "message": str, "balance": float|None}
"""

from models import get_balance, update_balance, log_transaction


def process_deposit(customer_id: int, raw_amount) -> dict:
    """Validate and apply a deposit.

    Checks (in order):
    1. Amount is present and non-blank.
    2. Amount is numeric.
    3. Amount is greater than zero.

    On success: updates balance and logs the transaction.
    """
    # --- Presence check ---
    if raw_amount is None or str(raw_amount).strip() == "":
        return {"ok": False, "message": "Please enter a deposit amount.", "balance": None}

    # --- Numeric check ---
    try:
        amount = float(raw_amount)
    except (ValueError, TypeError):
        return {"ok": False, "message": "Amount must be a valid number.", "balance": None}

    # --- Positive check ---
    if amount <= 0:
        return {"ok": False, "message": "Deposit amount must be greater than zero.", "balance": None}

    # --- Apply ---
    current = get_balance(customer_id)
    new_balance = round(current + amount, 2)
    update_balance(customer_id, new_balance)
    log_transaction(customer_id, "deposit", amount)

    return {
        "ok": True,
        "message": f"Successfully deposited ${amount:,.2f}.",
        "balance": new_balance,
    }


def process_withdrawal(customer_id: int, raw_amount) -> dict:
    """Validate and apply a withdrawal.

    Checks (in order):
    1. Amount is present and non-blank.
    2. Amount is numeric.
    3. Amount is greater than zero.
    4. Sufficient funds exist (balance >= amount).

    On success: updates balance and logs the transaction.
    """
    # --- Presence check ---
    if raw_amount is None or str(raw_amount).strip() == "":
        return {"ok": False, "message": "Please enter a withdrawal amount.", "balance": None}

    # --- Numeric check ---
    try:
        amount = float(raw_amount)
    except (ValueError, TypeError):
        return {"ok": False, "message": "Amount must be a valid number.", "balance": None}

    # --- Positive check ---
    if amount <= 0:
        return {"ok": False, "message": "Withdrawal amount must be greater than zero.", "balance": None}

    # --- Sufficient funds check ---
    current = get_balance(customer_id)
    if amount > current:
        return {
            "ok": False,
            "message": f"Insufficient funds. Your available balance is ${current:,.2f}.",
            "balance": current,
        }

    # --- Apply ---
    new_balance = round(current - amount, 2)
    update_balance(customer_id, new_balance)
    log_transaction(customer_id, "withdrawal", amount)

    return {
        "ok": True,
        "message": f"Successfully withdrew ${amount:,.2f}.",
        "balance": new_balance,
    }
