-- error check constaint
INSERT INTO products (category_id, name, price, stock)
VALUES (1, 'Invalid Product', -1000, 10);

INSERT INTO orders (user_id, total_amount)
VALUES (1, -50000);

INSERT INTO orders (user_id, total_amount, status)
VALUES (1, 100000, 'paid');

INSERT INTO order_items (order_id, product_id, price_ordered, quantity_ordered, discount)
VALUES (1, 1, 150000, 0, 0);

INSERT INTO order_items (order_id, product_id, price_ordered, quantity_ordered, discount)
VALUES (1, 2, -500000, 1, 0);


-- error unique constaint
INSERT INTO users (username, email, password_hash)
VALUES ('muhammad', 'new@gmail.com', 'hash');

INSERT INTO users (username, email, password_hash)
VALUES ('newuser', 'muhammad@gmail.com', 'hash');


-- error fk relationship
INSERT INTO products (category_id, name, price, stock)
VALUES (999, 'Unknown Category Product', 100000, 10);

INSERT INTO orders (user_id, total_amount)
VALUES (999, 100000);

INSERT INTO order_items (order_id, product_id, price_ordered, quantity_ordered, discount)
VALUES (1, 999, 100000, 1, 0);


-- error remove fk constraint
DELETE FROM users
WHERE id = 1;

DELETE FROM products
WHERE id = 1;

-- pass remove fk constraint
DELETE FROM orders
WHERE id = 1;

DELETE FROM categories
WHERE id = 1;