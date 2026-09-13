"""Generate the Revoshop Postman collection, organized by user role.

Each role folder contains every endpoint that role is authorized to call
(based on the route decorators and service-level ownership rules). Shared
no-auth endpoints live in a Public folder. Run:

    python scripts/build_postman.py

Writes docs/revoshop.postman_collection.json.
"""
import json
import os

BASE = "{{baseUrl}}"


def url(path_segments):
    return {
        "raw": BASE + "/" + "/".join(path_segments),
        "host": [BASE],
        "path": path_segments,
    }


def example(name, code, status_text, body, method="GET", req_url=None, raw_body=None):
    orig = {"method": method, "header": [], "url": req_url or {}}
    if raw_body is not None:
        orig["header"] = [{"key": "Content-Type", "value": "application/json"}]
        orig["body"] = {"mode": "raw", "raw": raw_body}
    return {
        "name": name,
        "originalRequest": orig,
        "status": status_text,
        "code": code,
        "_postman_previewlanguage": "json",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": body,
    }


def request(name, method, path_segments, raw_body=None, examples=None, test_script=None):
    req = {"method": method, "header": [], "url": url(path_segments)}
    if raw_body is not None:
        req["header"] = [{"key": "Content-Type", "value": "application/json"}]
        req["body"] = {"mode": "raw", "raw": raw_body}
    item = {"name": name, "request": req, "response": examples or []}
    if test_script:
        item["event"] = [{
            "listen": "test",
            "script": {"type": "text/javascript", "exec": test_script},
        }]
    return item


def login_request(role, token_var, email):
    body = json.dumps({"email": email, "password": "password123"}, indent=2)
    req_url = url(["auth", "login"])
    ok_body = json.dumps({
        "status": True, "message": "login successful",
        "data": {"id": 1, "username": role, "email": email, "role": role},
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    }, indent=2)
    fail_body = json.dumps({"status": False, "message": "invalid email or password"}, indent=2)
    item = request(
        f"Login ({role.capitalize()})", "POST", ["auth", "login"], raw_body=body,
        examples=[
            example("200 - login success", 200, "OK", ok_body, "POST", req_url, body),
            example("401 - wrong credentials", 401, "UNAUTHORIZED", fail_body, "POST", req_url,
                    json.dumps({"email": email, "password": "wrong"}, indent=2)),
        ],
        test_script=[
            "const body = pm.response.json();",
            f"if (body && body.access_token) {{ pm.collectionVariables.set('{token_var}', body.access_token); }}",
            "pm.test('login ok', function () { pm.response.to.have.status(200); });",
        ],
    )
    # login itself must not send the folder bearer token
    item["request"]["auth"] = {"type": "noauth"}
    return item


def envelope(message, data=None, extra=None):
    payload = {"status": True, "message": message}
    if data is not None:
        payload["data"] = data
    if extra:
        payload.update(extra)
    return json.dumps(payload, indent=2)


def error(message):
    return json.dumps({"status": False, "message": message}, indent=2)


def save_id_script(var):
    return [
        "if (pm.response.code < 300) {",
        "  const body = pm.response.json();",
        f"  if (body.data && body.data.id) pm.collectionVariables.set('{var}', body.data.id);",
        "}",
    ]


# ── shared endpoint builders (return a request item) ─────────────────────────

def ep_refresh():
    return request(
        "Refresh Token", "POST", ["auth", "refresh"],
        examples=[example("200 - new access token", 200, "OK",
                          envelope("create new access token successful",
                                   extra={"access_token": "eyJ..."}), "POST", url(["auth", "refresh"]))],
    )


def ep_me():
    return request(
        "Get Current User", "GET", ["users", "me"],
        examples=[
            example("200 - current user", 200, "OK",
                    envelope("get user data successful",
                             {"id": 1, "username": "user", "email": "user@example.com", "role": "buyer"}),
                    "GET", url(["users", "me"])),
            example("401 - no token", 401, "UNAUTHORIZED",
                    json.dumps({"msg": "Missing Authorization Header"}, indent=2),
                    "GET", url(["users", "me"])),
        ],
    )


