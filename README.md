# Revoshop

A simple e-commerce backend application for learning Flask, SQLAlchemy, and PostgreSQL fundamentals.

## Overview

Revoshop is a hands-on learning project demonstrating core backend concepts including database design, API endpoints, CRUD operations, relationships, constraints, and indexing in PostgreSQL.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python, Flask |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migration | Flask-Migrate |
| Password Hashing | bcrypt |
| Testing | pytest, requests |

## Features

- ✅ User Management (register, authentication)
- ✅ Product Management (CRUD operations)
- ✅ Product Categories
- ✅ Order Management
- ✅ Validation & Error Handling
- ✅ RESTful API Endpoints

## Project Structure

```
revoshop/
├── models/                 # Database models
│   ├── user.py            # User model with authentication
│   ├── product.py         # Product model with validation
│   ├── category.py        # Category model
│   └── order.py           # Order model
├── routes/                # API endpoints
│   ├── users.py           # User endpoints (register, get)
│   └── products.py        # Product endpoints (CRUD)
├── seeders/               # Database seeding
│   └── seeders.py         # Populate test data
├── tests/                 # Automated tests
│   └── test_endpoints.py  # Test all API endpoints
├── migrations/            # Database migrations (Flask-Migrate)
├── app.py                 # Flask application entry point
├── utils.py               # Database utilities
├── run_server.py          # Start development server
├── run_tests.py           # Run test suite
└── requirements.txt       # Python dependencies
```

## Database Schema

### Tables

| Table | Purpose |
|-------|---------|
| `users` | Store user accounts with authentication |
| `categories` | Store product categories |
| `products` | Store product information |
| `orders` | Store customer orders |
| `order_items` | Store products in each order |

### Database Diagram

![Schema Diagram](./images/diagram.png)

## Setup

### 1. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. PostgreSQL Setup

**macOS (Homebrew):**
```bash
brew install postgresql@18
brew services start postgresql@18
```

