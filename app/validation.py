ALLOWED_TRANSITIONS = {
    'waiting_for_payment': ['processing'],
    'processing': ['shipped'],
    'shipped': ['delivered'],
    'delivered': [],
    'cancelled': [],
}

ROLE_ALLOWED_TARGET_STATUSES = {
    'buyer': set(),
    'seller': {'processing', 'shipped', 'delivered'},
    'admin': {'processing', 'shipped', 'delivered'},
}

UNDELETABLE_STATUSES = ('shipped', 'delivered')

TERMINAL_STATUSES = ('cancelled', 'delivered')

ACTIVE_ORDER_STATUSES = ('waiting_for_payment', 'processing', 'shipped')
