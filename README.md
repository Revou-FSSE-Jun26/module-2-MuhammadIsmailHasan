# Revoshop

An e-commerce backend API built with Flask. It demonstrates a layered
architecture (routes → services → repositories), JWT auth, and role-based
access control.

## Live Demo

The API is deployed and publicly reachable:

**Base URL:** <https://revoshop-apis.onrender.com/>

- Health check: <https://revoshop-apis.onrender.com/api/v1/health>
- Swagger UI: <https://revoshop-apis.onrender.com/docs/swagger-ui>

> Hosted on Render's free tier, so the first request after a period of
> inactivity may take a few seconds while the instance wakes up.

### Try it with demo accounts

The deployment is seeded with the accounts below. Log in via
`POST /api/v1/auth/login` to get a token, then send it as
`Authorization: Bearer <access_token>` on protected routes. All demo accounts
share the password **`password123`**.

| Role | Email | Password |
|------|-------|----------|
| admin | `john@example.com` | `password123` |
| buyer | `jane@example.com` | `password123` |
| buyer | `bob@example.com` | `password123` |
| seller | `alice@example.com` | `password123` |
| seller | `charlie@example.com` | `password123` |

```bash
# Log in and grab a token
curl -X POST https://revoshop-apis.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "jane@example.com", "password": "password123"}'

# Use the returned access_token on a protected route
curl https://revoshop-apis.onrender.com/api/v1/orders/ \
  -H "Authorization: Bearer <access_token>"
```

> These are shared public demo credentials — please don't store anything
> sensitive. The data may be reset at any time.

## Overview

Revoshop is a marketplace backend where **buyers** shop and place orders,
**sellers** manage their own catalog and fulfill orders that contain their
products, and **admins** operate across the whole platform. It is built as a
hands-on study of backend fundamentals: relational data modeling, RESTful API
design, request validation, JWT authentication with role-based access control,
and a clean separation of concerns.

The codebase follows a layered flow — routes handle HTTP, marshmallow schemas
validate and serialize, services hold the business rules, and repositories own
data access — which keeps the logic testable and the layers swappable. It ships
with unit and integration tests, load testing, security/quality tooling, and a
Docker setup for both development and production.

## Features Implemented

- **Authentication & authorization** — registration, JWT login/refresh, and a
  `roles_required` guard enforcing buyer / seller / admin access.
- **Users & profiles** — account management plus a one-to-one profile (upsert).
- **Address book** — buyers keep many shipping addresses with exactly one
  enforced default; soft delete.
- **Categories & products** — full CRUD with filtering, sorting, and
  pagination; auto-generated stable slugs; seller ownership; soft delete.
- **Product images** — one-to-many with server-managed ordering (auto-append)
  and an atomic reorder endpoint; managed by the owning seller or an admin.
- **Orders** — buyer checkout with server-side pricing and stock deduction, a
  full status lifecycle (payment → fulfillment → delivery, plus cancel/return
  with restock and refund notes), a shipping-address snapshot, and soft delete.
- **Payments (Midtrans)** — buyer starts a payment, the API creates a Midtrans
  Snap transaction and returns the payment page URL, and a signature-verified
  webhook updates the payment and order when the status changes. One order can
  have many payment attempts, so a failed attempt lets the buyer retry without
  losing the order.
- **Shopping cart** — one lazy cart per buyer, grouped by seller, with
  live-computed totals and availability, plus whole / per-seller / partial
  checkout.
- **Platform** — a uniform JSON response envelope, centralized error handling,
  daily-rotating logs, a health check, and OpenAPI/Swagger docs.

## Tech Stack

Flask · flask-smorest · PostgreSQL · SQLAlchemy · Flask-Migrate · marshmallow ·
flask-jwt-extended / bcrypt · pytest · Locust · Bandit / Pylint / pip-audit ·
Docker

## Roles at a Glance

Every account has exactly one role, carried in the JWT.

