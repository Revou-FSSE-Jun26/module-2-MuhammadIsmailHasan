import os
import random

from locust import HttpUser, TaskSet, task, between, events

LOGIN_EMAIL = os.getenv("LOCUST_EMAIL", "jane@example.com")
LOGIN_PASSWORD = os.getenv("LOCUST_PASSWORD", "password456")

SELLER_EMAIL = os.getenv("LOCUST_SELLER_EMAIL", "alice@example.com")
SELLER_PASSWORD = os.getenv("LOCUST_SELLER_PASSWORD", "passwordabc")

API = "/api/v1"

NEXT_STATUS = {
    "waiting_for_payment": "processing",
    "processing": "shipped",
    "shipped": "delivered",
}


class CustomerJourney(TaskSet):

    def on_start(self):
        self.in_stock = []
        self.product_id = None
        self.order_id = None

    @task(4)
    def view_product(self):
        if self.product_id is None:
            return

        with self.client.get(
            f"{API}/products/{self.product_id}",
            name="GET /products/:id (view details)",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                resp.success()
            else:
                resp.failure(f"unexpected status {resp.status_code}")

    @task(3)
    def browse_products(self):
        with self.client.get(
            f"{API}/products/",
            name="GET /products (browse catalog)",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"unexpected status {resp.status_code}")
                return

            products = (resp.json() or {}).get("data", [])
            self.in_stock = [p for p in products if p.get("stock", 0) > 0]
            if self.in_stock:
                self.product_id = random.choice(self.in_stock)["id"]
            resp.success()

    @task(2)
    def verify_order(self):
        if self.order_id is None:
            return

        with self.client.get(
            f"{API}/orders/{self.order_id}",
            name="GET /orders/:id (verify order)",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"unexpected status {resp.status_code}")
                return

            returned = ((resp.json() or {}).get("data") or {}).get("id")
            if returned == self.order_id:
                resp.success()
            else:
                resp.failure(
                    f"order id mismatch: expected {self.order_id}, got {returned}"
                )

    @task(1)
    def place_order(self):
        if not self.in_stock:
            return

        count = min(random.randint(1, 3), len(self.in_stock))
        chosen = random.sample(self.in_stock, count)
        items = [
            {"product_id": p["id"], "quantity": random.randint(1, 2)}
            for p in chosen
        ]

        with self.client.post(
            f"{API}/orders/",
            json={"items": items},
            name="POST /orders (place order)",
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                self.order_id = ((resp.json() or {}).get("data") or {}).get("id")
                resp.success()
            elif resp.status_code == 422:
                self.order_id = None
                resp.success()
            else:
                self.order_id = None
                resp.failure(f"unexpected status {resp.status_code}")


class SellerFulfillment(TaskSet):

    def on_start(self):
        self.order_ids = []

    @task(3)
    def list_orders(self):
        with self.client.get(
            f"{API}/orders/",
            name="GET /orders (seller list)",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"unexpected status {resp.status_code}")
                return

            orders = (resp.json() or {}).get("data", [])
            self.order_ids = [
                o for o in orders
                if o.get("status") in NEXT_STATUS
            ]
            resp.success()

    @task(2)
    def advance_status(self):
        if not self.order_ids:
            return

        order = random.choice(self.order_ids)
        target = NEXT_STATUS.get(order.get("status"))
        if target is None:
            return

        with self.client.put(
            f"{API}/orders/{order['id']}",
            json={"status": target},
            name="PUT /orders/:id (advance status)",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 400, 403):
                resp.success()
            else:
                resp.failure(f"unexpected status {resp.status_code}")


class ShopUser(HttpUser):

    tasks = [CustomerJourney]
    wait_time = between(1, 3)

    def on_start(self):
        with self.client.post(
            f"{API}/auth/login",
            json={"email": LOGIN_EMAIL, "password": LOGIN_PASSWORD},
            name="POST /auth/login",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200 and (resp.json() or {}).get("access_token"):
                token = resp.json()["access_token"]
                self.client.headers.update({"Authorization": f"Bearer {token}"})
                resp.success()
            else:
                resp.failure(
                    f"login failed ({resp.status_code}); "
                    f"seed data and check credentials"
                )


class SellerUser(HttpUser):

    tasks = [SellerFulfillment]
    wait_time = between(2, 5)

    def on_start(self):
        with self.client.post(
            f"{API}/auth/login",
            json={"email": SELLER_EMAIL, "password": SELLER_PASSWORD},
            name="POST /auth/login (seller)",
            catch_response=True,
        ) as resp:
            if resp.status_code == 200 and (resp.json() or {}).get("access_token"):
                token = resp.json()["access_token"]
                self.client.headers.update({"Authorization": f"Bearer {token}"})
                resp.success()
            else:
                resp.failure(
                    f"seller login failed ({resp.status_code}); "
                    f"seed data and check credentials"
                )


@events.quitting.add_listener
def _log_summary(environment, **kwargs):
    stats = environment.stats.total
    if stats.num_requests == 0:
        print("\n[locust] No requests were made - is the API running and seeded?")
        return
    print(
        f"\n[locust] requests={stats.num_requests} "
        f"failures={stats.num_failures} "
        f"fail_ratio={stats.fail_ratio:.2%} "
        f"median={stats.median_response_time}ms "
        f"p95={stats.get_response_time_percentile(0.95)}ms"
    )
