"""
Seeder untuk testing products dan users endpoint
Jalankan dengan: python -c "from seeders import seed_test_data; seed_test_data()"
"""

from app import create_app
from app.extensions import db
from app.models import User, Product, Category, Order, OrderItem
from app.slug import slugify
import bcrypt
from datetime import datetime, timedelta
from decimal import Decimal

app = create_app()


def clear_tables():
    """Hapus semua data dari table untuk testing fresh"""
    try:
        db.session.query(OrderItem).delete()
        db.session.query(Order).delete()
        db.session.query(Product).delete()
        db.session.query(User).delete()
        db.session.query(Category).delete()
        db.session.commit()
        print("Tables cleared")
    except Exception as e:
        db.session.rollback()
        print(f"Error clearing tables: {e}")
        raise


def seed_categories():
    """Seed kategori produk"""
    categories = [
        Category(name='Electronics'),
        Category(name='Clothing'),
        Category(name='Food & Beverages'),
        Category(name='Books'),
        Category(name='Sports'),
    ]

    try:
        db.session.add_all(categories)
        db.session.commit()
        print(f"Created {len(categories)} categories")
        return categories
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding categories: {e}")
        raise


def seed_users():
    """Seed user untuk testing"""
    users_data = [
        {
            'username': 'john_doe',
            'email': 'john@example.com',
            'password': 'password123',
            'role': 'admin'
        },
        {
            'username': 'jane_smith',
            'email': 'jane@example.com',
            'password': 'password456',
            'role': 'buyer'
        },
        {
            'username': 'bob_wilson',
            'email': 'bob@example.com',
            'password': 'password789',
            'role': 'buyer'
        },
        {
            'username': 'alice_brown',
            'email': 'alice@example.com',
            'password': 'passwordabc',
            'role': 'seller'
        },
        {
            'username': 'charlie_davis',
            'email': 'charlie@example.com',
            'password': 'passworddef',
            'role': 'seller'
        },
    ]

    users = []
    try:
        for user_data in users_data:
            password_hash = bcrypt.hashpw(
                user_data['password'].encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=password_hash,
                role=user_data['role'],
                last_login=datetime.utcnow() - timedelta(days=1)
            )
            users.append(user)

        db.session.add_all(users)
        db.session.commit()
        print(f"Created {len(users)} users")
        return users
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding users: {e}")
        raise


def seed_products():
    """Seed produk untuk testing"""
    electronics_cat = Category.query.filter_by(name='Electronics').first()
    clothing_cat = Category.query.filter_by(name='Clothing').first()
    food_cat = Category.query.filter_by(name='Food & Beverages').first()

    seller_alice = User.query.filter_by(username='alice_brown').first()
    seller_charlie = User.query.filter_by(username='charlie_davis').first()
    alice_id = seller_alice.id if seller_alice else None
    charlie_id = seller_charlie.id if seller_charlie else None

    products_data = [
        {
            'category_id': electronics_cat.id if electronics_cat else None,
            'seller_id': alice_id,
            'name': 'Laptop Pro 15"',
            'description': 'High-performance laptop with 16GB RAM and 512GB SSD',
            'price': 1299.99,
            'stock': 15
        },
        {
            'category_id': electronics_cat.id if electronics_cat else None,
            'seller_id': alice_id,
            'name': 'Wireless Mouse',
            'description': 'Ergonomic wireless mouse with long battery life',
            'price': 29.99,
            'stock': 50
        },
        {
            'category_id': electronics_cat.id if electronics_cat else None,
            'seller_id': alice_id,
            'name': 'USB-C Cable',
            'description': '2-meter USB-C charging and data cable',
            'price': 9.99,
            'stock': 100
        },
        {
            'category_id': electronics_cat.id if electronics_cat else None,
            'seller_id': alice_id,
            'name': 'Monitor 4K 27"',
            'description': '4K IPS monitor with USB-C connectivity',
            'price': 599.99,
            'stock': 10
        },
        {
            'category_id': electronics_cat.id if electronics_cat else None,
            'seller_id': alice_id,
            'name': 'Mechanical Keyboard',
            'description': 'RGB mechanical keyboard with switches',
            'price': 149.99,
            'stock': 25
        },
        {
            'category_id': clothing_cat.id if clothing_cat else None,
            'seller_id': charlie_id,
            'name': 'Cotton T-Shirt',
            'description': '100% cotton casual t-shirt, available in multiple colors',
            'price': 19.99,
            'stock': 75
        },
        {
            'category_id': clothing_cat.id if clothing_cat else None,
            'seller_id': charlie_id,
            'name': 'Denim Jeans',
            'description': 'Classic blue denim jeans with comfortable fit',
            'price': 49.99,
            'stock': 40
        },
        {
            'category_id': clothing_cat.id if clothing_cat else None,
            'seller_id': charlie_id,
            'name': 'Hoodie',
            'description': 'Warm fleece hoodie, perfect for winter',
            'price': 59.99,
            'stock': 30
        },
        {
            'category_id': food_cat.id if food_cat else None,
            'seller_id': charlie_id,
            'name': 'Organic Coffee Beans',
            'description': 'Premium arabica coffee beans, 1kg pack',
            'price': 15.99,
            'stock': 60
        },
        {
            'category_id': food_cat.id if food_cat else None,
            'seller_id': charlie_id,
            'name': 'Green Tea',
            'description': 'Organic green tea, 50 tea bags',
            'price': 8.99,
            'stock': 80
        },
    ]

    products = []
    try:
        for product_data in products_data:
            product = Product(
                category_id=product_data['category_id'],
                seller_id=product_data['seller_id'],
                name=product_data['name'],
                slug=slugify(product_data['name']),
                description=product_data['description'],
                price=product_data['price'],
                stock=product_data['stock']
            )
            products.append(product)

        db.session.add_all(products)
        db.session.commit()
        print(f"Created {len(products)} products")
        return products
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding products: {e}")
        raise


