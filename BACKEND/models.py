"""
models.py — Data access layer.
This is the ONLY file that interacts with the SQLite database.
All other modules call these functions; none execute SQL directly.
"""

import sqlite3
import os
from datetime import datetime, timezone

# Resolve the absolute path to banking.db relative to this file's location.
DB_PATH = os.path.join(os.path.dirname(__file__), "banking.db")


def get_connection():
    """Open and return a database connection with row_factory set so that
    results can be accessed by column name (e.g. row['balance'])."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enforce foreign key constraints on every connection.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the customers and transactions tables if they do not already exist.
    Safe to call multiple times — uses CREATE TABLE IF NOT EXISTS."""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                full_name     TEXT    NOT NULL,
                balance       REAL    NOT NULL DEFAULT 0.0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                type        TEXT    NOT NULL CHECK(type IN ('deposit', 'withdrawal')),
                amount      REAL    NOT NULL,
                timestamp   TEXT    NOT NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        """)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Customer queries
# ---------------------------------------------------------------------------

def get_customer_by_username(username):
    """Return the customer row matching the given username, or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM customers WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_customer_by_id(customer_id):
    """Return the customer row matching the given id, or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM customers WHERE id = ?", (customer_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_balance(customer_id):
    """Return the current balance for the given customer id."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT balance FROM customers WHERE id = ?", (customer_id,)
        ).fetchone()
        return row["balance"] if row else None
    finally:
        conn.close()


def update_balance(customer_id, new_balance):
    """Atomically update the balance for the given customer.
    Uses a single UPDATE inside an implicit transaction."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE customers SET balance = ? WHERE id = ?",
            (new_balance, customer_id),
        )
        conn.commit()
    finally:
        conn.close()


def insert_customer(username, password_hash, full_name, balance=0.0):
    """Insert a new customer record. Returns the new row id."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO customers (username, password_hash, full_name, balance) "
            "VALUES (?, ?, ?, ?)",
            (username, password_hash, full_name, balance),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Transaction logging
# ---------------------------------------------------------------------------

def log_transaction(customer_id, txn_type, amount):
    """Append an immutable record to the transactions table.
    txn_type must be 'deposit' or 'withdrawal'."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO transactions (customer_id, type, amount, timestamp) "
            "VALUES (?, ?, ?, ?)",
            (customer_id, txn_type, amount, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
