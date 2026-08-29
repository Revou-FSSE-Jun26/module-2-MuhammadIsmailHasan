# Revoshop

An e-commerce backend API built with Flask, demonstrating a layered architecture (routes → services → repositories), JWT authentication, and role-based access control.

## Overview

Revoshop is a hands-on learning project for backend fundamentals: database design, RESTful API design, validation, authentication, automated testing (unit + integration), and load testing. The codebase follows a clean separation of concerns with a service/repository pattern and schema-based validation.

## Users & Roles

Revoshop is a marketplace with three kinds of users. Every account has exactly
one role, stored on the user and carried inside the JWT, which determines what
that account is allowed to do.

| Role | Who they are | What they can do |
|------|--------------|------------------|
| **buyer** | A customer who shops on the platform | Browse products and categories, place orders, view their **own** orders, and cancel their own orders (via `DELETE`). Buyers **cannot** advance an order's status. |
| **seller** | A merchant who supplies the catalog | Browse products and categories, create / update / delete products and categories, advance the fulfillment status of orders that contain **their own** products, and cancel those orders (via `DELETE`). Sellers do **not** place orders. |
| **admin** | A platform operator | Full access: everything a buyer and seller can do, plus acting on **any** user's orders and deleting **any** user account. |

Notes:

- **Self-registration** creates only `buyer` or `seller` accounts. The `admin`
  role is privileged and is provisioned separately (e.g. via the seeder), not
  through the public registration endpoint.
- **Ownership matters even within a role.** A buyer can only touch their own
  orders; a seller can only change the status of orders that include one of
  their own products; only an admin can act across all users and orders.
- **Products have an owner.** When a seller creates a product it is stamped
  with their `seller_id`. This ownership is what scopes a seller's control
  over order status. Products created before this feature have no owner
  (`seller_id` is null), so only an admin can change the status of orders
  built from them.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python, Flask |
| API / OpenAPI | flask-smorest |
| Database | PostgreSQL (psycopg2) |
| ORM | SQLAlchemy |
| Migration | Flask-Migrate (Alembic) |
| Validation | marshmallow |
| Auth | flask-jwt-extended, bcrypt |
| Unit & integration testing | pytest, pytest-cov |
| Performance testing | Locust |
| Security linting | Bandit |
| Code quality / linting | Pylint |
| Dependency audit | pip-audit |
| Logging | Python logging (daily rotating file) |
| API documentation | Postman, Swagger UI (flask-smorest) |

## Features

- User management (registration, JWT login/refresh)
- Role-based access control (buyer, seller, admin)
- Product management (CRUD, filtering, sorting, pagination)
- Product categories (CRUD, optional nested products)
- Order management (creation with stock deduction, status transitions, cancel/refund)
- Schema-based validation and centralized error handling

## Business Logic

The main rules the system enforces:

**Users**

- Passwords are stored securely (hashed), never in plain text.
- Usernames and emails must be unique.
- You can delete your own account; admins can delete anyone.

**Categories**

- Category names must be unique.
- Deleting a category hides it instead of erasing it.

**Products**

- A product's category must exist.
- A product is owned by the seller who created it (`seller_id`). Admin-created
  products are owned by that admin.
- Each product has a unique `slug` generated automatically from its name at
  creation (e.g. `Laptop Pro 15"` → `laptop-pro-15`). Duplicate names get a
  numeric suffix (`gadget-x`, `gadget-x-2`). The slug is fixed once set —
  renaming a product does not change it, so links stay stable. Products can be
  fetched by slug via `GET /products/slug/<slug>`.
- A product can't be deleted while it's part of an active order.
- Deleting a product hides it instead of erasing it.

**Orders**

- You can only order what's in stock; if any item runs short, the whole order is rejected.
- Prices and totals are calculated by the server from the product, not sent by the client.
- Placing an order reduces stock automatically.
- Buyers see and manage only their own orders; sellers see orders that contain their products; admins see and act on any order.
- Status progression and cancellation are two separate concerns handled by two
  different endpoints:

  ```
  waiting_for_payment → processing → shipped → delivered   (progression: PUT)
          │                  │
          └──────────────────┴──────────────→ cancelled    (cancellation: DELETE)
  ```

