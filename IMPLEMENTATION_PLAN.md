# Banking Web Application — Implementation Plan

> **Status:** Planning  
> **Technology:** HTML + Bootstrap (Frontend) · Python Flask (Backend) · SQLite (Database)

---

## 1. Solution Overview

### Objective

Build a lightweight, browser-based banking web application that allows registered customers to securely log in, view their account balance, and perform basic financial transactions (deposit and withdrawal) through a simple dashboard interface.

### Scope

| In Scope | Out of Scope |
|---|---|
| Customer login / logout | New customer self-registration |
| Dashboard with account summary | Multi-account support per customer |
| View current balance | Fund transfers between accounts |
| Deposit funds | External payment gateway integration |
| Withdraw funds | Admin / teller portal |
| Session-based access control | Mobile-native application |

### Users

- **Customer** — An existing bank customer who has a pre-created account. All application features are scoped to this single user role.

### Functional Requirements

1. A customer must authenticate with a username and password before accessing any page.
2. After successful login, the customer is directed to a personal dashboard.
3. The dashboard displays the customer's name and current account balance.
4. The customer can deposit a positive monetary amount; the balance updates immediately.
5. The customer can withdraw a positive monetary amount up to the current available balance.
6. The customer can log out, which terminates their session and redirects to the login page.
7. All protected pages redirect unauthenticated users to the login page.

### Non-Functional Requirements

| Category | Requirement |
|---|---|
| Security | Passwords stored as hashed values; session tokens managed server-side |
| Usability | Responsive layout using Bootstrap; works on desktop and tablet |
| Reliability | Atomic transaction writes to prevent partial balance updates |
| Maintainability | Clear separation between frontend templates and backend logic |
| Portability | SQLite file-based database; no external database server required |
| Performance | All pages load within 2 seconds on a standard development machine |

### Assumptions

- Customer accounts are pre-seeded in the database; no self-registration flow is required.
- A single SQLite file serves as the database for the entire application lifecycle.
- The application runs on `localhost` during development; no production hosting is in scope.
- Bootstrap is loaded via CDN; no Node.js / npm build step is required.
- Python 3.10+ and Flask are available in the development environment.
- A single active session per customer is sufficient (no concurrent session management).

---

## 2. High-Level Architecture

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          BROWSER                                │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │              FRONTEND  (FRONTEND/)                       │  │
│   │                                                          │  │
│   │   HTML Templates (Jinja2)   +   Bootstrap CSS/JS (CDN)   │  │
│   │                                                          │  │
│   │   login.html · dashboard.html · deposit.html            │  │
│   │   withdraw.html                                          │  │
│   └──────────────────────┬───────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           │  HTTP Request / Response
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKEND  (BACKEND/)                          │
│                                                                 │
│   Flask Application                                             │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│   │  Auth Routes │  │  Dashboard   │  │  Transaction Routes  │ │
│   │  /login      │  │  /dashboard  │  │  /deposit            │ │
│   │  /logout     │  │              │  │  /withdraw           │ │
│   └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘ │
│          │                 │                      │             │
│   ┌──────▼─────────────────▼──────────────────────▼───────────┐ │
│   │              Business Logic Layer                          │ │
│   │   authenticate_user · get_balance · apply_transaction     │ │
│   └──────────────────────────┬─────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
                               │  SQL via sqlite3 / SQLAlchemy
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE  (BACKEND/)                         │
│                                                                 │
│   SQLite File  (banking.db)                                     │
│   ┌────────────────────┐  ┌──────────────────────────────────┐  │
│   │  customers table   │  │  transactions table              │  │
│   │  id, username,     │  │  id, customer_id, type,          │  │
│   │  password_hash,    │  │  amount, timestamp               │  │
│   │  name, balance     │  │                                  │  │
│   └────────────────────┘  └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Frontend → Backend → Database Interaction

| Layer | Role in a Request |
|---|---|
| Browser | Sends an HTTP form POST or GET to a Flask route |
| Flask Route | Validates session, delegates to business logic |
| Business Logic | Reads or writes data via the database layer |
| SQLite | Persists or returns the requested data |
| Flask Template | Renders the HTML response returned to the browser |

