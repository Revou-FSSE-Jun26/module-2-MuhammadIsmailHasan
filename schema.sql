CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    category_id INTEGER,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(1000),
    price NUMERIC(11, 2) NOT NULL
			CONSTRAINT price_positive 
			CHECK (price > 0),
    stock INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_products_category 
        FOREIGN KEY (category_id) REFERENCES categories(id)
        ON DELETE SET NULL
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    total_amount NUMERIC(14, 2) NOT NULL
			CONSTRAINT total_amount_positive
			CHECK (total_amount >= 0),
    status VARCHAR(25) NOT NULL DEFAULT 'waitingForPayment'
			CONSTRAINT status_valid 
			CHECK (status IN ('waitingForPayment', 'processing', 'shipped', 'delivered', 'cancelled')),
    ordered_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_orders_user 
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE RESTRICT
);

CREATE TABLE order_items (
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    price_ordered NUMERIC(14, 2) NOT NULL
			CONSTRAINT price_ordered_positive
			CHECK (price_ordered >= 0),
    quantity_ordered INTEGER DEFAULT 1 NOT NULL
			CONSTRAINT quantity_ordered_positive 
			CHECK (quantity_ordered > 0),
    discount NUMERIC(3, 2),
    PRIMARY KEY (order_id, product_id),
    CONSTRAINT fk_oi_order 
        FOREIGN KEY (order_id) REFERENCES orders(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_oi_product
        FOREIGN KEY (product_id) REFERENCES products(id)
        ON DELETE RESTRICT
);

CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_oi_order ON order_items(order_id);
CREATE INDEX idx_oi_product ON order_items(product_id);
-- checking the fk index
SELECT indexname, indexdef
FROM pg_indexes 	
WHERE tablename IN ('products', 'orders', 'order_items');