- **Progressing status (`PUT /orders/<id>`):** moves an order forward one step
  along `waiting_for_payment → processing → shipped → delivered`. Cancellation
  is **not** done here.

  | Role | Allowed |
  |------|---------|
  | buyer | Cannot change status. |
  | seller | Can advance orders that contain one of their own products. |
  | admin | Can advance any order. |

  A seller acting on an order with no product of theirs gets `403`. An illegal
  move (skipping a step, going backward) returns `400`. Once an order is
  `cancelled` or `delivered` it is terminal — any further status change returns
  `400` with "order is ... and can no longer be modified".

- **Cancelling (`DELETE /orders/<id>`):** the single cancel path for everyone.
  A buyer can cancel their own order; a seller can cancel an order containing
  one of their products; an admin can cancel any order. Cancellation is
  identical regardless of who triggers it: the order is set to `cancelled`,
  soft-deleted, and **the reserved stock is returned**. Cancelling from
  `processing` also returns a refund note. Shipped and delivered orders cannot
  be cancelled (`400`).

- **Audit:** every status change and cancellation records the acting user in
  the order's `updated_by` field.

## Architecture

Each domain (users, auth, categories, products, orders) is organized into layers:

```
Request → Route (flask-smorest MethodView)
        → Schema (marshmallow validation / serialization)
        → Service (business logic, custom exceptions)
        → Repository (data access)
        → Model (SQLAlchemy)
```

## Project Structure

```
module-2/
├── app/
│   ├── __init__.py            # Application factory (create_app)
│   ├── extensions.py          # db, jwt, migrate, api instances
│   ├── auth.py                # password hashing, roles_required decorator
│   ├── errors.py              # centralized HTTP + SQLAlchemy error handlers
│   ├── validation.py          # shared constants (e.g. ACTIVE_ORDER_STATUSES)
│   ├── models/                # SQLAlchemy models
│   │   ├── users.py
│   │   ├── categories.py
│   │   ├── products.py
│   │   └── orders.py
│   ├── schemas/               # marshmallow schemas (validation + serialization)
│   │   ├── user_schema.py
│   │   ├── category_schema.py
│   │   ├── product_schema.py
│   │   └── order_schema.py
│   ├── repositories/          # data access layer
│   │   ├── user_repository.py
│   │   ├── category_repository.py
│   │   ├── product_repository.py
│   │   └── order_repository.py
│   ├── services/              # business logic layer
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── category_service.py
│   │   ├── product_service.py
│   │   └── order_service.py
│   └── routes/                # flask-smorest blueprints (MethodView)
│       ├── auth.py
│       ├── users.py
│       ├── categories.py
│       ├── products.py
│       └── orders.py
├── config/                    # base / development / production configs
├── migrations/                # Flask-Migrate (Alembic) migrations
├── seeders/                   # database seeding (users, categories, products, orders)
├── tests/
│   ├── conftest.py            # shared fixtures (app, db, client, seeders)
│   ├── unit/                  # fast, isolated tests (mocked repositories)
│   │   ├── test_schemas.py
│   │   ├── test_user_service.py
│   │   ├── test_category_service.py
│   │   ├── test_product_service.py
│   │   └── test_order_service.py
│   └── integration/           # full HTTP-through-stack tests
│       ├── test_auth.py
│       ├── test_users.py
│       ├── test_categories.py
│       ├── test_products.py
│       └── test_orders.py
├── locust/
│   └── locustfile.py          # performance / load test (customer journey)
├── images/                    # diagrams and test-result evidence
├── run.py                     # application entry point
├── pytest.ini                 # pytest configuration
└── requirements.txt           # Python dependencies
```

## Database Schema

| Table | Purpose |
|-------|---------|
| `users` | User accounts with authentication and roles |
| `categories` | Product categories |
| `products` | Product information |
| `orders` | Customer orders |
| `order_items` | Line items within each order |

### Database Diagram

![Schema Diagram](./images/diagram-3.png)

## Setup

### 1. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 2. PostgreSQL

**macOS (Homebrew):**
```bash
brew install postgresql@18
brew services start postgresql@18
```

**Create the database:**
```bash
psql -U postgres -c "CREATE DATABASE revoshop_db;"
```

### 3. Configure environment

Copy `.env.example` to `.env` and set the database URL:

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/revoshop_db
```

### 4. Initialize the database

```bash
flask db upgrade
```

### 5. Seed test data (optional)

```bash
python3 -m seeders.seeders
```

## Running the App

```bash
# Uses FLASK_ENV (defaults to development)
python3 run.py