def ep_get_user():
    return request(
        "Get User By Id", "GET", ["users", "2"],
        examples=[example("200 - public user", 200, "OK",
                          envelope("success get user data", {"username": "jane_smith", "email": "jane@example.com"}),
                          "GET", url(["users", "2"]))],
    )


def ep_delete_user(target="3"):
    return request(
        "Delete User", "DELETE", ["users", target],
        examples=[
            example("200 - deleted", 200, "OK", envelope("success delete user"), "DELETE", url(["users", target])),
            example("403 - not allowed", 403, "FORBIDDEN", error("you can only delete your own account"),
                    "DELETE", url(["users", "1"])),
        ],
    )


def ep_get_profile():
    return request(
        "Get Profile", "GET", ["profile"],
        examples=[
            example("200 - profile", 200, "OK",
                    envelope("success get profile",
                             {"full_name": "Jane Smith", "phone": "+628123456789", "avatar_url": None}),
                    "GET", url(["profile"])),
            example("404 - no profile yet", 404, "NOT FOUND", error("profile not found"), "GET", url(["profile"])),
        ],
    )


def ep_put_profile():
    body = json.dumps({"full_name": "Jane Smith", "phone": "+628123456789", "avatar_url": None}, indent=2)
    return request(
        "Upsert Profile", "PUT", ["profile"], raw_body=body,
        examples=[example("200 - saved", 200, "OK",
                          envelope("profile saved",
                                   {"full_name": "Jane Smith", "phone": "+628123456789", "avatar_url": None}),
                          "PUT", url(["profile"]), body)],
    )


def address_endpoints():
    create_body = json.dumps({
        "label": "Home", "recipient_name": "Jane Smith", "phone": "+628123456789",
        "address_line": "Jl. Merdeka No. 1", "city": "Jakarta", "postal_code": "10110", "is_default": True,
    }, indent=2)
    update_body = json.dumps({"city": "Bandung", "postal_code": "40111"}, indent=2)
    return [
        request("List Addresses", "GET", ["addresses"],
                examples=[example("200 - addresses", 200, "OK",
                                  envelope("success get addresses",
                                           [{"id": 1, "label": "Home", "recipient_name": "Jane Smith",
                                             "city": "Jakarta", "is_default": True}]),
                                  "GET", url(["addresses"]))]),
        request("Create Address", "POST", ["addresses"], raw_body=create_body,
                test_script=save_id_script("addressId"),
                examples=[
                    example("201 - created", 201, "CREATED",
                            envelope("address created",
                                     {"id": 2, "label": "Home", "city": "Jakarta", "is_default": True}),
                            "POST", url(["addresses"]), create_body),
                    example("422 - validation error", 422, "UNPROCESSABLE ENTITY",
                            json.dumps({"status": False, "message": "validation error",
                                        "errors": {"recipient_name": ["recipient_name is required"]}}, indent=2),
                            "POST", url(["addresses"]), json.dumps({"city": "Jakarta"}, indent=2)),
                ]),
        request("Get Address", "GET", ["addresses", "{{addressId}}"],
                examples=[example("200 - address", 200, "OK",
                                  envelope("success get address",
                                           {"id": 2, "label": "Home", "city": "Jakarta"}),
                                  "GET", url(["addresses", "2"]))]),
        request("Update Address", "PUT", ["addresses", "{{addressId}}"], raw_body=update_body,
                examples=[example("200 - updated", 200, "OK",
                                  envelope("address updated", {"id": 2, "city": "Bandung"}),
                                  "PUT", url(["addresses", "2"]), update_body)]),
        request("Delete Address", "DELETE", ["addresses", "{{addressId}}"],
                examples=[
                    example("200 - deleted", 200, "OK", envelope("address deleted"), "DELETE", url(["addresses", "2"])),
                    example("409 - default with others", 409, "CONFLICT",
                            error("cannot delete the default address while other addresses exist"),
                            "DELETE", url(["addresses", "1"])),
                ]),
        request("Set Default Address", "PUT", ["addresses", "{{addressId}}", "default"],
                examples=[example("200 - default set", 200, "OK",
                                  envelope("default address updated", {"id": 2, "is_default": True}),
                                  "PUT", url(["addresses", "2", "default"]))]),
    ]