**Windows:** Download from [postgresql.org](https://www.postgresql.org/download/windows/)

**Create Database:**
```bash
psql -U postgres -c "CREATE DATABASE revoshop_db;"
```

### 3. Configure Environment

Copy `.env.example` to `.env` and update the database URL:

```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/revoshop_db
DATABASE_TRACK_MODIFICATION=False
```

### 4. Initialize Database

```bash
# Create tables from migrations
flask db upgrade

# Or using direct SQL
psql -U postgres -d revoshop_db -f schema.sql
psql -U postgres -d revoshop_db -f seed.sql
```

## Usage

### Start Development Server

```bash
# Default port 5000 (may conflict on macOS)
python3 run_server.py

# Or use custom port
python3 run_server.py 5001
```

Server runs on: `http://localhost:5001`

### Seed Test Data

```bash
python3 -m seeders.seeders
```

This creates:
- 5 test users (john_doe, jane_smith, etc.)
- 5 product categories
- 10 sample products

### Run Tests

```bash
# Terminal 1: Start server
python3 run_server.py 5001

# Terminal 2: Run tests
FLASK_TEST_URL=http://localhost:5001 python3 tests/test_endpoints.py
```

Test coverage:
- ✅ User registration and retrieval
- ✅ Product CRUD operations
- ✅ Error handling and validation
- ✅ API response times

## API Endpoints

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/register` | Register new user |
| GET | `/users/<id>` | Get user by ID |

**Register User:**
```json
POST /users/register
{
  "username": "ken",
  "email": "ken@gmail.com",
  "password": "12345",
  "role": "user"
}
```

**Response (201 Created):**
```json
{
	"data": {
		"created_at": "2026-08-15T16:11:28.672574",
		"email": "ken@gmail.com",
		"id": 34,
		"last_login": null,
		"role": "user",
		"username": "ken"
	},
	"message": "user created",
	"status": true
}
```

**Test Result:** ✅ Success - User registered with ID=34

**Insomnia Screenshot:**
![Register User](./images/tests/register%20user.png)

---

**Error Case - Duplicate Username (409):**
```json
{
  "message": "username already exists",
  "status": false,
  "error": "this username is already registered"
}
```

---

**Get User:**
```bash
GET /users/1
```

**Response (200 OK):**
```json
{
	"data": {
		"created_at": "2026-08-15T16:03:10.325628",
		"email": "alice@example.com",
		"id": 24,
		"last_login": "2026-08-14T16:03:09.933791",
		"role": "user",
		"username": "alice_brown"
	},
	"message": "success get user data",
	"status": true
}
```

**Test Result:** ✅ Success - User data retrieved

**Insomnia Screenshot:**
![Get User Success](./images/tests/get%20user%20by%20id%20success.png)

**Test Result:** 😔 Success - User not found

**Insomnia Screenshot:**
![Get User Failed](./images/tests/get%20user%20by%20id%20failed.png)

---

### Products

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/products/` | Get all products |
| POST | `/products/` | Create new product |
| GET | `/products/<id>` | Get product by ID |
| PUT | `/products/<id>` | Update product |
| DELETE | `/products/<id>` | Delete product |

**Get All Products:**
```bash
GET /products/
```

**Response (200 OK):**
```json
{
  "message": "get all products success",
  "status": true,
  "data": [
    {
      "id": 1,
      "name": "Laptop Pro 15\"",
      "description": "High-performance laptop with 16GB RAM and 512GB SSD",
      "price": "1299.99",
      "stock": 15,
      "category_id": 1,
      "created_at": "2026-08-15T15:31:36.864394"
    },
    {
      "id": 2,
      "name": "Wireless Mouse",
      "description": "Ergonomic wireless mouse with long battery life",
      "price": "29.99",
      "stock": 50,
      "category_id": 1,
      "created_at": "2026-08-15T15:31:36.864400"
    }
  ]
}
```

**Test Result:** ✅ Success - Retrieved 10 products

**Insomnia Screenshot:**
![Get All Products](./images/tests/get%20all%20products.png)

---

**Create Product:**
```json
POST /products/
{
  "name": "Mechanical Keyboard RGB",
  "description": "Premium mechanical keyboard with RGB backlighting",
  "price": 199.99,
  "stock": 25,
  "category_id": 1
}
```

**Response (201 Created):**
```json
{
  "message": "product created",
  "status": true,
  "data": {
    "id": 34,
    "name": "Mechanical Keyboard RGB",
    "description": "Premium mechanical keyboard with RGB backlighting",
    "price": "199.99",
    "stock": 25,
    "category_id": 1,
    "created_at": "2026-08-15T16:15:30.123456"
  }
}
```

**Test Result:** ✅ Success - Product created with ID=34

---

**Error Case - Invalid Price (400):**
```json
POST /products/
{
  "name": "Invalid Product",
  "price": -50.00,
  "stock": 10
}
```

**Response (400 Bad Request):**
```json
{
  "message": "product price must be greater than 0",
  "status": false
}
```

**Test Result:** ❌ Failed as expected - Price validation working

---

**Get Single Product:**
```bash
GET /products/1
```

**Response (200 OK):**
```json
{
  "message": "success get product",
  "status": true,
  "data": {
    "id": 1,
    "name": "Laptop Pro 15\"",
    "description": "High-performance laptop with 16GB RAM and 512GB SSD",
    "price": "1299.99",
    "stock": 15,
    "category_id": 1,
    "created_at": "2026-08-15T15:31:36.864394"
  }
}
```

**Test Result:** ✅ Success - Product retrieved

**Insomnia Screenshot:**
![Get Product by ID Success](./images/tests/get%20products%20by%20id%20success.png)

**Test Result:** 😔 Failed - Product not found

**Insomnia Screenshot:**
![Get Product by ID Success](./images/tests/get%20product%20by%20id%20failed.png)


---

**Update Product:**
```json
PUT /products/1
{
  "name": "Laptop Pro 15\" 2026",
  "price": 1399.99,
  "stock": 12
}
```

**Response (200 OK):**
```json
{
  "message": "success update product",
  "status": true,
  "data": {
    "id": 1,
    "name": "Laptop Pro 15\" 2026",
    "description": "High-performance laptop with 16GB RAM and 512GB SSD",
    "price": "1399.99",
    "stock": 12,
    "category_id": 1,
    "created_at": "2026-08-15T15:31:36.864394"
  }
}
```

**Test Result:** ✅ Success - Product updated

---

**Delete Product:**
```bash
DELETE /products/34
```

**Response (200 OK):**
```json
{
  "message": "success delete product",
  "status": true
}
```

**Test Result:** ✅ Success - Product deleted

---

**Error Case - Not Found (404):**
```bash
DELETE /products/99999
```

**Response (404 Not Found):**
```json
{
  "message": "product not found",
  "status": false
}
```

**Test Result:** ❌ Not found as expected

## Example Usage

```bash
# Get all products
curl http://localhost:5001/products/

# Register new user
curl -X POST http://localhost:5001/users/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "email": "alice@example.com",
    "password": "password123"
  }'

# Create product
curl -X POST http://localhost:5001/products/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wireless Mouse",
    "price": 29.99,
    "stock": 50,
    "category_id": 1
  }'
```

## Test Data

Default test users (password = username + digits, see seeders.py):
- `john_doe` (admin)
- `jane_smith` (user)
- `bob_wilson` (user)
- `alice_brown` (user)
- `charlie_davis` (seller)

## Troubleshooting

**Port 5000 already in use:**
```bash
python3 run_server.py 5001  # Use different port
```

**Database connection error:**
- Verify PostgreSQL is running: `brew services list`
- Check `.env` DATABASE_URL is correct
- Ensure database exists: `psql -l`

**Module not found errors:**
```bash
pip3 install -r requirements.txt
```

## Files Reference

| File | Purpose |
|------|---------|
| `schema.sql` | Database table definitions |
| `seed.sql` | Sample data |
| `queries.sql` | Example SQL queries |
| `requirements.txt` | Python package dependencies |
| `.env.example` | Environment variable template |