# Or with production config
FLASK_ENV=production python3 run.py
```

### API Documentation (Postman)

A published Postman collection documents every endpoint with example requests,
required headers, and sample request/response bodies. It also includes a login
request whose access token can be reused across the other authenticated calls.
Open it here:

<a href="https://documenter.getpostman.com/view/17905565/2sBYAsyCVE#e32c17ab-a8f1-4f09-a5d4-feabb2e874f8" target="_blank" rel="noopener noreferrer">Revoshop Postman Collection</a>

### API Documentation (Swagger UI)

With the server running, open the flask-smorest Swagger UI:

```
http://127.0.0.1:5000/docs/swagger-ui
```

## Response Format

All endpoints return a consistent JSON envelope. Every response includes a
boolean `status` and a human-readable `message`.

### Success

`status` is `true`. Endpoints that return a resource include a `data` field;
list endpoints add a `pagination` object; the login endpoint also returns tokens.

Single resource:

```json
{
  "status": true,
  "message": "success get product",
  "data": {
    "id": 1,
    "name": "Laptop Pro 15\"",
    "price": 1299.99,
    "stock": 15
  }
}
```

Paginated list:

```json
{
  "status": true,
  "message": "get all products success",
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total_items": 42,
    "total_pages": 5
  }
}
```

Login (tokens are returned alongside the user data):

```json
{
  "status": true,
  "message": "login successful",
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "data": { "id": 1, "username": "jane_smith", "email": "jane@example.com", "role": "buyer" }
}
```

### Error

`status` is `false` and `message` describes the problem. The HTTP status code
carries the category of the error.

```json
{
  "status": false,
  "message": "product not found"
}
```

| Status | When it occurs |
|--------|----------------|
| 400 | Bad request (e.g. deleting an order that cannot be cancelled) |
| 401 | Missing or invalid authentication token, or wrong login credentials |
| 403 | Authenticated but not allowed (wrong role, or not the resource owner) |
| 404 | Resource not found |
| 405 | HTTP method not allowed on the route |
| 409 | Conflict (e.g. duplicate category name, username, or email) |
| 422 | Validation error (invalid body/query) or insufficient stock |
| 500 | Unexpected server error |
| 503 | Database connection issue |

## API Endpoints

All endpoints are prefixed with `/api/v1`. Protected endpoints require a
`Authorization: Bearer <access_token>` header.

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Log in, returns access + refresh tokens |
| POST | `/api/v1/auth/refresh` | Get a new access token (refresh token required) |

### Users

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/api/v1/users/` | Register a new user | public |
| GET | `/api/v1/users/me` | Get current user | authenticated |
| GET | `/api/v1/users/<id>` | Get user by ID | authenticated |
| DELETE | `/api/v1/users/<id>` | Delete a user (own account or admin) | authenticated |

### Categories

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/v1/categories/` | List categories (filter, sort, paginate, `with_products`) | any role |
| POST | `/api/v1/categories/` | Create a category | seller, admin |
| GET | `/api/v1/categories/<id>` | Get a category with its products | any role |
| PUT | `/api/v1/categories/<id>` | Update a category | seller, admin |
| DELETE | `/api/v1/categories/<id>` | Soft-delete a category | seller, admin |

### Products

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/v1/products/` | List products (filter, sort, paginate) | any role |
| POST | `/api/v1/products/` | Create a product (owned by the creating seller/admin) | seller, admin |
| GET | `/api/v1/products/<id>` | Get a product by id (detail includes `seller_id`, `slug`) | any role |
| GET | `/api/v1/products/slug/<slug>` | Get a product by its slug | any role |
| PUT | `/api/v1/products/<id>` | Update a product | seller, admin |
| DELETE | `/api/v1/products/<id>` | Soft-delete a product | seller, admin |

### Orders

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/v1/orders/` | List orders (buyer: own; seller: containing their products; admin: all) | any role |
| POST | `/api/v1/orders/` | Create an order (checks stock, deducts inventory) | buyer, admin |
| GET | `/api/v1/orders/<id>` | Get an order (buyer owner, seller of a product in it, or admin) | any role |
| PUT | `/api/v1/orders/<id>` | Advance order status one step (seller scoped to own products; cannot cancel here) | seller, admin |
| DELETE | `/api/v1/orders/<id>` | Cancel an order: restores stock, soft-deletes, records `updated_by` | buyer, seller, admin |

**Order status transitions:**

```
waiting_for_payment → processing → shipped → delivered     (PUT: forward only)
        │                  │
        └──────────────────┴──────────────→ cancelled      (DELETE: cancel + restore stock)
