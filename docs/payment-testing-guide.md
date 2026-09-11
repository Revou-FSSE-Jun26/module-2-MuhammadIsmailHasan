# Payment Testing Guide (Midtrans)

How to run and test the payment feature on a local machine.

## What This Feature Does

1. A buyer starts a payment for an order.
2. The API asks Midtrans to create a payment page and returns its link.
3. The buyer opens the link and picks a payment method on Midtrans.
4. After the buyer pays, Midtrans calls the webhook.
5. The API updates the payment and the order (for example, to `paid`).

One order can have many payment attempts. A failed attempt keeps the order as
`waiting_for_payment`, so the buyer can retry. Only an expired payment link
cancels the order.

## Prerequisites

- Python virtual environment is active.
- PostgreSQL is running and the app's database exists.
- Midtrans sandbox account (free).

## Step 1: Get Midtrans Sandbox Keys

Sandbox uses fake money, so it is safe for testing.

1. Sign up at https://dashboard.sandbox.midtrans.com
2. Switch the dashboard environment to **Sandbox** (toggle near the top).
3. Open **Settings -> Access Keys**.
4. Copy the **Server Key** and the **Client Key**.

Note: modern sandbox keys may or may not start with `SB-`. The prefix is not a
reliable signal. What matters is that the keys are copied from the **Sandbox**
tab, not Production.

## Step 2: Add the Keys to `.env`

Add these to the local `.env` file (never to `.env.example`, never commit
`.env`):

```
MIDTRANS_SERVER_KEY="your-sandbox-server-key"
MIDTRANS_CLIENT_KEY="your-sandbox-client-key"
MIDTRANS_IS_PRODUCTION=false
MIDTRANS_EXPIRY_MINUTES=1440
```

Important: the app reads `.env` once at startup. After changing `.env`, restart
the app or the new keys will not take effect.

## Step 3: macOS Only — Install SSL Certificates

On macOS with a python.org build of Python, the outbound HTTPS call to Midtrans
can fail with "could not reach midtrans" because the trusted certificates are
not installed. Fix it once by running the bundled script (adjust the version):

```bash
/Applications/Python\ 3.x/Install\ Certificates.command
```

Linux and most other setups already trust the certificates and can skip this.

## Step 4: Update and Seed the Database

```bash
FLASK_APP=run.py flask db upgrade
python -m seeders.seeders
```

This creates the `payments` table and adds sample users, products (Indonesian
items priced in whole rupiah), and orders.

## Step 5: Start the App

```bash
python run.py
```

Keep this terminal open. Use a new terminal for the calls below.

## Step 6: Log In

```bash
curl -s -X POST http://127.0.0.1:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","password":"password123"}'
```

Copy the `access_token` from the response.

## Step 7: Find a Payable Order

The order must belong to the logged-in buyer and have status
`waiting_for_payment`.

```bash
curl -s http://127.0.0.1:5000/api/v1/orders/ \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

Note the `id` of a `waiting_for_payment` order. If there is none, create one:

```bash
curl -s -X POST http://127.0.0.1:5000/api/v1/orders/ \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"items":[{"product_id":1,"quantity":1}]}'
```

## Step 8: Create a Payment

```bash
curl -s -X POST http://127.0.0.1:5000/api/v1/payments/ \
  -H "Authorization: Bearer ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"order_id": ORDER_ID}'
```

Success returns status `201` with a `snap_token` and a `redirect_url`.

Open the `redirect_url` in a browser to see the Midtrans page where the buyer
picks a payment method. This confirms the app-to-Midtrans part works.

## Step 9: Pay With the Sandbox Simulator

Use the Midtrans payment simulator to complete sandbox payments:

https://simulator.sandbox.midtrans.com

For a credit card on the Snap page, the common test card is:

- Number: `4811 1111 1111 1114`
- CVV: `123`
- Expiry: any future date
- OTP / 3DS: `112233`

Other methods (virtual account, e-wallet, QRIS) can be completed from the
simulator link above.

## Step 10: Test the Webhook

Midtrans cannot reach `localhost`, so a public URL is needed.

1. Run a tunnel, for example ngrok:

   ```bash
   ngrok http 5000
   ```

2. Copy the public URL, for example `https://abc123.ngrok-free.app`.
3. In the Midtrans dashboard, open **Settings -> Configuration**.
4. Set the **Payment Notification URL** to:

   ```
   https://abc123.ngrok-free.app/api/v1/payments/webhook/midtrans
   ```

Pay again (Steps 8 and 9). Watch the app terminal for a log line like
`payment X -> paid, order Y reacted`.

## Step 11: Check the Result

```bash
curl -s http://127.0.0.1:5000/api/v1/orders/ORDER_ID \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

The order status should now be `paid`.

## Testing a Retry

To see retry behavior, make a payment fail (for example, cancel it in the
simulator, or use a card that gets denied). The payment attempt becomes
`failed`, but the order stays `waiting_for_payment`. Call `POST /payments`
again for the same order to create a new attempt (`order-<id>-2`), then complete
it. The order should move to `paid`.

## How Often the Webhook Fires

- Midtrans sends a notification on every status change (event-driven), not on a
  timer. A single payment may produce several: `pending`, then `settlement`, and
  possibly `refund` later.
- If the endpoint does not return `200`, Midtrans retries the same notification
  on increasing intervals for about a day. The handler is idempotent (it ignores
  a duplicate that matches the current status) and always returns `200`.

## Short Version (No Webhook)

Steps 1 to 8 alone test the main part: create a payment and get the Midtrans
link. The webhook part (Steps 10 and 11) needs a tunnel and is optional for a
first run.

## Common Issues

- **"could not reach midtrans"** — usually the macOS SSL certificate step
  (Step 3). It is a network-level failure before the request reaches Midtrans.
- **"Access denied ... unauthorized transaction"** — wrong keys, or the app was
  not restarted after editing `.env`. Confirm sandbox keys and restart the app.
- **"gross_amount is not equal to the sum of item_details"** — item prices must
  add up exactly to the total. Use whole-rupiah product prices; the seeder
  already does this.

## Sample Users (From Seeder)

| Email | Password | Role |
| --- | --- | --- |
| john@example.com | password123 | admin |
| jane@example.com | password123 | buyer |
| bob@example.com | password123 | buyer |
| alice@example.com | password123 | seller |
| charlie@example.com | password123 | seller |
