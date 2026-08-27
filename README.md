# Revoshop

An e-commerce backend API built with Flask, demonstrating a layered architecture (routes → services → repositories), JWT authentication, and role-based access control.

## Overview

Revoshop is a hands-on learning project for backend fundamentals: database design, RESTful API design, validation, authentication, and automated testing. The codebase follows a clean separation of concerns with a service/repository pattern and schema-based validation.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python, Flask |
| API / OpenAPI | flask-smorest |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migration | Flask-Migrate |
| Validation | marshmallow |
| Auth | flask-jwt-extended, bcrypt |
| Testing | pytest, pytest-cov |

## Features

- User management (registration, JWT login/refresh)
- Role-based access control (buyer, seller, admin)
- Product management (CRUD, filtering, pagination)
- Product categories (CRUD, optional nested products)
- Order management (creation with stock deduction, status transitions, cancel/refund)
- Schema-based validation and centralized error handling

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
├── migrations/                # Flask-Migrate migrations
├── seeders/                   # database seeding
├── tests/
│   ├── conftest.py            # shared fixtures (app, db, client, seeders)
│   ├── unit/                  # fast, isolated tests (mocked repositories)
│   └── integration/           # full HTTP-through-stack tests
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

![Schema Diagram](./images/diagram-2.png)

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

### API Documentation (Swagger UI)

With the server running, open the flask-smorest Swagger UI:

```
http://localhost:5000/docs/swagger-ui
```

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
| POST | `/api/v1/products/` | Create a product | seller, admin |
| GET | `/api/v1/products/<id>` | Get a product | any role |
| PUT | `/api/v1/products/<id>` | Update a product | seller, admin |
| DELETE | `/api/v1/products/<id>` | Soft-delete a product | seller, admin |

### Orders

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/api/v1/orders/` | List orders (own orders; admin sees all) | any role |
| POST | `/api/v1/orders/` | Create an order (checks stock, deducts inventory) | buyer, admin |
| GET | `/api/v1/orders/<id>` | Get an order (owner or admin) | any role |
| PUT | `/api/v1/orders/<id>` | Update order status (validated transitions) | buyer, admin |
| DELETE | `/api/v1/orders/<id>` | Cancel an order (refunds stock where applicable) | buyer, admin |

**Order status transitions:**

```
waiting_for_payment → processing → shipped → delivered
        ↓                  ↓
    cancelled          cancelled
```

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

## Troubleshooting

**Database connection error:**
- Verify PostgreSQL is running: `brew services list`
- Check `DATABASE_URL` in `.env`
- Ensure the database exists: `psql -l`

**Module not found errors:**
```bash
pip3 install -r requirements.txt
```