### Request Lifecycle

1. **Browser** submits a form (e.g. login credentials or deposit amount).
2. **Flask route handler** receives the request, checks session validity.
3. **Business logic function** applies rules (e.g. balance ≥ withdrawal amount).
4. **SQLite** is queried or updated atomically.
5. **Flask** renders a Jinja2 template with updated data and returns the HTTP response.
6. **Browser** displays the rendered page to the customer.

---

## 3. Component Design

### Frontend Responsibilities

- Render all user-facing pages using HTML and Jinja2 templating (served by Flask).
- Apply consistent layout, typography, and responsiveness via Bootstrap 5 (CDN).
- Present form inputs for login, deposit, and withdrawal.
- Display feedback messages (success, error, validation notices) using Bootstrap alert components.
- Redirect the browser to the appropriate route on form submission.
- No client-side business logic — all decisions are made server-side.

### Backend Responsibilities

- Expose HTTP routes that map to each application feature.
- Manage user sessions using Flask's server-side session mechanism.
- Enforce authentication on every protected route.
- Execute business rules (e.g. insufficient funds check before withdrawal).
- Interact with the SQLite database for all reads and writes.
- Return rendered HTML templates or redirect responses to the browser.
- Hash and verify passwords securely.

### Database Responsibilities

- Persist customer credentials, names, and current account balances.
- Record an immutable log of all deposit and withdrawal transactions.
- Provide atomic updates to prevent inconsistent balance states.
- Serve as the single source of truth for all application data.

---

## 4. Folder Structure

```
banking-workshop/
│
├── IMPLEMENTATION_PLAN.md          ← This document
│
├── FRONTEND/                       ← All HTML templates (rendered by Flask/Jinja2)
│   └── templates/
│       ├── login.html              ← Login form page
│       ├── dashboard.html          ← Account summary / home page after login
│       ├── deposit.html            ← Deposit funds form
│       └── withdraw.html           ← Withdraw funds form
│
└── BACKEND/                        ← All server-side Python code and data
    ├── app.py                      ← Flask application entry point; route definitions
    ├── models.py                   ← Database models / data access functions
    ├── auth.py                     ← Authentication helpers (hashing, verification)
    ├── transactions.py             ← Deposit and withdrawal business logic
    ├── requirements.txt            ← Python dependency list
    ├── banking.db                  ← SQLite database file (created at runtime)
    └── seed.py                     ← One-time script to seed initial customer data
```

### Folder Responsibilities

| Path | Responsibility |
|---|---|
| `FRONTEND/templates/` | Jinja2 HTML templates rendered and served by Flask |
| `BACKEND/app.py` | Application factory, route registration, session config |
| `BACKEND/models.py` | All database interactions; abstracts raw SQL from routes |
| `BACKEND/auth.py` | Password hashing and credential verification utilities |
| `BACKEND/transactions.py` | Deposit / withdrawal rules and atomic balance updates |
| `BACKEND/seed.py` | Populates the database with initial customer accounts |
| `BACKEND/banking.db` | SQLite data file; created automatically on first run |
| `BACKEND/requirements.txt` | Declares Flask and any other Python dependencies |

---

## 5. Module Breakdown

### Authentication Module

**Purpose:** Control access to the application — only verified customers may reach protected pages.

| Concern | Detail |
|---|---|
| Login | Accept username + password, verify against stored hash, create session |
| Logout | Destroy the active session, redirect to login page |
| Session Guard | Decorator / check applied to every protected route |
| Password Security | Passwords stored as salted hashes (e.g. `werkzeug.security`) |

**Pages:** `login.html`  
**Routes:** `GET/POST /login`, `GET /logout`

---

### Dashboard Module

**Purpose:** Provide the customer's home screen after login — a summary of their account.

| Concern | Detail |
|---|---|
| Identity | Display the logged-in customer's full name |
| Balance | Show the current account balance |
| Navigation | Provide links to Deposit and Withdraw actions |

**Pages:** `dashboard.html`  
**Routes:** `GET /dashboard`

