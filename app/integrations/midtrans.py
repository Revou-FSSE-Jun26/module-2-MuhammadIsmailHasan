import base64
import json
import urllib.request
import urllib.error

from flask import current_app


SANDBOX_SNAP_URL = 'https://app.sandbox.midtrans.com/snap/v1/transactions'
PRODUCTION_SNAP_URL = 'https://app.midtrans.com/snap/v1/transactions'


class MidtransError(Exception):
    pass


def _snap_url():
    if current_app.config.get('MIDTRANS_IS_PRODUCTION'):
        return PRODUCTION_SNAP_URL
    return SANDBOX_SNAP_URL


def _auth_header():
    server_key = current_app.config.get('MIDTRANS_SERVER_KEY', '')
    raw = f"{server_key}:".encode('utf-8')
    encoded = base64.b64encode(raw).decode('utf-8')
    return f"Basic {encoded}"


def create_snap_transaction(payment_reference, gross_amount, customer,
                            item_details=None, expiry_minutes=None):
    payload = {
        'transaction_details': {
            'order_id': payment_reference,
            'gross_amount': int(gross_amount),
        },
        'credit_card': {'secure': True},
        'customer_details': customer,
    }

    if item_details:
        payload['item_details'] = item_details

    if expiry_minutes:
        payload['expiry'] = {'unit': 'minute', 'duration': int(expiry_minutes)}

    body = json.dumps(payload).encode('utf-8')
    request = urllib.request.Request(
        _snap_url(),
        data=body,
        method='POST',
        headers={
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': _auth_header(),
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode('utf-8', errors='replace')
        current_app.logger.error('midtrans HTTP %s: %s', exc.code, detail)
        raise MidtransError(f"midtrans rejected the request ({exc.code})")
    except urllib.error.URLError as exc:
        current_app.logger.error('midtrans unreachable: %s', exc.reason)
        raise MidtransError("could not reach midtrans")

    token = data.get('token')
    redirect_url = data.get('redirect_url')
    if not token or not redirect_url:
        current_app.logger.error('unexpected midtrans response: %s', data)
        raise MidtransError("midtrans response missing token/redirect_url")

    return {'token': token, 'redirect_url': redirect_url}
