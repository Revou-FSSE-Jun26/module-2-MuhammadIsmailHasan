# Ticket map

Jira discards the `Issue Id` column on import, so these internal backlog
numbers exist only here. Use this to look up any ticket referenced as `303`
or similar in chat or in the README.

| Jira | Id | Type | Pts | Tier | Epic | Summary |
|---|---|---|---|---|---|---|
| `REV-1` | 1 | Epic |  | mvp |  | MVP - Auth Foundation with JWT and Roles |
| `REV-2` | 2 | Epic |  | mvp |  | MVP - Order Module |
| `REV-3` | 3 | Epic |  | mvp |  | MVP - Product and Category Compliance |
| `REV-4` | 4 | Epic |  | mvp |  | MVP - Migrations Seeders Tests and Docs |
| `REV-5` | 5 | Epic |  | improvement |  | IMPROVEMENT - Marshmallow DTO Layer |
| `REV-6` | 6 | Epic |  | improvement |  | IMPROVEMENT - Auth Enhancements |
| `REV-7` | 7 | Epic |  | improvement |  | IMPROVEMENT - User Profile and Addresses |
| `REV-8` | 8 | Epic |  | improvement |  | IMPROVEMENT - Product Catalog Enhancements |
| `REV-9` | 9 | Epic |  | improvement |  | IMPROVEMENT - Order Status Lifecycle |
| `REV-10` | 10 | Epic |  | improvement |  | IMPROVEMENT - Seller Ownership Rules |
| `REV-11` | 11 | Epic |  | improvement |  | IMPROVEMENT - Data Integrity and Robustness |
| `REV-12` | 101 | Story | 2 | mvp | REV-1 | Expose POST /users as the registration route |
| `REV-13` | 102 | Story | 3 | mvp | REV-1 | Add POST /auth/login verifying credentials |
| `REV-14` | 103 | Story | 2 | mvp | REV-1 | Add JWT dependencies and secret configuration |
| `REV-15` | 104 | Story | 2 | mvp | REV-1 | Issue a JWT access token from POST /auth/login |
| `REV-16` | 105 | Story | 3 | mvp | REV-1 | Normalize user role to buyer seller admin with a data migration |
| `REV-17` | 106 | Story | 3 | mvp | REV-1 | Add auth decorators for token and role checks |
| `REV-18` | 107 | Story | 1 | mvp | REV-1 | Add GET /auth/me returning the authenticated user |
| `REV-19` | 108 | Story | 2 | mvp | REV-1 | Add 401 403 and 409 error handlers to the standard envelope |
| `REV-20` | 201 | Story | 5 | mvp | REV-2 | Rework order_items into an OrderItem model with quantity and unit_price |
| `REV-21` | 202 | Story | 2 | mvp | REV-2 | Create the orders blueprint and register it |
| `REV-22` | 203 | Task | 1 | mvp | REV-2 | Decide the auth compatibility policy for graded endpoints |
| `REV-23` | 204 | Story | 5 | mvp | REV-2 | Add POST /orders to place an order and decrement stock |
| `REV-24` | 205 | Story | 2 | mvp | REV-2 | Add GET /orders listing the authenticated user's orders |
| `REV-25` | 206 | Story | 3 | mvp | REV-2 | Add GET /orders/<id> returning order items with product details |
| `REV-26` | 207 | Story | 3 | mvp | REV-2 | Add DELETE /orders/<id> with a documented stock policy |
| `REV-27` | 301 | Story | 3 | mvp | REV-3 | Block product deletion while active orders reference it |
| `REV-28` | 302 | Task | 1 | mvp | REV-3 | Define and document the active order status set |
| `REV-29` | 303 | Story | 1 | mvp | REV-3 | Return products in GET /categories/<id> by default |
| `REV-30` | 401 | Task | 2 | mvp | REV-4 | Write the Alembic migration for the order_items rework |
| `REV-31` | 402 | Task | 2 | mvp | REV-4 | Update seeders for roles and order items |
| `REV-32` | 403 | Task | 5 | mvp | REV-4 | Extend the test suite for auth and the order module |
| `REV-33` | 404 | Task | 3 | mvp | REV-4 | Update Swagger and README for the MVP endpoints |
| `REV-34` | 501 | Story | 3 | improvement | REV-5 | Create the schemas package and Marshmallow base configuration |
| `REV-35` | 502 | Story | 3 | improvement | REV-5 | Migrate product validation to Marshmallow schemas |
| `REV-36` | 503 | Story | 2 | improvement | REV-5 | Migrate category validation to Marshmallow schemas |
| `REV-37` | 504 | Story | 3 | improvement | REV-5 | Add user and auth schemas |
| `REV-38` | 505 | Story | 3 | improvement | REV-5 | Add order schemas including a status-only update |
| `REV-39` | 506 | Story | 3 | improvement | REV-5 | Validate query parameters via schema and fix the sort fallback |
| `REV-40` | 507 | Bug | 2 | improvement | REV-5 | Normalize Decimal serialization across product and order responses |
| `REV-41` | 508 | Story | 2 | improvement | REV-5 | Add a central 422 handler for Marshmallow validation errors |
| `REV-42` | 601 | Story | 2 | improvement | REV-6 | Add GET /users/check-email for registration availability |
| `REV-43` | 602 | Story | 5 | improvement | REV-6 | Add refresh token and logout denylist |
| `REV-44` | 603 | Story | 2 | improvement | REV-6 | Add rate limiting to public endpoints |
| `REV-45` | 701 | Story | 3 | improvement | REV-7 | Add the user_profiles table and model |
| `REV-46` | 702 | Story | 3 | improvement | REV-7 | Add GET and PUT /users/me/profile |
| `REV-47` | 703 | Story | 3 | improvement | REV-7 | Add the user_addresses table and model |
| `REV-48` | 704 | Story | 5 | improvement | REV-7 | Enforce at most one default address per user |
| `REV-49` | 705 | Story | 2 | improvement | REV-7 | Include the default address in the user output DTO |
| `REV-50` | 706 | Story | 5 | improvement | REV-7 | Add CRUD endpoints for user addresses |
| `REV-51` | 707 | Story | 3 | improvement | REV-7 | Add set-default address and guard default deletion |
| `REV-52` | 801 | Story | 3 | improvement | REV-8 | Add user_id ownership column to products |
| `REV-53` | 802 | Story | 3 | improvement | REV-8 | Add slug to products with generation and backfill |
| `REV-54` | 803 | Story | 2 | improvement | REV-8 | Add GET /products/slug/<slug> |
| `REV-55` | 804 | Story | 3 | improvement | REV-8 | Add the product_images table |
| `REV-56` | 805 | Story | 5 | improvement | REV-8 | Add product image management endpoints |
| `REV-57` | 806 | Story | 3 | improvement | REV-8 | Refactor product-by-category into a nested multi-parameter route |
| `REV-58` | 807 | Story | 3 | improvement | REV-8 | Extend product filtering and sorting |
| `REV-59` | 901 | Story | 5 | improvement | REV-9 | Define and enforce the order status transition state machine |
| `REV-60` | 902 | Story | 3 | improvement | REV-9 | Restrict order updates to status only |
| `REV-61` | 903 | Story | 5 | improvement | REV-9 | Add order cancellation with idempotent stock restore |
| `REV-62` | 904 | Story | 3 | improvement | REV-9 | Add a payment-success endpoint advancing the order to processing |
| `REV-63` | 905 | Story | 3 | improvement | REV-9 | Add seller fulfilment transitions for shipped and delivered |
| `REV-64` | 906 | Story | 3 | improvement | REV-9 | Add filtering and sorting to the order list |
| `REV-65` | 907 | Story | 3 | improvement | REV-9 | Snapshot the shipping address onto the order |
| `REV-66` | 1001 | Story | 3 | improvement | REV-10 | Restrict product mutation and deletion to the owning seller or admin |
| `REV-67` | 1002 | Story | 3 | improvement | REV-10 | Extend order permissions to the related seller |
| `REV-68` | 1003 | Task | 2 | improvement | REV-10 | Decide the multi-seller order policy |
| `REV-69` | 1101 | Story | 5 | improvement | REV-11 | Make stock decrement concurrency-safe |
| `REV-70` | 1102 | Story | 2 | improvement | REV-11 | Add a non-negative stock CHECK constraint to products |
| `REV-71` | 1103 | Task | 3 | improvement | REV-11 | Review the migration chain and test every downgrade |
