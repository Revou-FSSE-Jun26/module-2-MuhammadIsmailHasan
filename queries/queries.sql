SELECT name, created_at FROM categories;

SELECT name, description, price, stock FROM products;
SELECT name, price, stock FROM products WHERE stock BETWEEN 100 AND 1000 ORDER BY price ASC;
SELECT name, price * stock AS product_value FROM products WHERE stock BETWEEN 100 AND 1000 ORDER BY product_value DESC LIMIT 3;

SELECT username, email FROM users WHERE username = 'ismail';
SELECT username, email FROM users WHERE LOWER(username) LIKE 'b%';

SELECT status, COUNT(*) AS count FROM orders GROUP BY status ORDER BY count ASC;
SELECT * from orders WHERE total_amount > 200000 ORDER BY total_amount ASC LIMIT 2;