def seed_orders():
    """Seed orders dengan berbagai status untuk testing"""
    buyer = User.query.filter_by(username='jane_smith').first()
    buyer2 = User.query.filter_by(username='bob_wilson').first()
    products = Product.query.limit(5).all()

    if not buyer or not buyer2 or len(products) < 3:
        print("Cannot seed orders: missing users or products")
        return

    orders_data = [
        {
            'user': buyer,
            'status': 'waiting_for_payment',
            'items': [
                {'product': products[0], 'quantity': 1},
                {'product': products[1], 'quantity': 2},
            ]
        },
        {
            'user': buyer,
            'status': 'processing',
            'items': [
                {'product': products[2], 'quantity': 1},
            ]
        },
        {
            'user': buyer,
            'status': 'shipped',
            'items': [
                {'product': products[3], 'quantity': 1},
            ]
        },
        {
            'user': buyer2,
            'status': 'delivered',
            'items': [
                {'product': products[0], 'quantity': 2},
                {'product': products[4], 'quantity': 1},
            ]
        },
        {
            'user': buyer2,
            'status': 'cancelled',
            'is_active': False,
            'items': [
                {'product': products[1], 'quantity': 3},
            ]
        },
    ]

    try:
        for order_data in orders_data:
            total_amount = Decimal('0')
            items_to_add = []

            for item in order_data['items']:
                product = item['product']
                quantity = item['quantity']
                unit_price = product.price
                sub_total = unit_price * quantity
                total_amount += Decimal(str(float(sub_total)))
                items_to_add.append({
                    'product_id': product.id,
                    'unit_price': unit_price,
                    'quantity': quantity,
                    'sub_total': sub_total
                })

            order = Order(
                user_id=order_data['user'].id,
                total_amount=total_amount,
                status=order_data['status'],
                is_active=order_data.get('is_active', True),
                ordered_at=datetime.utcnow() - timedelta(days=len(orders_data))
            )
            db.session.add(order)
            db.session.flush()

            for item_data in items_to_add:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item_data['product_id'],
                    unit_price=item_data['unit_price'],
                    quantity=item_data['quantity'],
                    sub_total=item_data['sub_total']
                )
                db.session.add(order_item)

        db.session.commit()
        print(f"Created {len(orders_data)} orders")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding orders: {e}")
        raise


def seed_test_data():
    """Run all seeders"""
    with app.app_context():
        print("\n" + "=" * 50)
        print("Starting test data seeding...")
        print("=" * 50 + "\n")

        try:
            clear_tables()
            seed_categories()
            seed_users()
            seed_products()
            seed_orders()

            print("\n" + "=" * 50)
            print("Test data seeding completed successfully!")
            print("=" * 50 + "\n")

            print("Summary:")
            print(f"  Users: {User.query.count()}")
            print(f"  Categories: {Category.query.count()}")
            print(f"  Products: {Product.query.count()}")
            print(f"  Orders: {Order.query.count()}")
            print(f"  Order Items: {OrderItem.query.count()}")

        except Exception as e:
            print(f"\nSeeding failed: {e}")
            raise


if __name__ == '__main__':
    seed_test_data()