| Role | Can do |
|------|--------|
| **buyer** | Shop, place orders, view/cancel/return their own orders. Cannot advance fulfillment. |
| **seller** | Manage their own products/categories, advance and cancel orders containing their products. Does not place orders. |
| **admin** | Act on any order or account. Does not place orders. |

Self-registration creates only `buyer` or `seller`; `admin` is provisioned via
the seeder. Ownership is scoped even within a role: a seller only controls
orders that include one of their own products.

## Order Lifecycle

Status changes and soft-deletion are two separate concerns on two endpoints.

```mermaid
stateDiagram-v2
    [*] --> waiting_for_payment
    waiting_for_payment --> paid: seller/admin confirms payment
    paid --> processing
    processing --> shipped: requires tracking_id
    shipped --> delivered
    delivered --> returned: buyer/admin

    waiting_for_payment --> cancelled
    paid --> cancelled
    processing --> cancelled

    cancelled --> [*]
    returned --> [*]
```

- **Advance / cancel / return — `PUT /orders/<id>`.** Moves the order to the
  next valid status. Sellers act only on orders containing their products;
  buyers may only `cancel` (from `waiting_for_payment`, `paid`, `processing`) or
  `return` (from `delivered`). Illegal moves return `400`.
- **Restock.** Moving to `cancelled` or `returned` returns the reserved stock.
- **Refund note.** Cancelling an order that was already `paid` or `processing`
  adds a refund note to the response.
- **Shipping needs a tracking ID.** The `processing → shipped` move must carry a
  `tracking_id`; it is frozen once set and ignored on any other transition.
- **Soft delete — `DELETE /orders/<id>`.** Housekeeping only: flips `is_active`
  off and stamps `deleted_at`. It does **not** change status or restock, and is
  allowed only once an order is no longer in flight (`delivered`, `returned`,
  `cancelled`). To cancel, use `PUT`.
- **Audit.** Every status change records the acting user in `updated_by`.

## Payments (Midtrans)

Payment uses Midtrans Snap. The buyer picks their method on the Midtrans page,
not in this API. An order is linked to many payment attempts, so a failed
attempt does not kill the order.

```mermaid
sequenceDiagram
    participant Buyer
    participant API
    participant Midtrans
    Buyer->>API: POST /payments { order_id }
    API->>Midtrans: create Snap transaction (our payment_reference as order_id)
    Midtrans-->>API: token + redirect_url
    API-->>Buyer: redirect_url
    Buyer->>Midtrans: pay on the Snap page
    Midtrans->>API: webhook (transaction_status)
    API->>API: verify signature, update payment + order
```

- **Start a payment — `POST /payments`.** Only the owning buyer, and only while
  the order is `waiting_for_payment`. Creates a `pending` payment attempt with a
  unique reference (`order-<id>-<attempt>`) and returns Midtrans's `snap_token`
  and `redirect_url`.
- **Webhook — `POST /payments/webhook/midtrans`.** Public (no login); trust is
  established by verifying Midtrans's SHA512 signature. Idempotent — duplicate
  notifications are ignored, and it always answers `200` so Midtrans stops
  retrying.
- **Safe against out-of-order webhooks.** A `paid` payment is never regressed by
  a late `deny`/`expire` notification — once paid, only a `refund` may change it;
  a `refunded` payment is fully terminal. This protects the correct final state
  when notifications arrive late, duplicated, or out of order.
- **Status reactions.** A `settlement` moves the order to `paid`. An `expire`
  cancels the order and restocks. A `refund` cancels a paid order and restocks.
- **Failure and retry.** A denied or cancelled *attempt* is marked `failed` but
  the *order stays* `waiting_for_payment`, so the buyer can call `POST /payments`
  again to create a fresh attempt. Only an expired payment link cancels the
  order.

See `docs/payment-testing-guide.md` for a full local setup and test walkthrough.

<details>
<summary>Full business rules (users, products, orders, cart, images)</summary>

**Users & Profiles**

