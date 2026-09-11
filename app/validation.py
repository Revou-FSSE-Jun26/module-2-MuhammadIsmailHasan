ALLOWED_TRANSITIONS = {
    'waiting_for_payment': ['paid', 'cancelled'],
    'paid': ['processing', 'cancelled'],
    'processing': ['shipped', 'cancelled'],
    'shipped': ['delivered'],
    'delivered': ['returned'],
    'returned': [],
    'cancelled': [],
}

ROLE_ALLOWED_TARGET_STATUSES = {
    'buyer': {'returned', 'cancelled'},
    'seller': {'paid', 'processing', 'shipped', 'delivered', 'cancelled'},
    'admin': {'paid', 'processing', 'shipped', 'delivered', 'returned', 'cancelled'},
}

RESTOCK_STATUSES = ('cancelled', 'returned')

REFUNDABLE_STATUSES = ('paid', 'processing')

UNDELETABLE_STATUSES = ('waiting_for_payment', 'paid', 'processing', 'shipped')

TERMINAL_STATUSES = ('cancelled', 'returned')

ACTIVE_ORDER_STATUSES = ('waiting_for_payment', 'paid', 'processing', 'shipped')


PAYMENT_STATUSES = ('pending', 'paid', 'expired', 'failed', 'refunded')

MIDTRANS_STATUS_TO_PAYMENT_STATUS = {
    'settlement': 'paid',
    'pending': 'pending',
    'authorize': 'pending',
    'expire': 'expired',
    'cancel': 'failed',
    'deny': 'failed',
    'failure': 'failed',
    'refund': 'refunded',
    'partial_refund': 'refunded',
}

PAYMENT_STATUS_TO_ORDER_STATUS = {
    'paid': 'paid',
    'expired': 'cancelled',
    'refunded': 'cancelled',
}
