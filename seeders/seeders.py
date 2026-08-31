"""
Seeder untuk testing products dan users endpoint
Jalankan dengan: python -c "from seeders import seed_test_data; seed_test_data()"
"""

from app import create_app
from app.extensions import db
from app.models import (
    User, Product, Category, Order, OrderItem, ProductImage, Cart, CartItem,
    UserProfile, UserAddress
)
from app.slug import slugify
import bcrypt
from datetime import timedelta
from decimal import Decimal
from app.utils.timezone import utcnow

app = create_app()


def clear_tables():
    """Hapus semua data dari table untuk testing fresh"""
    try:
        db.session.query(CartItem).delete()
        db.session.query(Cart).delete()
        db.session.query(OrderItem).delete()
        db.session.query(Order).delete()
        db.session.query(ProductImage).delete()
        db.session.query(Product).delete()
        db.session.query(UserAddress).delete()
        db.session.query(UserProfile).delete()
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
            'password': 'password123',
            'role': 'buyer'
        },
        {
            'username': 'bob_wilson',
            'email': 'bob@example.com',
            'password': 'password123',
            'role': 'buyer'
        },
        {
            'username': 'alice_brown',
            'email': 'alice@example.com',
            'password': 'password123',
            'role': 'seller'
        },
        {
            'username': 'charlie_davis',
            'email': 'charlie@example.com',
            'password': 'password123',
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
                last_login=utcnow() - timedelta(days=1)
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


def seed_product_images():
    products = Product.query.order_by(Product.id).all()

    if not products:
        print("Cannot seed product images: no products found")
        return

    images = []
    try:
        for index, product in enumerate(products):
            slug = product.slug or slugify(product.name)
            image_count = 3 if index < 3 else 1
            for order in range(image_count):
                images.append(
                    ProductImage(
                        product_id=product.id,
                        url=f'https://cdn.example.com/products/{slug}-{order + 1}.jpg',
                        order=order,
                    )
                )

        db.session.add_all(images)
        db.session.commit()
        print(f"Created {len(images)} product images")
        return images
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding product images: {e}")
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
            'tracking_id': 'JNE-0001234567',
            'items': [
                {'product': products[3], 'quantity': 1},
            ]
        },
        {
            'user': buyer2,
            'status': 'delivered',
            'tracking_id': 'SICEPAT-0007654321',
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

            default_address = UserAddress.query.filter_by(
                user_id=order_data['user'].id, is_default=True, is_active=True
            ).first()

            order = Order(
                user_id=order_data['user'].id,
                total_amount=total_amount,
                status=order_data['status'],
                is_active=order_data.get('is_active', True),
                ordered_at=utcnow() - timedelta(days=len(orders_data)),
                shipping_recipient_name=default_address.recipient_name if default_address else None,
                shipping_phone=default_address.phone if default_address else None,
                shipping_address_line=default_address.address_line if default_address else None,
                shipping_city=default_address.city if default_address else None,
                shipping_postal_code=default_address.postal_code if default_address else None,
                tracking_id=order_data.get('tracking_id'),
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


def seed_carts():
    buyer = User.query.filter_by(username='jane_smith').first()
    if not buyer:
        print("Cannot seed carts: buyer not found")
        return

    alice = User.query.filter_by(username='alice_brown').first()
    charlie = User.query.filter_by(username='charlie_davis').first()

    alice_product = (
        Product.query.filter_by(seller_id=alice.id).first() if alice else None
    )
    charlie_product = (
        Product.query.filter_by(seller_id=charlie.id).first() if charlie else None
    )

    picks = [p for p in (alice_product, charlie_product) if p is not None]
    if not picks:
        print("Cannot seed carts: no seller products found")
        return

    try:
        cart = Cart(user_id=buyer.id)
        db.session.add(cart)
        db.session.flush()

        for index, product in enumerate(picks):
            db.session.add(CartItem(
                cart_id=cart.id,
                product_id=product.id,
                quantity=index + 1,
            ))

        db.session.commit()
        print(f"Created 1 cart with {len(picks)} items")
        return cart
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding carts: {e}")
        raise


def seed_user_profiles():
    profiles_data = {
        'john_doe': {'full_name': 'John Doe', 'phone': '+62811000001'},
        'jane_smith': {'full_name': 'Jane Smith', 'phone': '+62811000002'},
        'bob_wilson': {'full_name': 'Bob Wilson', 'phone': '+62811000003'},
        'alice_brown': {'full_name': 'Alice Brown', 'phone': '+62811000004'},
        'charlie_davis': {'full_name': 'Charlie Davis', 'phone': '+62811000005'},
    }

    try:
        profiles = []
        for username, data in profiles_data.items():
            user = User.query.filter_by(username=username).first()
            if not user:
                continue
            profiles.append(UserProfile(
                user_id=user.id,
                full_name=data['full_name'],
                phone=data['phone'],
            ))
        db.session.add_all(profiles)
        db.session.commit()
        print(f"Created {len(profiles)} user profiles")
        return profiles
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding user profiles: {e}")
        raise


def seed_user_addresses():
    addresses_data = {
        'jane_smith': [
            {
                'label': 'Home', 'recipient_name': 'Jane Smith',
                'phone': '+62811000002', 'address_line': 'Jl. Melati No. 1',
                'city': 'Jakarta', 'postal_code': '10110', 'is_default': True,
            },
            {
                'label': 'Office', 'recipient_name': 'Jane Smith',
                'phone': '+62811000002', 'address_line': 'Jl. Sudirman No. 99',
                'city': 'Jakarta', 'postal_code': '10220', 'is_default': False,
            },
        ],
        'bob_wilson': [
            {
                'label': 'Home', 'recipient_name': 'Bob Wilson',
                'phone': '+62811000003', 'address_line': 'Jl. Kenanga No. 5',
                'city': 'Bandung', 'postal_code': '40111', 'is_default': True,
            },
        ],
    }

    try:
        addresses = []
        for username, entries in addresses_data.items():
            user = User.query.filter_by(username=username).first()
            if not user:
                continue
            for entry in entries:
                addresses.append(UserAddress(
                    user_id=user.id,
                    label=entry['label'],
                    recipient_name=entry['recipient_name'],
                    phone=entry['phone'],
                    address_line=entry['address_line'],
                    city=entry['city'],
                    postal_code=entry['postal_code'],
                    is_default=entry['is_default'],
                ))
        db.session.add_all(addresses)
        db.session.commit()
        print(f"Created {len(addresses)} user addresses")
        return addresses
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding user addresses: {e}")
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
            seed_user_profiles()
            seed_user_addresses()
            seed_products()
            seed_product_images()
            seed_orders()
            seed_carts()

            print("\n" + "=" * 50)
            print("Test data seeding completed successfully!")
            print("=" * 50 + "\n")

            print("Summary:")
            print(f"  Users: {User.query.count()}")
            print(f"  Categories: {Category.query.count()}")
            print(f"  Products: {Product.query.count()}")
            print(f"  Product Images: {ProductImage.query.count()}")
            print(f"  Orders: {Order.query.count()}")
            print(f"  Order Items: {OrderItem.query.count()}")
            print(f"  Carts: {Cart.query.count()}")
            print(f"  Cart Items: {CartItem.query.count()}")
            print(f"  User Profiles: {UserProfile.query.count()}")
            print(f"  User Addresses: {UserAddress.query.count()}")

        except Exception as e:
            print(f"\nSeeding failed: {e}")
            raise


if __name__ == '__main__':
    seed_test_data()
