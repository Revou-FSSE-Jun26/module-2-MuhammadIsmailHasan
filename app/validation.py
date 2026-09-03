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