- Passwords are hashed, never stored in plain text; usernames and emails are unique.
- You can delete your own account; admins can delete anyone.
- Each user has at most one profile (one-to-one). The first `PUT /profile`
  creates it, later calls update it; `GET /profile` is `404` until saved once.

**Addresses**

- A buyer concern (sellers/admins get `403`). A buyer keeps many addresses but
  exactly one default at a time.
- The first address becomes the default; setting a new default unsets the old
  one (backed by a partial unique index). You cannot delete the default while
  other addresses exist (`409`). Delete is a soft delete.

**Categories & Products**

- Category and product deletes are soft deletes; category names are unique.
- A product's category must exist. Each product is owned by its creator
  (`seller_id`) and gets a unique auto-generated `slug` fixed at creation.
- A product cannot be deleted while it is part of an active order.

**Orders**

- Only buyers place orders. Prices and totals are computed server-side; you can
  only order what is in stock, and placing an order deducts inventory.
- The shipping address is **snapshotted** onto the order at checkout (copy of
  the values, not a link), so editing the address book never rewrites past
  orders. Order creation/checkout take an optional `address_id`, else the
  default is used; an unresolvable address returns `422`.
- `PUT /orders/<id>/address` re-snapshots, but only while `waiting_for_payment`
  (otherwise `409`).

**Product Images**

- A product has many images, each with a `url` and a server-managed `order`
  (auto-appended; sending `order` on create/update returns `422`). Images sort
  by `order` ascending; the smallest is the primary image.
- Reorder via `PUT /products/<id>/images/reorder` with the exact set of active
  image IDs in the desired order. Delete is a soft delete. Only an admin or the
  owning seller may manage images.
- What is stored is a **key**, not a full URL — `products/42/<uuid>.jpg`. The
  API prefixes it with `IMAGE_BASE_URL` when it serializes a response, so
  moving between local static files, S3 and a CDN is one environment variable
  and a restart. Values that are already absolute are passed through unchanged.
- `POST /products/<id>/images/upload` takes `multipart/form-data` with a `file`
  field. The file type is detected from its magic bytes, not from the filename
  or `Content-Type` the client sends; only JPEG, PNG and WebP are accepted, up
  to `MAX_IMAGE_UPLOAD_BYTES` (5 MB by default). The object is uploaded to S3
  first and the row written second, so no row can ever point at an object that
  failed to upload; if the insert then fails, the object is deleted again so it
  does not linger as an orphan. Returns `422` for an invalid file and `503`
  when `AWS_S3_BUCKET` is not configured.
- Deleting an image is a soft delete, so the S3 object is deliberately **not**
  removed — the row can be restored. Reclaiming storage is a separate
  housekeeping job.

**Nested product previews**

- The four endpoints that nest products (`/categories/products`,
  `/categories/<id>`, `/sub-categories/products`, `/sub-categories/<id>`)
  return a **preview**, not the full catalogue: at most `products_limit`
  products per group, defaulting to **10** and capped at 100. Pass
  `?products_limit=0` to get the tree with no products at all.
- Only the outer list is paginated (`page` / `limit`); the nested products are
  never paginated, which is why they are capped instead. For a full, paginated
  product list use `GET /products/?sub_category_id=<id>&page=<n>`.
- The cap is applied in SQL with a window function, so the extra products are
  never loaded into memory, and each preview eager-loads its images in one
  query. Before this, a single request to `/categories/products` issued **2,218
  queries** and serialised **2,200 products** — enough to exhaust a small
  container's memory.

**Cart**

- One active cart per buyer, created lazily on first add. A cart item stores
  only `product_id` + `quantity`; prices, subtotals, and availability are
  computed live from the current product on every read.
- The cart is grouped by seller with per-group and grand totals.
- **Checkout** reuses order-creation logic, then removes only the ordered items.
  An optional body narrows the scope: `seller_id` (one group) or `cart_item_ids`
  (chosen lines) — mutually exclusive — plus an optional `address_id`. Each
  checkout produces a single order.

