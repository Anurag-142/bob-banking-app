"""
app.py — Flask application entry point.
Registers all routes, configures sessions and template folder,
and starts the development server.
"""

import os
import sys

# Ensure BACKEND modules (models, auth, transactions) are importable
# when app.py is run from any working directory.
sys.path.insert(0, os.path.dirname(__file__))

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

from auth import verify_password
from models import get_customer_by_username, get_customer_by_id, get_balance
from transactions import process_deposit, process_withdrawal

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "FRONTEND", "templates")

app = Flask(__name__, template_folder=TEMPLATE_DIR)

# Secret key signs the session cookie. In production, load from an env var.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")


# ---------------------------------------------------------------------------
# Session guard helper
# ---------------------------------------------------------------------------

def login_required():
    """Return a redirect to /login if no active session, else None."""
    if "customer_id" not in session:
        return redirect(url_for("login"))
    return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Root URL — redirect to login (or dashboard if already authenticated)."""
    if "customer_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# ---- Authentication --------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    """GET: render login form (skip if already logged in).
    POST: validate credentials and create session on success."""
    # Already logged in — send to dashboard.
    if "customer_id" in session:
        return redirect(url_for("dashboard"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # --- Validation: fields must not be blank ---
        if not username or not password:
            error = "Please enter your username and password."
        else:
            customer = get_customer_by_username(username)

            # Use the same generic message whether the user is unknown
            # or the password is wrong — prevents username enumeration.
            if customer is None or not verify_password(password, customer["password_hash"]):
                error = "Invalid username or password."
            else:
                # Credentials verified — establish session.
                session["customer_id"] = customer["id"]
                session["customer_name"] = customer["full_name"]
                return redirect(url_for("dashboard"))

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    """Destroy the session and redirect to the login page."""
    session.clear()
    return redirect(url_for("login"))


# ---- Dashboard -------------------------------------------------------------

@app.route("/dashboard")
def dashboard():
    """Display the customer's name and current balance."""
    guard = login_required()
    if guard:
        return guard

    customer_id = session["customer_id"]
    customer = get_customer_by_id(customer_id)
    balance = get_balance(customer_id)

    return render_template(
        "dashboard.html",
        customer_name=session["customer_name"],
        balance=balance,
    )


# ---- Deposit ---------------------------------------------------------------

@app.route("/deposit", methods=["GET", "POST"])
def deposit():
    """GET: render deposit form.
    POST: process deposit via the transaction service."""
    guard = login_required()
    if guard:
        return guard

    customer_id = session["customer_id"]
    result = None

    if request.method == "POST":
        raw_amount = request.form.get("amount", "").strip()
        result = process_deposit(customer_id, raw_amount)

    # Always fetch the latest balance for display.
    balance = get_balance(customer_id)

    return render_template(
        "deposit.html",
        customer_name=session["customer_name"],
        balance=balance,
        result=result,
    )


# ---- Withdraw --------------------------------------------------------------

@app.route("/withdraw", methods=["GET", "POST"])
def withdraw():
    """GET: render withdrawal form.
    POST: process withdrawal via the transaction service."""
    guard = login_required()
    if guard:
        return guard

    customer_id = session["customer_id"]
    result = None

    if request.method == "POST":
        raw_amount = request.form.get("amount", "").strip()
        result = process_withdrawal(customer_id, raw_amount)

    # Always fetch the latest balance for display.
    balance = get_balance(customer_id)

    return render_template(
        "withdraw.html",
        customer_name=session["customer_name"],
        balance=balance,
        result=result,
    )


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # debug=True is safe for local development only.
    # Never set debug=True in a shared or production environment.
    app.run(debug=True, port=5000)
