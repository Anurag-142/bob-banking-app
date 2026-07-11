# Banking Web Application — Step-by-Step Implementation Guide

> **Reference:** [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md)  
> **Technology:** HTML + Bootstrap · Python Flask · SQLite  
> **Approach:** Plain-English instructions describing *what to build and why*, not literal code.

---

## Table of Contents

1. [Environment Setup](#1-environment-setup)
2. [Backend Implementation](#2-backend-implementation)
3. [Frontend Implementation](#3-frontend-implementation)
4. [Integration Steps](#4-integration-steps)
5. [Validation Rules](#5-validation-rules)
6. [Testing](#6-testing)
7. [Deployment](#7-deployment)

---

## 1. Environment Setup

### 1.1 Prerequisites

Before writing any code, confirm the following tools are available on your machine:

- **Python 3.10 or newer** — the runtime for the Flask backend.
- **pip** — Python's package manager, used to install Flask and its dependencies.
- A terminal / command prompt and a code editor of your choice.

You do not need Node.js, npm, or any frontend build tooling. Bootstrap is pulled in via a CDN link in the HTML.

---

### 1.2 Create the Project Folder Structure

Manually create the following directories at the root of the project:

- A `FRONTEND/` folder containing a `templates/` subfolder — this is where all HTML pages will live.
- A `BACKEND/` folder — this holds all Python source files and the database.

This separation keeps presentation (HTML) and logic (Python) cleanly apart from the start.

---

### 1.3 Create and Activate a Virtual Environment

Inside the `BACKEND/` folder, create a Python virtual environment. A virtual environment isolates the project's dependencies from any other Python projects on your machine, preventing version conflicts.

- On Windows: use `python -m venv venv` then activate with `venv\Scripts\activate`.
- On macOS/Linux: use `python3 -m venv venv` then activate with `source venv/bin/activate`.

You will know the environment is active when the terminal prompt shows the environment name in parentheses.

---

### 1.4 Create `requirements.txt`

Inside `BACKEND/`, create a plain text file named `requirements.txt`. List each dependency on its own line:

- `Flask` — the web framework.
- `Werkzeug` — ships with Flask; provides the password hashing utilities.

Having a `requirements.txt` means any developer (or CI pipeline) can reproduce the exact environment with a single install command: `pip install -r requirements.txt`.

---

### 1.5 Install Dependencies

With the virtual environment active, run the install command pointing at your `requirements.txt`. pip will download Flask and all of its transitive dependencies (including Werkzeug, Jinja2, and Click) into the virtual environment.

Verify the install succeeded by running `flask --version` in the terminal. If a version number is printed, the environment is ready.

---

## 2. Backend Implementation

### 2.1 Create the Flask Application Entry Point (`app.py`)

`app.py` is the heart of the backend. Its responsibilities are:

1. **Instantiate the Flask app** — create a Flask application object and give it a secret key. The secret key is a random string used to cryptographically sign session cookies; without it, sessions cannot be trusted.
2. **Configure the template folder** — tell Flask where to look for HTML files. Point it at `../FRONTEND/templates` so it finds the files in the `FRONTEND` directory.
3. **Register all route functions** — each URL the browser can visit must be mapped to a Python function that handles it.
4. **Start the development server** — at the bottom of the file, add the standard `if __name__ == "__main__"` guard that starts Flask's built-in server when you run `python app.py`.

Keep `app.py` focused on wiring things together. Business logic should live in the service files described below.

---

### 2.2 Create the Database Model Layer (`models.py`)

`models.py` is the only file that speaks directly to SQLite. All other Python files go through this module to read or write data. Its responsibilities are:

1. **Open a connection** — provide a helper function that opens (and if needed, creates) the `banking.db` SQLite file in the `BACKEND/` folder and returns a connection object.
2. **Initialise the schema** — provide a function that creates the two tables if they do not already exist:
   - A `customers` table storing each customer's unique id, username, hashed password, full name, and current balance.
   - A `transactions` table storing each transaction's id, a foreign key to the customer, the transaction type (deposit or withdrawal), the amount, and the timestamp.
3. **Customer lookup** — a function that accepts a username and returns the matching customer record from the database, or `None` if no match is found. Used during login.
4. **Balance retrieval** — a function that accepts a customer id and returns the current balance figure.
5. **Balance update** — a function that accepts a customer id and a new balance value and persists it. This must be wrapped in a database transaction so the write is atomic.
6. **Transaction logging** — a function that inserts a new row into the `transactions` table whenever a deposit or withdrawal completes successfully.

By isolating all SQL in this one file, you make the rest of the application database-agnostic — swapping SQLite for PostgreSQL later would only require changes here.

---

### 2.3 Create the Authentication Helper (`auth.py`)

`auth.py` contains two pure utility functions with no side effects:

1. **`hash_password(plain_text)`** — accepts a plain-text password string and returns a salted hash using Werkzeug's `generate_password_hash`. This is called once during data seeding, never during a live login.
2. **`verify_password(plain_text, stored_hash)`** — accepts the password the user typed and the hash stored in the database, and returns `True` if they match or `False` otherwise. Uses Werkzeug's `check_password_hash`.

These two functions are the only place in the application that touches raw password strings. Nothing else in the codebase ever reads or compares plain-text passwords.

---

### 2.4 Create the Transaction Service (`transactions.py`)

`transactions.py` contains the business rules for deposits and withdrawals. It does not touch the database directly — it calls `models.py` functions:

1. **`process_deposit(customer_id, amount)`**
   - Confirm the amount is a positive number greater than zero.
   - Fetch the current balance from `models.py`.
   - Add the amount to the current balance to compute the new balance.
   - Call the balance update function in `models.py`.
   - Call the transaction logging function in `models.py` with type `"deposit"`.
   - Return a success result.

2. **`process_withdrawal(customer_id, amount)`**
   - Confirm the amount is a positive number greater than zero.
   - Fetch the current balance from `models.py`.
   - Check that the current balance is greater than or equal to the requested amount.
   - If sufficient funds exist, subtract the amount and call the balance update function.
   - Call the transaction logging function in `models.py` with type `"withdrawal"`.
   - If insufficient funds, return a failure result with an explanatory message.

Centralising these rules in one service file means the Flask routes stay thin — they just call a service function and decide what to render based on the result.

---

### 2.5 Seed the Database (`seed.py`)

`seed.py` is a standalone script (not part of the running app) that you execute once to populate the database with test data:

1. Call the schema initialisation function from `models.py` to create the tables.
2. Define one or more test customer records — username, plain-text password, full name, and a starting balance.
3. For each record, hash the password using `auth.py`'s `hash_password` function.
4. Insert the hashed record into the `customers` table.

Run this script once before starting the app for the first time. If you need to reset the database, delete `banking.db` and run `seed.py` again.

---

### 2.6 Define the Flask Routes in `app.py`

Each route is a Python function decorated with `@app.route(...)`. Here is how to approach each one:

#### `GET /` — Root redirect
When someone visits the bare root URL, redirect them immediately to `/login`. This avoids a blank page.

#### `GET /login` and `POST /login` — Login
- On a **GET** request: check if the user already has an active session. If so, redirect straight to `/dashboard`. If not, render `login.html`.
- On a **POST** request: extract the username and password from the submitted form data. Call the customer lookup function from `models.py`, then call `verify_password` from `auth.py`. If the credentials match, store the customer's id and name in the Flask session object, then redirect to `/dashboard`. If they do not match, re-render `login.html` with an error message.

#### `GET /logout` — Logout
Clear the entire session using Flask's `session.clear()`. Then redirect to `/login`. No template is rendered — this is a pure redirect.

#### `GET /dashboard` — Dashboard
First, check that the session contains a logged-in customer id. If not, redirect to `/login`. If yes, fetch the customer's name and current balance from `models.py` and render `dashboard.html`, passing both values into the template.

#### `GET /deposit` and `POST /deposit` — Deposit
- On **GET**: check session, then render `deposit.html`.
- On **POST**: read the amount from the form. Pass it to `transactions.py`'s `process_deposit` function along with the session's customer id. If the result is success, render `deposit.html` with a success message and the new balance. If it fails validation, re-render with an error message.

#### `GET /withdraw` and `POST /withdraw` — Withdraw
- On **GET**: check session, then render `withdraw.html` with the current balance.
- On **POST**: read the amount from the form. Pass it to `transactions.py`'s `process_withdrawal`. If successful, render `withdraw.html` with a success message and updated balance. If it fails (insufficient funds or invalid amount), re-render with a clear error message.

---

### 2.7 Session Management

Flask's session object behaves like a Python dictionary that is serialised, signed with the secret key, and stored in a browser cookie. Here is how to use it correctly:

- **On login:** write the customer's database id and display name into the session — e.g., `session["customer_id"]` and `session["customer_name"]`.
- **On every protected route:** at the very start of the route function, check whether `"customer_id"` exists in the session. If it does not, call `redirect(url_for("login"))` immediately and return, before executing any other logic.
- **On logout:** call `session.clear()` to remove all keys.
- **Secret key discipline:** never hard-code the secret key as a visible string in production. For development, a fixed string is acceptable; for production, load it from an environment variable.

---

### 2.8 Error Handling

Add the following lightweight error handling to `app.py`:

- **404 handler:** register a Flask `@app.errorhandler(404)` function that renders a simple "Page not found" message rather than Flask's default debug page.
- **500 handler:** register a `@app.errorhandler(500)` function that renders a "Something went wrong" message. This catches unhandled exceptions in production mode.
- **Route-level validation errors:** for invalid form inputs (e.g. non-numeric amount), re-render the same page with an inline error message rather than crashing. These are not server errors — they are user errors and should be communicated clearly.

---

## 3. Frontend Implementation

All pages live in `FRONTEND/templates/`. Flask renders them using Jinja2, which means you can embed Python variables directly in the HTML using `{{ variable_name }}` syntax and use `{% if %}` / `{% for %}` blocks for logic.

---

### 3.1 Shared Layout Principles

Before building individual pages, decide on a consistent layout:

- Include the Bootstrap 5 CDN `<link>` tag in the `<head>` of every page. This loads Bootstrap's CSS.
- Include the Bootstrap bundle `<script>` tag just before `</body>` on every page. This enables interactive components.
- Use Bootstrap's container and grid system (`container`, `row`, `col`) to centre content and keep pages readable on different screen sizes.
- Use a Bootstrap `navbar` component at the top of every page except the login page. The navbar should show the app name on the left and a "Logout" link on the right.
- Display feedback messages (success or error) using Bootstrap's `alert` component — `alert-success` for confirmations and `alert-danger` for errors. Only render the alert block if a message was passed by the route.

To avoid repeating the navbar and boilerplate HTML on every page, consider using Jinja2's template inheritance: create a `base.html` that contains the common structure and a `{% block content %}` placeholder, then have each page extend it with `{% extends "base.html" %}`.

---

### 3.2 Login Page (`login.html`)

**Purpose:** Collect the customer's username and password and submit them to the backend.

**What to include:**
- A centred card layout using Bootstrap's `card` component — this gives the login form a clean, professional appearance.
- A heading such as "Welcome to Banking App" above the form.
- Two form inputs: one for username (type `text`) and one for password (type `password`). Both should have clear `<label>` elements.
- A submit button styled with Bootstrap's `btn btn-primary`.
- An error message area that only appears when the backend passes an error string to the template. Use a Bootstrap `alert-danger` div rendered conditionally with `{% if error %}`.
- The form's `action` attribute should point to `/login` and the `method` should be `POST`.

**What to leave out:** Do not add client-side JavaScript validation. All validation happens server-side.

---

### 3.3 Dashboard Page (`dashboard.html`)

**Purpose:** Show the authenticated customer a summary of their account and give them navigation to actions.

**What to include:**
- The shared navbar at the top.
- A greeting that uses the customer's name pulled from the template variable — e.g., "Welcome back, {{ customer_name }}".
- A prominent display of the current balance, formatted as currency.
- Two Bootstrap buttons (or cards): one linking to `/deposit` and one linking to `/withdraw`.
- The balance display should be inside a Bootstrap `card` or `jumbotron`-style panel to draw visual attention to it.

---

### 3.4 Deposit Page (`deposit.html`)

**Purpose:** Let the customer enter an amount to add to their balance.

**What to include:**
- The shared navbar.
- A form with a single numeric input labelled "Amount to Deposit". The input type should be `number` with a minimum value attribute of `0.01` to hint to the browser that only positive values are allowed (though server-side validation is the real guard).
- A submit button.
- A success message area that shows the confirmed deposit amount and the updated balance when the route passes a success result.
- An error message area that shows validation or business logic errors.
- A "Back to Dashboard" link so the customer does not have to use the browser back button.

---

### 3.5 Withdraw Page (`withdraw.html`)

**Purpose:** Let the customer enter an amount to deduct from their balance.

**What to include:**
- The shared navbar.
- Display the current available balance at the top of the form so the customer knows their limit before entering an amount.
- A form with a single numeric input labelled "Amount to Withdraw".
- A submit button.
- A success message showing the withdrawn amount and new remaining balance.
- An error message for insufficient funds or invalid input — the wording should be specific, e.g., "You cannot withdraw more than your available balance of $X".
- A "Back to Dashboard" link.

---

## 4. Integration Steps

### 4.1 Connect Flask to the Frontend Templates

Flask must know where the templates folder is. When you create the Flask app object in `app.py`, pass the `template_folder` argument pointing to the relative path of `FRONTEND/templates` from `BACKEND/app.py`. This is typically `../FRONTEND/templates`.

Once configured, every call to `render_template("dashboard.html", ...)` will look in that folder for the file.

Verify this works by adding a temporary root route that renders `login.html` and running the app. If the page loads in the browser, the path is correctly configured.

---

### 4.2 Connect Flask to the SQLite Database

The SQLite database file path is set in `models.py`. Define a constant at the top of that file that holds the path to `banking.db` relative to `models.py`'s own location — using `os.path` to resolve it dynamically ensures it works regardless of where you launch the app from.

Use Python's built-in `sqlite3` module. The standard pattern is:
1. Open a connection with `sqlite3.connect(DB_PATH)`.
2. Set `connection.row_factory = sqlite3.Row` so that query results behave like dictionaries — you can then access columns by name instead of index, making the code more readable.
3. Execute the query and fetch results.
4. Always close the connection when done, or use a `with` block to close it automatically.

There is no ORM involved — plain SQL strings are fine for an application of this size.

---

### 4.3 Wire HTML Forms to Flask Routes

For each form in the frontend:

- The form's `method` attribute must be `"POST"` for any action that changes data (login, deposit, withdraw).
- The form's `action` attribute must match the Flask route URL exactly (e.g., `action="/deposit"`).
- Each input field's `name` attribute must match what the Flask route reads from `request.form`. Mismatched names are the most common integration bug — check them first if a route receives empty values.

For links (e.g., Logout, Back to Dashboard), use standard `<a>` tags pointing to the correct Flask route URL.

---

### 4.4 Pass Data from Flask to Templates

When a route calls `render_template`, it passes named keyword arguments that become variables inside the template. For example:

- The dashboard route fetches the customer's name and balance from `models.py`, then passes them as `customer_name=...` and `balance=...` to `render_template("dashboard.html", ...)`.
- Inside `dashboard.html`, reference them as `{{ customer_name }}` and `{{ balance }}`.
- For conditional content like error/success messages, pass a `message` and `message_type` variable and wrap the alert block in `{% if message %}`.

Keep the amount of logic inside templates minimal. Templates should only decide what to display — not compute values.

---

## 5. Validation Rules

### 5.1 Login Validation

Apply these checks in the `/login` POST route handler, in order:

| Check | Condition | Action if Failed |
|---|---|---|
| Fields not empty | Both username and password fields must contain at least one character | Re-render login with "Please enter your username and password" |
| Customer exists | `models.py` lookup returns a record | Re-render login with "Invalid username or password" (do not reveal which field was wrong) |
| Password matches | `auth.py` verify returns `True` | Re-render login with "Invalid username or password" |

Always use the same generic error message for both a missing user and a wrong password. Specific messages like "username not found" leak information and help attackers enumerate valid usernames.

---

### 5.2 Balance Validation

Apply these checks in the dashboard route and before any transaction:

| Check | Condition | Action if Failed |
|---|---|---|
| Customer id in session | `session["customer_id"]` exists and is not `None` | Redirect to `/login` |
| Balance is a valid number | The value returned from the database is numeric | Log the anomaly; display a generic error |

---

### 5.3 Deposit Validation

Apply these checks in `transactions.py`'s `process_deposit`, in order:

| Check | Condition | Action if Failed |
|---|---|---|
| Amount is present | The submitted form value is not empty or blank | Return failure with "Please enter an amount" |
| Amount is numeric | The value can be safely converted to a float | Return failure with "Amount must be a number" |
| Amount is positive | The converted value is greater than zero | Return failure with "Deposit amount must be greater than zero" |
| Amount is reasonable | Optionally, the amount does not exceed a maximum single-transaction limit | Return failure with the limit message |

After all checks pass, proceed with the balance update.

---

### 5.4 Withdrawal Validation

Apply these checks in `transactions.py`'s `process_withdrawal`, in order:

| Check | Condition | Action if Failed |
|---|---|---|
| Amount is present | The submitted form value is not empty or blank | Return failure with "Please enter an amount" |
| Amount is numeric | The value can be safely converted to a float | Return failure with "Amount must be a number" |
| Amount is positive | The converted value is greater than zero | Return failure with "Withdrawal amount must be greater than zero" |
| Sufficient funds | The current balance is greater than or equal to the requested amount | Return failure with "Insufficient funds. Your available balance is $X" |

The insufficient-funds error message should include the actual balance so the customer knows exactly what they have available.

---

## 6. Testing

### 6.1 Unit Tests

Unit tests verify individual functions in isolation, without running the Flask server or touching the real database. Create a `tests/` folder inside `BACKEND/` and a file named `test_unit.py`.

**What to unit test:**

| Function | Test Cases |
|---|---|
| `auth.hash_password` | Output is not equal to the plain input; output is a non-empty string |
| `auth.verify_password` | Returns `True` when plain matches hash; returns `False` for wrong password |
| `transactions.process_deposit` | Accepts valid positive amount; rejects zero; rejects negative; rejects non-numeric |
| `transactions.process_withdrawal` | Accepts amount ≤ balance; rejects amount > balance; rejects zero; rejects non-numeric |

For transaction tests, do not connect to the real database. Instead, replace the `models.py` functions with simple test doubles (stubs) that return a fixed balance value. This keeps tests fast and deterministic.

---

### 6.2 Integration Tests

Integration tests verify that multiple components work correctly together — Flask routes, business logic, and the database. Use Flask's built-in `test_client()` to simulate HTTP requests without a real browser.

Create `test_integration.py` in the `tests/` folder. Before each test, create a fresh in-memory SQLite database (using `":memory:"` as the path) and seed it with one test customer.

**What to integration test:**

| Scenario | Steps | Expected Result |
|---|---|---|
| Successful login | POST to `/login` with valid credentials | Redirects to `/dashboard`; session contains customer id |
| Failed login — wrong password | POST to `/login` with wrong password | Stays on login page; error message visible |
| Dashboard requires login | GET `/dashboard` without a session | Redirects to `/login` |
| Successful deposit | Login, then POST to `/deposit` with a valid amount | Balance increases; success message shown |
| Deposit with zero amount | Login, then POST to `/deposit` with amount = 0 | Error message shown; balance unchanged |
| Successful withdrawal | Login, then POST to `/withdraw` with amount ≤ balance | Balance decreases; success message shown |
| Overdraft withdrawal | Login, then POST to `/withdraw` with amount > balance | Error message shown; balance unchanged |
| Logout | GET `/logout` while logged in | Session is cleared; redirects to `/login` |

---

### 6.3 Manual Testing Checklist

Run through this checklist in the browser after each development phase to catch issues that automated tests might miss:

**Authentication**
- [ ] Visiting `/dashboard` while logged out redirects to `/login`
- [ ] Submitting empty login form shows a validation error
- [ ] Submitting wrong credentials shows a generic error (does not reveal which field was wrong)
- [ ] Submitting correct credentials redirects to the dashboard
- [ ] Clicking Logout returns to the login page and clears the session (test by using the browser back button — should not grant access)

**Dashboard**
- [ ] Dashboard shows the correct customer name
- [ ] Dashboard shows the correct current balance
- [ ] Deposit and Withdraw buttons navigate to the correct pages

**Deposit**
- [ ] Submitting a valid deposit amount increases the balance and shows a success message
- [ ] Submitting zero or a negative amount shows an error message
- [ ] Submitting a non-numeric value shows an error message
- [ ] Balance on dashboard reflects the deposit after returning to it

**Withdrawal**
- [ ] Submitting a valid withdrawal amount decreases the balance and shows a success message
- [ ] Submitting an amount greater than the balance shows an "insufficient funds" error
- [ ] Submitting zero or a negative amount shows an error message
- [ ] Balance on dashboard reflects the withdrawal after returning to it

**General**
- [ ] All pages display correctly on a standard desktop browser width
- [ ] All pages display correctly at tablet width (≈768px)
- [ ] No unhandled Python exceptions appear in the terminal during any of the above steps

---

## 7. Deployment

### 7.1 Run Locally

Follow these steps every time you want to start the application on your development machine:

1. Open a terminal and navigate to the `BACKEND/` folder.
2. Activate the virtual environment (see Section 1.3).
3. If running for the first time, or after deleting `banking.db`, run `python seed.py` to create and populate the database.
4. Start the Flask development server with `python app.py`.
5. Flask will print the local URL — typically `http://127.0.0.1:5000`. Open this in your browser.
6. To stop the server, press `Ctrl+C` in the terminal.

**Important:** The Flask development server (`debug=True`) is single-threaded and not hardened against malicious input. It is intended for local development only — never expose it directly to the internet.

---

### 7.2 Environment Variables for Configuration

Before moving toward any shared or production-like environment, move sensitive configuration out of source code:

- **Secret key:** store it in an environment variable (e.g., `FLASK_SECRET_KEY`) and read it in `app.py` with `os.environ.get(...)`. Fall back to a hard-coded development value only when the variable is not set.
- **Database path:** consider making the `banking.db` path configurable via an environment variable so the database can be placed outside the source directory if needed.
- **Debug flag:** ensure `debug=True` is not active in any shared environment. Read the debug flag from an environment variable too.

---

### 7.3 Production Considerations

The Flask development server is not production-ready. If this application were to be hosted for real users, the following changes would be required:

| Concern | Development Approach | Production Approach |
|---|---|---|
| WSGI Server | Flask built-in server | Gunicorn or uWSGI |
| Database | SQLite file | PostgreSQL or MySQL |
| Secret Key | Hard-coded string | Randomly generated, stored in secret manager |
| HTTPS | Not configured | TLS certificate via reverse proxy (nginx) |
| Debug mode | `debug=True` | `debug=False`; structured logging instead |
| Static files | Served by Flask | Served by nginx or a CDN |

For this workshop scope, local execution with the Flask dev server is entirely sufficient. The items above are listed for awareness, not as required tasks.

---

*End of Step-by-Step Implementation Guide*
