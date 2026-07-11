"""
seed.py — One-time script to initialise the database and insert test customers.
Run this before starting the app for the first time:
    cd BACKEND
    python seed.py

To reset: delete banking.db then run this script again.
"""

import sys
import os

# Allow imports from the BACKEND directory when run directly.
sys.path.insert(0, os.path.dirname(__file__))

from models import init_db, insert_customer, get_customer_by_username
from auth import hash_password

SEED_CUSTOMERS = [
    {
        "username": "alice",
        "password": "password123",
        "full_name": "Alice Johnson",
        "balance": 5000.00,
    },
    {
        "username": "bob",
        "password": "securepass",
        "full_name": "Bob Williams",
        "balance": 12500.50,
    },
    {
        "username": "carol",
        "password": "mybank2024",
        "full_name": "Carol Davis",
        "balance": 750.00,
    },
]


def seed():
    print("Initialising database schema...")
    init_db()
    print("Schema ready.")

    inserted = 0
    skipped = 0

    for customer in SEED_CUSTOMERS:
        existing = get_customer_by_username(customer["username"])
        if existing:
            print(f"  SKIP  {customer['username']} — already exists.")
            skipped += 1
            continue

        hashed = hash_password(customer["password"])
        insert_customer(
            username=customer["username"],
            password_hash=hashed,
            full_name=customer["full_name"],
            balance=customer["balance"],
        )
        print(f"  OK    {customer['username']} ({customer['full_name']}) — balance ${customer['balance']:,.2f}")
        inserted += 1

    print(f"\nDone. {inserted} customer(s) inserted, {skipped} skipped.")
    print("\nTest credentials:")
    for c in SEED_CUSTOMERS:
        print(f"  username: {c['username']:<10}  password: {c['password']}")


if __name__ == "__main__":
    seed()