</details>

## CORS (browser access)

Browsers block a page on one origin from reading responses from another unless
the API opts in, so a frontend on `https://app.example.com` calling this API
needs CORS enabled here — no proxy route on the frontend is required.

CORS is applied to `/api/*` only and the allowed origins come from one
environment variable, comma-separated:

```bash
CORS_ORIGINS=https://app.example.com,https://www.example.com
```

| Environment | Default when `CORS_ORIGINS` is unset |
| --- | --- |
| development | `http://localhost:3000`, `http://localhost:5173`, `http://127.0.0.1:5173` |
| production | **none — every cross-origin browser request is blocked** |

Production is closed by default on purpose, so a forgotten variable fails
visibly instead of silently exposing the API to every website. On Render, add
`CORS_ORIGINS` under Environment with your deployed frontend's exact origin
(scheme + host, no path, no trailing slash) and let the service restart.

- Allowed request headers are `Authorization` and `Content-Type`; allowed
  methods are `GET POST PUT PATCH DELETE OPTIONS`. Preflight responses are
  cached for 10 minutes.
- Authentication is a bearer token in the `Authorization` header, not a cookie,
  so credentialed CORS is off and a wildcard origin is never returned.
- Error responses (401, 413, 422, …) carry the CORS headers too, so the
  frontend can read the error body instead of seeing an opaque network failure.
- This is enforced by the browser only. It does not protect the API from
  `curl` or other servers — authentication does that.

## Architecture

```mermaid
flowchart LR
    Req[Request] --> Route[Route<br/>flask-smorest]
    Route --> Schema[Schema<br/>marshmallow]
    Schema --> Service[Service<br/>business logic]
    Service --> Repo[Repository<br/>data access]
    Repo --> Model[Model<br/>SQLAlchemy]
    Model --> DB[(PostgreSQL)]
```

Each domain (users, auth, categories, products, orders, cart) is split across
these layers. Shared helpers live in `app/utils/` and cross-cutting constants in
`app/validation.py`.

<details>
<summary>Project structure</summary>

```
app/
├── __init__.py        # application factory
├── extensions.py      # db, jwt, migrate, api
├── auth.py            # hashing, roles_required
├── errors.py          # centralized error handlers
├── validation.py      # shared status constants / transitions
├── models/            # SQLAlchemy models
├── schemas/           # marshmallow validation + serialization
├── repositories/      # data access
├── services/          # business logic
├── routes/            # flask-smorest blueprints
└── utils/             # http, auth_context, timezone, slug, text
config/                # base / development / production
migrations/            # Flask-Migrate (Alembic)
seeders/               # database seeding
tests/
├── unit/              # isolated, repositories mocked
└── integration/       # full HTTP-through-stack (in-memory SQLite)
locust/                # load test (customer journey)
docker/entrypoint.sh   # waits for DB, migrates, starts server
Dockerfile · docker-compose.yml · docker-compose.prod.yml
run.py · pytest.ini · requirements.txt
```

</details>

## Database Schema

`users`, `user_profiles`, `user_addresses`, `categories`, `products`,
`product_images`, `orders` (with a `shipping_*` snapshot, `tracking_id`, and
`deleted_at`), `order_items`, `carts`, `cart_items`, `payments` (one order to
many attempts, referencing `orders`).

![Schema Diagram](./images/diagram-6.png)

## Running the Project Locally

Pick one of the two paths below. Docker is the quickest start if you already
have Docker installed; the manual path gives you a local Python + PostgreSQL
setup.

**Prerequisites**

- Without Docker: Python 3.11+ and PostgreSQL 14+.
- With Docker: Docker and Docker Compose.

### Option A — Without Docker

You provide the Python environment and a running PostgreSQL instance.

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Start PostgreSQL and create the database (macOS / Homebrew shown)
brew install postgresql@18 && brew services start postgresql@18
psql -U postgres -c "CREATE DATABASE revoshop_db;"