---

### Account Management Module

**Purpose:** Give the customer a read-only view of their account information.

| Concern | Detail |
|---|---|
| Balance Retrieval | Query the database for the customer's current balance |
| Data Binding | Pass balance and customer name to the dashboard template |

> This module's responsibilities are fulfilled within the Dashboard module for this application scope.

---

### Transactions Module

**Purpose:** Handle all money-movement operations with appropriate validation.

| Concern | Detail |
|---|---|
| Deposit | Accept an amount > 0; add to balance; record transaction |
| Withdrawal | Accept an amount > 0 and ≤ current balance; deduct; record transaction |
| Validation | Reject non-positive amounts; reject overdrafts |
| Feedback | Communicate success or failure back to the customer via the UI |
| Audit Log | Every transaction is written to the transactions table with a timestamp |

**Pages:** `deposit.html`, `withdraw.html`  
**Routes:** `GET/POST /deposit`, `GET/POST /withdraw`

---

## 6. Implementation Roadmap

### Development Phases

#### Phase 1 — Project Scaffolding
**Goal:** Establish the folder structure and environment baseline.

| Task | Dependency |
|---|---|
| Create `FRONTEND/templates/` and `BACKEND/` directories | None |
| Create `requirements.txt` and install Flask | None |
| Create `app.py` with minimal Flask app and health-check route | `requirements.txt` |
| Create `banking.db` via `seed.py` with at least one test customer | `app.py`, `models.py` |

**Estimated Effort:** Small  
**Status:** `[ ] pending`

---

#### Phase 2 — Authentication
**Goal:** Customers can log in and log out; all routes are protected.

| Task | Dependency |
|---|---|
| Implement `auth.py` (hash + verify) | Phase 1 |
| Implement `models.py` customer lookup | Phase 1 |
| Build `/login` route and `login.html` template | Phase 1 |
| Build `/logout` route | `/login` route |
| Add session guard to protect all non-login routes | `/login` route |

**Estimated Effort:** Small–Medium  
**Status:** `[ ] pending`

---

#### Phase 3 — Dashboard
**Goal:** Authenticated customers land on a dashboard showing their balance.

| Task | Dependency |
|---|---|
| Build `/dashboard` route | Phase 2 |
| Build `dashboard.html` template with Bootstrap layout | Phase 2 |
| Display customer name and balance from database | `models.py` |
| Add navigation links to Deposit / Withdraw | `dashboard.html` |

**Estimated Effort:** Small  
**Status:** `[ ] pending`

---

#### Phase 4 — Transactions
**Goal:** Customers can deposit and withdraw funds with validation and balance updates.

| Task | Dependency |
|---|---|
| Implement `transactions.py` deposit logic | Phase 3 |
| Implement `transactions.py` withdrawal logic with overdraft guard | Phase 3 |
| Build `/deposit` route and `deposit.html` template | `transactions.py` |
| Build `/withdraw` route and `withdraw.html` template | `transactions.py` |
| Write transaction records to the database on each operation | `models.py` |
| Display success / error feedback on the page | Templates |

**Estimated Effort:** Medium  
**Status:** `[ ] pending`

---

#### Phase 5 — Integration & Polish
**Goal:** End-to-end flow works smoothly; UI is consistent and user-friendly.

| Task | Dependency |
|---|---|
| Apply consistent Bootstrap navbar / layout across all pages | Phases 2–4 |
| Test full login → dashboard → deposit → withdraw → logout flow | Phases 2–4 |
| Verify session expiry redirects unauthenticated users correctly | Phase 2 |
| Verify overdraft and negative-amount validation | Phase 4 |

**Estimated Effort:** Small  
**Status:** `[ ] pending`

---

### Dependency Summary

```
Phase 1 (Scaffolding)
    └── Phase 2 (Authentication)
            └── Phase 3 (Dashboard)
                    └── Phase 4 (Transactions)
                                └── Phase 5 (Integration & Polish)
```

Each phase builds directly on the previous one; no phases can run in parallel.

---

*End of Implementation Plan*