def category_write_endpoints():
    create_body = json.dumps({"name": "Home & Living"}, indent=2)
    update_body = json.dumps({"name": "Home & Kitchen"}, indent=2)
    return [
        request("Create Category", "POST", ["categories", ""], raw_body=create_body,
                test_script=save_id_script("categoryId"),
                examples=[
                    example("201 - created", 201, "CREATED",
                            envelope("category created", {"id": 6, "name": "Home & Living"}),
                            "POST", url(["categories", ""]), create_body),
                    example("409 - name exists", 409, "CONFLICT", error("category name already exists"),
                            "POST", url(["categories", ""]), json.dumps({"name": "Electronics"}, indent=2)),
                ]),
        request("Update Category", "PUT", ["categories", "{{categoryId}}"], raw_body=update_body,
                examples=[example("200 - updated", 200, "OK",
                                  envelope("category updated", {"id": 6, "name": "Home & Kitchen"}),
                                  "PUT", url(["categories", "6"]), update_body)]),
        request("Delete Category", "DELETE", ["categories", "{{categoryId}}"],
                examples=[example("200 - deleted", 200, "OK", envelope("category deleted"),
                                  "DELETE", url(["categories", "6"]))]),
    ]


def product_write_endpoints():
    create_body = json.dumps({
        "name": "Speaker Bluetooth JBL", "description": "Speaker portable dengan bass mantap",
        "price": 750000, "stock": 20, "category_id": 1,
    }, indent=2)
    update_body = json.dumps({"price": 699000, "stock": 25}, indent=2)
    return [
        request("Create Product", "POST", ["products", ""], raw_body=create_body,
                test_script=save_id_script("productId"),
                examples=[
                    example("201 - created", 201, "CREATED",
                            envelope("product created",
                                     {"id": 11, "name": "Speaker Bluetooth JBL",
                                      "slug": "speaker-bluetooth-jbl", "price": 750000.0, "stock": 20,
                                      "category_id": 1, "seller_id": 4}),
                            "POST", url(["products", ""]), create_body),
                    example("422 - validation error", 422, "UNPROCESSABLE ENTITY",
                            json.dumps({"status": False, "message": "validation error",
                                        "errors": {"name": ["name is required"]}}, indent=2),
                            "POST", url(["products", ""]), json.dumps({"price": 5}, indent=2)),
                ]),
        request("Update Product", "PUT", ["products", "{{productId}}"], raw_body=update_body,
                examples=[example("200 - updated", 200, "OK",
                                  envelope("product updated", {"id": 11, "price": 699000.0, "stock": 25}),
                                  "PUT", url(["products", "11"]), update_body)]),
        request("Delete Product", "DELETE", ["products", "{{productId}}"],
                examples=[
                    example("200 - deleted", 200, "OK", envelope("product deleted"),
                            "DELETE", url(["products", "11"])),
                    example("400 - has active orders", 400, "BAD REQUEST",
                            error("cannot delete a product that is part of an active order"),
                            "DELETE", url(["products", "1"])),
                ]),
    ]