# 3. Configure the environment
cp .env.example .env
# then set in .env:
#   DATABASE_URL=postgresql://postgres:password@localhost:5432/revoshop_db
#   JWT_SECRET_KEY=<any-long-random-string>

# 4. Apply migrations
flask db upgrade

# 5. (Optional) seed sample users, products, and orders
python3 -m seeders.seeders

# 6. Run the API — FLASK_ENV defaults to development
python3 run.py
```

The API is served at `http://127.0.0.1:5000`. Set `FLASK_ENV=production` to run
with the production config.

### Option B — With Docker

A single `Dockerfile` builds the app image; two Compose files select the mode.
Both start `db` (PostgreSQL) and `web` (the API) on a private network. On
startup `web` waits for the database, runs `flask db upgrade` automatically,
then serves. **Seeding is never automatic** — run it yourself when you want
sample data.

```bash
# 1. Configure the environment
cp .env.docker.example .env
# Inside the Compose network the DB host is the service name `db`, not
# localhost. Compose builds DATABASE_URL from the POSTGRES_* values, so you
# usually only edit those and JWT_SECRET_KEY.

# 2a. Development — dev server with live reload, at http://localhost:5000
docker compose up --build

# 2b. Production — gunicorn, at http://localhost:8000 (DB port not published)
docker compose -f docker-compose.prod.yml up --build -d
```

Override the published port with `WEB_PORT` (e.g. `WEB_PORT=8080 docker compose
up`).

Other settings are passed through from `.env` to the container, and **an empty
value means "use the built-in default"** (not "set it to empty"):

