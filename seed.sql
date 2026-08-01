INSERT INTO categories (name)
VALUES ('Electronics'), ('Home'), ('Fashion'), ('Book');

INSERT INTO products (category_id, name, description, price, stock)
VALUES (1, 'Logitech MX Master 3S', 'Wireless ergonomic mouse by Logitech', 1500000, 200),
    (1, 'Keychron K2', 'Wireless mechanical keyboard by Keychron', 1200000, 100),
    (2, 'IKEA Mug', 'Ceramic coffee mug from IKEA', 50000, 1000),
    (2, 'Philips LED Desk Lamp', 'LED desk lamp by Philips', 350000, 200),
    (3, 'Uniqlo AIRism', 'AIRism cotton t-shirt', 199000, 1500),
    (3, 'Executive Slim Jeans', 'Classic slim fit denim jeans', 899000, 500),
    (4, 'Clean Code', 'Book by Robert C. Martin', 450000, 300),
    (4, 'Atomic Habits', 'Book by James Clear', 350000, 500);

INSERT INTO users (username, email, password_hash)
VALUES ('muhammad', 'muhammad@gmail.com', 'hashed_password_1'),
    ('ismail', 'ismail@gmail.com', 'hashed_password_2'),
    ('hasan', 'hasan@gmail.com', 'hashed_password_3'),
    ('budi', 'budi@gmail.com', 'hashed_password_4'),
    ('joko', 'joko@gmail.com', 'hashed_password_5');
		
INSERT INTO orders (user_id, total_amount, status)
VALUES (1, 650000, 'waitingForPayment'),
    (2, 120000, 'processing'),
    (3, 100000, 'shipped'),
    (4, 400000, 'delivered'),
    (5, 250000, 'cancelled'),
    (1, 300000, 'processing'),
    (2, 500000, 'waitingForPayment'),
    (3, 170000, 'delivered'),
    (4, 250000, 'shipped'),
    (5, 200000, 'processing');
		
INSERT INTO order_items (order_id, product_id, price_ordered, quantity_ordered, discount)
VALUES
    (1, 1, 150000, 1, 0),
    (1, 2, 500000, 1, 0),
    (2, 3, 20000, 1, 0),
    (2, 5, 100000, 1, 0),
    (3, 8, 100000, 1, 0),
    (4, 3, 20000, 5, 0),
    (4, 6, 300000, 1, 0),
    (5, 4, 250000, 1, 0),
    (6, 6, 300000, 1, 0),
    (7, 2, 500000, 1, 0),
    (8, 1, 150000, 1, 0),
    (8, 3, 20000, 1, 0),
    (9, 4, 250000, 1, 0),
    (10, 7, 100000, 2, 0),
    (10, 3, 20000, 5, 0);