def product_image_endpoints():
    create_body = json.dumps({"url": "https://cdn.example.com/products/jbl-1.jpg"}, indent=2)
    update_body = json.dumps({"url": "https://cdn.example.com/products/jbl-1-new.jpg"}, indent=2)
    reorder_body = json.dumps({"image_ids": [2, 1, 3]}, indent=2)
    return [
        request("Add Product Image", "POST", ["products", "{{productId}}", "images", ""], raw_body=create_body,
                test_script=save_id_script("imageId"),
                examples=[
                    example("201 - image added", 201, "CREATED",
                            envelope("product image added",
                                     {"id": 5, "product_id": 11, "url": "https://cdn.example.com/products/jbl-1.jpg", "order": 0}),
                            "POST", url(["products", "11", "images", ""]), create_body),
                    example("403 - not owner (seller)", 403, "FORBIDDEN",
                            error("you don't have permission to manage this product's images"),
                            "POST", url(["products", "1", "images", ""]), create_body),
                ]),
        request("Update Product Image", "PUT", ["products", "{{productId}}", "images", "{{imageId}}"],
                raw_body=update_body,
                examples=[example("200 - updated", 200, "OK",
                                  envelope("product image updated",
                                           {"id": 5, "url": "https://cdn.example.com/products/jbl-1-new.jpg"}),
                                  "PUT", url(["products", "11", "images", "5"]), update_body)]),
        request("Reorder Product Images", "PUT", ["products", "{{productId}}", "images", "reorder"],
                raw_body=reorder_body,
                examples=[
                    example("200 - reordered", 200, "OK",
                            envelope("product images reordered",
                                     [{"id": 2, "order": 0}, {"id": 1, "order": 1}, {"id": 3, "order": 2}]),
                            "PUT", url(["products", "11", "images", "reorder"]), reorder_body),
                    example("422 - id set mismatch", 422, "UNPROCESSABLE ENTITY",
                            error("image_ids must be exactly the product's active image ids"),
                            "PUT", url(["products", "11", "images", "reorder"]),
                            json.dumps({"image_ids": [99]}, indent=2)),
                ]),
        request("Delete Product Image", "DELETE", ["products", "{{productId}}", "images", "{{imageId}}"],
                examples=[example("200 - deleted", 200, "OK", envelope("product image deleted"),
                                  "DELETE", url(["products", "11", "images", "5"]))]),
    ]


def order_list_get_endpoints():
    return [
        request("List Orders", "GET", ["orders", ""],
                examples=[example("200 - orders", 200, "OK",
                                  envelope("get all orders success",
                                           [{"id": 13, "user_id": 2, "total_amount": 8499000.0, "status": "paid"}],
                                           extra={"pagination": {"page": 1, "limit": 10, "total_items": 1, "total_pages": 1}}),
                                  "GET", url(["orders", ""]))]),
        request("Get Order", "GET", ["orders", "{{orderId}}"],
                examples=[
                    example("200 - order detail", 200, "OK",
                            envelope("success get order",
                                     {"id": 13, "user_id": 2, "total_amount": 8499000.0, "status": "paid",
                                      "items": [{"id": 21, "product_id": 1, "product_name": "Laptop ASUS Vivobook 14",
                                                 "quantity": 1, "sub_total": 8499000.0}]}),
                            "GET", url(["orders", "13"])),
                    example("403 - no permission", 403, "FORBIDDEN",
                            error("you don't have permission to view this order"),
                            "GET", url(["orders", "1"])),
                ]),
    ]


def order_status_endpoint(sample_status, fail_from, fail_to):
    body = json.dumps({"status": sample_status}, indent=2)
    return request(
        "Update Order Status", "PUT", ["orders", "{{orderId}}"], raw_body=body,
        examples=[
            example("200 - status updated", 200, "OK",
                    envelope("success update order status", {"id": 13, "status": sample_status}),
                    "PUT", url(["orders", "13"]), body),
            example("400 - illegal transition", 400, "BAD REQUEST",
                    error(f"cannot change status from '{fail_from}' to '{fail_to}'"),
                    "PUT", url(["orders", "13"]), json.dumps({"status": fail_to}, indent=2)),
        ],
    )


def order_delete_endpoint():
    return request(
        "Delete Order", "DELETE", ["orders", "{{orderId}}"],
        examples=[
            example("200 - deleted", 200, "OK",
                    envelope("order deleted successfully", {"id": 13, "status": "cancelled"}),
                    "DELETE", url(["orders", "13"])),
            example("400 - not deletable", 400, "BAD REQUEST",
                    error("cannot delete order with status 'paid'"),
                    "DELETE", url(["orders", "13"])),
        ],
    )


def folder(name, description, token_var, items):
    return {
        "name": name,
        "description": description,
        "auth": {"type": "bearer", "bearer": [{"key": "token", "value": "{{" + token_var + "}}", "type": "string"}]},
        "item": items,
    }