```

`cancelled` and `delivered` are terminal. Cancelling is only allowed before an
order ships.

## Testing

Tests are split into fast unit tests (isolated, repositories mocked) and
integration tests (full HTTP stack against an in-memory SQLite database).

```bash
# Run everything (unit + integration)
python3 -m pytest

# Only unit tests (fast)
python3 -m pytest tests/unit/

# Only integration tests
python3 -m pytest tests/integration/

# A single file, class, or test
python3 -m pytest tests/unit/test_order_service.py
python3 -m pytest tests/unit/test_order_service.py::TestDelete
python3 -m pytest tests/integration/test_orders.py::TestCreateOrder::test_create_order_success

# Filter by keyword
python3 -m pytest -k "refund or insufficient"
```

> Tip: the development config enables `SQLALCHEMY_ECHO`, which prints every SQL
> statement during integration tests. Add `--log-level=WARNING` to quiet it.

### Coverage

```bash
# Terminal report with missing lines
python3 -m pytest --cov=app --cov-report=term-missing

# HTML report (open htmlcov/index.html afterwards)
python3 -m pytest --cov=app --cov-report=html
```

### Test Result

Full suite passing with a coverage report:

![Pytest Result](./images/tests/v2/pytest-20260829.png)

## Performance Testing (Locust)

A Locust load test in `locust/locustfile.py` simulates a realistic customer
journey with weighted tasks: browsing the catalog, viewing product details,
placing multi-product orders, and verifying the placed order. Each simulated
user logs in once, then repeats the journey.

### 1. Start the API and seed data

```bash
python3 -m seeders.seeders   # seed users, products, and orders
python3 run.py               # start the API (default: http://127.0.0.1:5000)
```

### 2. Run Locust

```bash
# Web UI at http://127.0.0.1:8089
locust -f locust/locustfile.py --host http://127.0.0.1:5000

# Headless: 10 users, spawn 2/s, run for 1 minute
locust -f locust/locustfile.py --host http://127.0.0.1:5000 \
    --users 10 --spawn-rate 2 --run-time 1m --headless
```

The test logs in as the seeded buyer (`jane@example.com`). Override the
credentials with the `LOCUST_EMAIL` and `LOCUST_PASSWORD` environment variables.


### Test Result

![Locust Result](./images/tests/v2/locust-20260829.png)

## Code Quality & Security

Three tools help keep the code clean and dependencies safe. They are configured
pragmatically (`.pylintrc` disables checks that do not apply to this codebase).

```bash
# Static security scan of the application code
bandit -r app

# Lint / code-quality report (uses .pylintrc)
pylint --rcfile=.pylintrc app

# Audit installed dependencies for known vulnerabilities
pip-audit
pip-audit -r requirements.txt
```

| Tool | Checks | Latest result |
|------|--------|---------------|
| Bandit | Security issues in our code | 0 issues |
| pip-audit | Known CVEs in dependencies | No known vulnerabilities |
| Pylint | Code quality / style | 9.66 / 10 |

## Logging

The app configures logging on startup (`app/logging_config.py`). Logs go to both
the console and a file at `logs/app.log`. The file rotates daily at midnight,
keeping the last 30 days (older files are named `app.log.YYYY-MM-DD`). The
`logs/` directory is git-ignored.

The log level follows the environment (`DEBUG` in development, `INFO` in
production) and can be overridden with environment variables:

```bash
LOG_LEVEL=WARNING      # console/file log level
LOG_TO_FILE=false      # disable file logging (console only)
LOG_DIR=logs           # directory for log files
LOG_FILE=app.log       # log file name
LOG_BACKUP_COUNT=30    # days of rotated logs to keep
```

Key events are logged, including application startup, login success/failure, and
order placement/cancellation.

## Troubleshooting

**Database connection error:**
- Verify PostgreSQL is running: `brew services list`
- Check `DATABASE_URL` in `.env`
- Ensure the database exists: `psql -l`

**Module not found errors:**
```bash
pip3 install -r requirements.txt
```