| Variable | Purpose |
| --- | --- |
| `CORS_ORIGINS` | Browser origins allowed to call the API — see [CORS](#cors-browser-access) |
| `IMAGE_BASE_URL` | Root that stored image keys are joined to; empty serves `/static/images` |
| `AWS_S3_BUCKET`, `AWS_S3_REGION` | Target of `POST /products/<id>/images/upload`; empty bucket disables it (503) |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Only needed outside AWS; on EC2 attach an IAM role and leave both empty |
| `MAX_IMAGE_UPLOAD_BYTES`, `MAX_CONTENT_LENGTH` | Upload size limits (5 MB / 6 MB by default) |

The image build leaves `app/static/images/` out (`.dockerignore`), so locally
downloaded product photos are never baked into the image. In development the
project directory is bind-mounted, so those files are still served from disk; in
production, point `IMAGE_BASE_URL` at S3 or a CDN.

<details>
<summary>Common Docker tasks</summary>

```bash
docker compose exec web python -m seeders.seeders   # seed sample data
docker compose exec web sh                           # shell into the app
docker compose exec web flask db upgrade             # run migrations manually
docker compose logs -f web                           # follow app logs
docker compose down                                  # stop (keeps the pgdata volume)
docker compose down -v                               # reset DB (drops the volume)
```

</details>

## API Documentation

- **Postman:** [Revoshop Postman Collection](https://documenter.getpostman.com/view/17905565/2sBYAysoh1)
  — every endpoint with example requests and a reusable login token.
- **Swagger UI:** [live](https://revoshop-apis.onrender.com/docs/swagger-ui), or
  `http://127.0.0.1:5000/docs/swagger-ui` when running locally.

## Response Format

Every response has a boolean `status` and a `message`. Success responses add
`data`; list endpoints add `pagination`; login adds tokens.

```json
{ "status": true, "message": "success get product", "data": { "id": 1, "name": "Laptop", "price": 1299.99 } }
```

```json
{ "status": false, "message": "product not found" }
```

Errors never carry `data`; they are always just `status: false` + `message`.
Validation errors (`422`) are flattened to a single `message` string rather than
a field-by-field object. Beyond `status`, `message`, and `data`, a few endpoints
add extra top-level fields:

| Field | Type | Added by |
|-------|------|----------|
| `data` | object / array | every success response that returns a body |
| `pagination` | object | list endpoints (`page`, `limit`, `total_items`, `total_pages`) |
| `access_token` | string | `POST /auth/login`, `POST /auth/refresh` |
| `refresh_token` | string | `POST /auth/login` |

For payments, `snap_token` and `redirect_url` are returned **inside** `data`, not
at the top level.

| Status | When |
|--------|------|
| 400 | Bad request (e.g. illegal status transition) |
| 401 | Missing/invalid token or wrong credentials |
| 403 | Authenticated but not allowed (role or ownership) |
| 404 | Not found |
| 405 | Method not allowed |
| 409 | Conflict (e.g. duplicate name, deleting the default address) |
| 422 | Validation error or insufficient stock |
| 502 | Payment gateway (Midtrans) error on `POST /payments/` |
| 500 / 503 | Server error / database unavailable |

## API Endpoints

All routes are prefixed with `/api/v1`. The **Access** column tells you who may
call each route:

- **public** — no token required; call it anonymously.
- **authenticated** — any logged-in user; send `Authorization: Bearer <access_token>`.
- **buyer / seller / admin** (or a combination) — authenticated *and* the JWT
  must carry one of the listed roles. Some routes add an ownership check on top
  (e.g. a seller only manages their own products) — see the description.

In short: every route that is not marked **public** needs
`Authorization: Bearer <access_token>`.

<details>
<summary>Health & Auth</summary>

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/health` | Liveness + DB readiness (`200` / `503`) | public |
| POST | `/auth/login` | Log in, returns access + refresh tokens | public |
| POST | `/auth/refresh` | New access token (refresh token required) | authenticated |

</details>

<details>
<summary>Users, Profile & Addresses</summary>

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/users/` | Register a new user | public |
| GET | `/users/me` | Current user | authenticated |
| GET | `/users/<id>` | User by ID | authenticated |
| DELETE | `/users/<id>` | Delete a user (own account or admin) | authenticated |
| GET | `/profile` | Current user's profile (`404` if not created) | buyer, seller, admin |
| PUT | `/profile` | Create or update the profile (upsert) | buyer, seller, admin |
| GET | `/addresses` | List addresses (default first) | buyer, admin |
| POST | `/addresses` | Add an address (first becomes default) | buyer, admin |
| GET | `/addresses/<id>` | Get one address | buyer, admin |
| PUT | `/addresses/<id>` | Update an address | buyer, admin |
| DELETE | `/addresses/<id>` | Soft-delete (`409` if default and others exist) | buyer, admin |
| PUT | `/addresses/<id>/default` | Set as default | buyer, admin |

</details>

<details>
<summary>Categories, Products & Images</summary>

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/categories/` | List categories | public |
| GET | `/categories/products` | Categories with a product preview | public |
| POST | `/categories/` | Create a category | seller, admin |
| GET | `/categories/<id>` | Category → sub-categories → product preview | public |
| PUT | `/categories/<id>` | Update a category | seller, admin |
| DELETE | `/categories/<id>` | Soft-delete a category | seller, admin |
| GET | `/sub-categories/` | List sub-categories | public |
| GET | `/sub-categories/products` | Sub-categories with a product preview | public |
| POST | `/sub-categories/` | Create a sub-category | seller, admin |
| GET | `/sub-categories/<id>` | Sub-category with a product preview | public |
| PUT | `/sub-categories/<id>` | Update a sub-category | seller, admin |
| DELETE | `/sub-categories/<id>` | Soft-delete a sub-category | seller, admin |
| GET | `/products/` | List products (filter, sort, paginate) | public |
| POST | `/products/` | Create a product | seller, admin |
| GET | `/products/<id>` | Product by ID | public |
| GET | `/products/slug/<slug>` | Product by slug | public |
| PUT | `/products/<id>` | Update a product | seller, admin |
| DELETE | `/products/<id>` | Soft-delete a product | seller, admin |
| GET | `/products/<id>/images/` | List active images (ordered) | public |
| POST | `/products/<id>/images/` | Add an image by key/URL (auto-appended) | admin, owning seller |
| POST | `/products/<id>/images/upload` | Upload an image file (multipart) | admin, owning seller |
| PUT | `/products/<id>/images/<id>` | Update an image (`url` only) | admin, owning seller |
| PUT | `/products/<id>/images/reorder` | Reorder active images | admin, owning seller |
| DELETE | `/products/<id>/images/<id>` | Soft-delete an image | admin, owning seller |

</details>

<details>
<summary>Orders & Cart</summary>

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/orders/` | List orders (scoped by role) | any role |
| POST | `/orders/` | Create an order (optional `address_id`; checks/deducts stock) | buyer |
| GET | `/orders/<id>` | Get an order (owner, seller of a product in it, or admin) | any role |
| PUT | `/orders/<id>` | Change status: advance, cancel, or return (`shipped` needs `tracking_id`) | buyer, seller, admin |
| PUT | `/orders/<id>/address` | Re-snapshot the shipping address (owner; only while `waiting_for_payment`) | buyer |
| DELETE | `/orders/<id>` | Soft-delete (no status change / restock; only when not in flight) | buyer, seller, admin |
| GET | `/cart` | Current cart, grouped by seller with live totals | buyer |
| POST | `/cart/items` | Add a product (accumulates quantity) | buyer |
| PUT | `/cart/items/<id>` | Set quantity (`0` removes it) | buyer |
| DELETE | `/cart/items/<id>` | Remove one item | buyer |
| DELETE | `/cart` | Clear the cart | buyer |
| POST | `/cart/checkout` | Convert cart to an order; optional subset + `address_id` | buyer |

Checkout body: none = whole cart · `{ "seller_id": 10 }` = one seller ·
`{ "cart_item_ids": [5, 8] }` = chosen lines (the two selectors are mutually
exclusive).

</details>

<details>
<summary>Payments</summary>

| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/payments/` | Start a payment for an order; returns `snap_token` + `redirect_url` | buyer |
| GET | `/payments/<id>` | Get a payment record (owning buyer or admin) | buyer, admin |
| POST | `/payments/webhook/midtrans` | Midtrans status notification (signature-verified) | public |

</details>

### Query Parameters

List endpoints accept query parameters for filtering, sorting, and pagination.
All are optional; the defaults are shown below. Out-of-range or invalid values
return `422`.

<details>
<summary>Common pagination & sorting</summary>

Shared by `GET /products/`, `/categories/`, `/sub-categories/`, `/orders/`
(and the `/products` preview variants).

| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `page` | int | `1` | Page number, min `1` |
| `limit` | int | `10` | Items per page, `1`–`100` |
| `sort_by` | string | varies | Allowed values differ per resource (see below) |
| `order` | string | `asc` (`orders`: `desc`) | `asc` or `desc` |

</details>

<details>
<summary>GET /products/</summary>

| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `name` | string | — | Case-insensitive name filter |
| `sub_category_id` | int | — | Filter by sub-category |
| `seller_id` | int | — | Filter by seller |
| `min_price` | float | — | Minimum price |
| `max_price` | float | — | Maximum price |
| `sort_by` | string | `id` | `id`, `name`, `price`, `created_at` |
| `order` | string | `asc` | `asc`, `desc` |
| `page` / `limit` | int | `1` / `10` | Pagination |

</details>

<details>
<summary>GET /categories/ and /sub-categories/</summary>

| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `name` | string | — | Case-insensitive name filter |
| `category_id` | int | — | **Sub-categories only** — filter by parent category |
| `sort_by` | string | `id` | `id`, `name`, `created_at` |
| `order` | string | `asc` | `asc`, `desc` |
| `page` / `limit` | int | `1` / `10` | Pagination |
| `products_limit` | int | `10` | Max products per group in the `/products` preview variants and `/<id>` detail; `0`–`100`. `0` returns the tree with no products |

</details>

<details>
<summary>GET /orders/</summary>

| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `status` | string | — | One of `waiting_for_payment`, `paid`, `processing`, `shipped`, `delivered`, `returned`, `cancelled` |
| `include_deleted` | bool | `false` | Include soft-deleted orders |
| `sort_by` | string | `id` | `id`, `total_amount`, `ordered_at` |
| `order` | string | `desc` | `asc`, `desc` |
| `page` / `limit` | int | `1` / `10` | Pagination |

</details>

## Testing

Fast unit tests (repositories mocked) and integration tests (full HTTP stack on
in-memory SQLite).

```bash
python3 -m pytest                       # everything
python3 -m pytest tests/unit/           # unit only
python3 -m pytest tests/integration/    # integration only
python3 -m pytest -k "refund or insufficient"

# Coverage
python3 -m pytest --cov=app --cov-report=term-missing
python3 -m pytest --cov=app --cov-report=html   # open htmlcov/index.html
```

![Pytest Result](./images/tests/v3/pytest-20260912.png)

## Performance Testing (Locust)

`locust/locustfile.py` simulates a customer journey (browse → view → add to
cart → cart checkout or direct checkout → create payment → check payment/order
status) with weighted tasks, plus a seller fulfillment journey. Each user logs
in once, then repeats.

Payment creation calls Midtrans, so it is **off by default** to keep the load
test independent of the external gateway. Enable it with
`LOCUST_TEST_PAYMENTS=true` when you specifically want to stress the payment
path (be mindful of Midtrans sandbox rate limits).

```bash
python3 -m seeders.seeders && python3 run.py

# Web UI at http://127.0.0.1:8089
locust -f locust/locustfile.py --host http://127.0.0.1:5000

# Headless: 10 users, 2/s, 1 minute
locust -f locust/locustfile.py --host http://127.0.0.1:5000 \
    --users 10 --spawn-rate 2 --run-time 1m --headless
```

Logs in as the seeded buyer (`jane@example.com`); override with `LOCUST_EMAIL` /
`LOCUST_PASSWORD`.

![Locust Result](./images/tests/v3/locust-20260912.png)

## Code Quality & Security

```bash
bandit -r app                   # security scan
pylint --rcfile=.pylintrc app   # lint
pip-audit                       # dependency CVE audit
```

| Tool | Checks | Latest |
|------|--------|--------|
| Bandit | Security issues in our code | 0 issues |
| pip-audit | Known CVEs in dependencies | None |
| Pylint | Code quality / style | 9.66 / 10 |

## Logging

Logging is configured on startup (`app/logging_config.py`): console + a daily
rotating file at `logs/app.log` (30 days kept, git-ignored). Level follows the
environment (`DEBUG` dev, `INFO` prod). Override with `LOG_LEVEL`, `LOG_TO_FILE`,
`LOG_DIR`, `LOG_FILE`, `LOG_BACKUP_COUNT`. Startup, login, and order events are
logged.

## Future Improvements

- **Concurrency-safe stock deduction.** Order creation currently does a
  read-modify-write on stock without a row lock, so simultaneous checkouts can
  oversell. The fix is to make the deduction atomic — lock the product rows
  (`SELECT ... FOR UPDATE` / `with_for_update()`) or use a conditional
  `UPDATE ... WHERE stock >= :qty` and treat a zero-row result as insufficient
  stock.

## Troubleshooting

- **Database connection error:** confirm Postgres is running
  (`brew services list`), check `DATABASE_URL` in `.env`, and that the database
  exists (`psql -l`).
- **Module not found:** `pip3 install -r requirements.txt`.
- **Browser says "blocked by CORS policy" but the API works in Postman:** the
  frontend's origin is not in `CORS_ORIGINS`. Match it exactly, including the
  scheme and port (`http://localhost:5173` is not `http://localhost:3000`).