def build():
    with open(os.path.join(os.path.dirname(__file__), "..", "docs",
                           "revoshop.postman_collection.json")) as f:
        collection = json.load(f)

    public_folder = collection["item"][0]  # keep the existing Public folder

    # ── Admin ────────────────────────────────────────────────────────────────
    admin_items = [
        login_request("admin", "adminToken", "john@example.com"),
        ep_refresh(), ep_me(), ep_get_user(), ep_delete_user(),
        ep_get_profile(), ep_put_profile(),
        *address_endpoints(),
        *category_write_endpoints(),
        *product_write_endpoints(),
        *product_image_endpoints(),
        *order_list_get_endpoints(),
        order_status_endpoint("processing", "paid", "delivered"),
        order_delete_endpoint(),
        request("Get Payment", "GET", ["payments", "{{paymentId}}"],
                examples=[
                    example("200 - payment", 200, "OK",
                            envelope("success get payment",
                                     {"id": 5, "order_id": 13, "payment_reference": "order-13-1",
                                      "amount": 8499000.0, "status": "paid", "payment_method": "credit_card"}),
                            "GET", url(["payments", "5"])),
                    example("404 - not found", 404, "NOT FOUND", error("payment not found"),
                            "GET", url(["payments", "99999"])),
                ]),
    ]

    # ── Buyer ────────────────────────────────────────────────────────────────
    add_cart_body = json.dumps({"product_id": 1, "quantity": 1}, indent=2)
    update_cart_body = json.dumps({"quantity": 2}, indent=2)
    create_order_body = json.dumps({"items": [{"product_id": 1, "quantity": 1}]}, indent=2)
    change_addr_body = json.dumps({"address_id": 2}, indent=2)
    create_payment_body = json.dumps({"order_id": "{{orderId}}"}, indent=2).replace('"{{orderId}}"', "{{orderId}}")

    buyer_items = [
        login_request("buyer", "buyerToken", "jane@example.com"),
        ep_refresh(), ep_me(), ep_get_user(), ep_delete_user(),
        ep_get_profile(), ep_put_profile(),
        *address_endpoints(),
        request("View Cart", "GET", ["cart"],
                examples=[example("200 - cart", 200, "OK",
                                  envelope("get cart success",
                                           {"cart_id": 1, "groups": [], "total_items": 0, "total_quantity": 0}),
                                  "GET", url(["cart"]))]),
        request("Add To Cart", "POST", ["cart", "items"], raw_body=add_cart_body,
                examples=[
                    example("201 - added", 201, "CREATED",
                            envelope("item added to cart",
                                     {"cart_id": 1, "groups": [{"seller_id": 4, "items": [{"id": 1, "product_id": 1, "quantity": 1}]}]}),
                            "POST", url(["cart", "items"]), add_cart_body),
                    example("422 - insufficient stock", 422, "UNPROCESSABLE ENTITY",
                            error("insufficient stock for product Laptop ASUS Vivobook 14 (available: 15, requested: 99999)"),
                            "POST", url(["cart", "items"]), json.dumps({"product_id": 1, "quantity": 99999}, indent=2)),
                ]),
        request("Update Cart Item", "PUT", ["cart", "items", "1"], raw_body=update_cart_body,
                examples=[example("200 - updated", 200, "OK",
                                  envelope("cart item updated", {"cart_id": 1}),
                                  "PUT", url(["cart", "items", "1"]), update_cart_body)]),
        request("Remove Cart Item", "DELETE", ["cart", "items", "1"],
                examples=[example("200 - removed", 200, "OK", envelope("cart item removed", {"cart_id": 1}),
                                  "DELETE", url(["cart", "items", "1"]))]),
        request("Clear Cart", "DELETE", ["cart"],
                examples=[example("200 - cleared", 200, "OK", envelope("cart cleared", {"cart_id": 1}),
                                  "DELETE", url(["cart"]))]),
        request("Checkout Cart", "POST", ["cart", "checkout"], raw_body="{}",
                test_script=save_id_script("orderId"),
                examples=[
                    example("201 - checkout success", 201, "CREATED",
                            envelope("checkout success",
                                     {"id": 12, "user_id": 2, "total_amount": 8499000.0, "status": "waiting_for_payment"}),
                            "POST", url(["cart", "checkout"]), "{}"),
                    example("400 - empty cart", 400, "BAD REQUEST", error("cart is empty"),
                            "POST", url(["cart", "checkout"]), "{}"),
                ]),
        request("Create Order (direct)", "POST", ["orders", ""], raw_body=create_order_body,
                test_script=save_id_script("orderId"),
                examples=[
                    example("201 - order created", 201, "CREATED",
                            envelope("order created",
                                     {"id": 13, "user_id": 2, "total_amount": 8499000.0, "status": "waiting_for_payment"}),
                            "POST", url(["orders", ""]), create_order_body),
                    example("404 - product not found", 404, "NOT FOUND",
                            error("product with id 99999 not found"),
                            "POST", url(["orders", ""]), json.dumps({"items": [{"product_id": 99999, "quantity": 1}]}, indent=2)),
                ]),
        *order_list_get_endpoints(),
        order_status_endpoint("cancelled", "paid", "delivered"),
        order_delete_endpoint(),
        request("Change Order Address", "PUT", ["orders", "{{orderId}}", "address"], raw_body=change_addr_body,
                examples=[
                    example("200 - address changed", 200, "OK",
                            envelope("shipping address updated", {"id": 13, "shipping_city": "Bandung"}),
                            "PUT", url(["orders", "13", "address"]), change_addr_body),
                    example("409 - not allowed", 409, "CONFLICT",
                            error("shipping address can no longer be changed for a 'paid' order"),
                            "PUT", url(["orders", "13", "address"]), change_addr_body),
                ]),
        request("Create Payment", "POST", ["payments", ""], raw_body=create_payment_body,
                test_script=save_id_script("paymentId"),
                examples=[
                    example("201 - payment created", 201, "CREATED",
                            envelope("payment created",
                                     {"id": 5, "order_id": 13, "payment_reference": "order-13-1",
                                      "amount": 8499000.0, "status": "pending",
                                      "snap_token": "a569d043-94b6-4860-a0d0-afb7ea3a1c1c",
                                      "redirect_url": "https://app.sandbox.midtrans.com/snap/v4/redirection/a569d043"}),
                            "POST", url(["payments", ""]), json.dumps({"order_id": 13}, indent=2)),
                    example("409 - not payable", 409, "CONFLICT", error("order is 'paid' and cannot be paid"),
                            "POST", url(["payments", ""]), json.dumps({"order_id": 13}, indent=2)),
                ]),
        request("Get Payment", "GET", ["payments", "{{paymentId}}"],
                examples=[
                    example("200 - payment status", 200, "OK",
                            envelope("success get payment",
                                     {"id": 5, "order_id": 13, "payment_reference": "order-13-1",
                                      "amount": 8499000.0, "status": "paid", "payment_method": "credit_card"}),
                            "GET", url(["payments", "5"])),
                    example("403 - not owner", 403, "FORBIDDEN",
                            error("you don't have permission to view this payment"),
                            "GET", url(["payments", "1"])),
                ]),
    ]

    # ── Seller ───────────────────────────────────────────────────────────────
    seller_items = [
        login_request("seller", "sellerToken", "alice@example.com"),
        ep_refresh(), ep_me(), ep_get_user(), ep_delete_user(),
        ep_get_profile(), ep_put_profile(),
        *category_write_endpoints(),
        *product_write_endpoints(),
        *product_image_endpoints(),
        *order_list_get_endpoints(),
        order_status_endpoint("shipped", "paid", "delivered"),
        order_delete_endpoint(),
    ]

    collection["item"] = [
        public_folder,
        folder("Admin", "Every endpoint an admin is authorized to call. Run 'Login (Admin)' first.",
               "adminToken", admin_items),
        folder("Buyer", "Every endpoint a buyer is authorized to call. Run 'Login (Buyer)' first.",
               "buyerToken", buyer_items),
        folder("Seller", "Every endpoint a seller is authorized to call. Run 'Login (Seller)' first.",
               "sellerToken", seller_items),
    ]

    out = os.path.join(os.path.dirname(__file__), "..", "docs", "revoshop.postman_collection.json")
    with open(out, "w") as f:
        json.dump(collection, f, indent=2)
    print("wrote", os.path.abspath(out))
    for fld in collection["item"]:
        reqs = len(fld["item"])
        ex = sum(len(r.get("response", [])) for r in fld["item"])
        print(f"  {fld['name']}: {reqs} requests, {ex} examples")


if __name__ == "__main__":
    build()
