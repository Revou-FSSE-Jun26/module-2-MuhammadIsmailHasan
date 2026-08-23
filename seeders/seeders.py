"""
Seeder untuk testing products dan users endpoint
Jalankan dengan: python -c "from seeders import seed_test_data; seed_test_data()"
"""

from app import app
from helper.utils import db
from models import User, Product, Category
import bcrypt
from datetime import datetime, timedelta

def clear_tables():
    """Hapus semua data dari table untuk testing fresh"""
    try:
        # Delete in order to respect foreign key constraints
        db.session.query(Product).delete()
        db.session.query(User).delete()
        db.session.query(Category).delete()
        db.session.commit()
        print("✓ Tables cleared")
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error clearing tables: {e}")
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
        print(f"✓ Created {len(categories)} categories")
        return categories
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error seeding categories: {e}")
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
            'role': 'user'
        },
        {
            'username': 'bob_wilson',
            'email': 'bob@example.com',
            'password': 'password789',
            'role': 'user'
        },
        {
            'username': 'alice_brown',
            'email': 'alice@example.com',
            'password': 'passwordabc',
            'role': 'user'
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
        print(f"✓ Created {len(users)} users")
        return users
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error seeding users: {e}")
        raise


def seed_products():
    """Seed produk untuk testing"""
    # Get categories
    electronics_cat = Category.query.filter_by(name='Electronics').first()
    clothing_cat = Category.query.filter_by(name='Clothing').first()
    food_cat = Category.query.filter_by(name='Food & Beverages').first()
    
    products_data = [
        # Electronics
        {
            'category_id': electronics_cat.id if electronics_cat else None,
            'name': 'Laptop Pro 15"',
            'description': 'High-performance laptop with 16GB RAM and 512GB SSD',
            'price': 1299.99,
            'stock': 15
        },
        {
            'category_id': electronics_cat.id if electronics_cat else None,
            'name': 'Wireless Mouse',
            'description': 'Ergonomic wireless mouse with long battery life',
            'price': 29.99,
            'stock': 50
        },
        {
            'category_id': electronics_cat.id if electronics_cat else None,
            'name': 'USB-C Cable',
            'description': '2-meter USB-C charging and data cable',
            'price': 9.99,
            'stock': 100
        },
        {
            'category_id': electronics_cat.id if electronics_cat else None,
            'name': 'Monitor 4K 27"',
            'description': '4K IPS monitor with USB-C connectivity',
            'price': 599.99,
            'stock': 10
        },
        {
            'category_id': electronics_cat.id if electronics_cat else None,
            'name': 'Mechanical Keyboard',
            'description': 'RGB mechanical keyboard with switches',
            'price': 149.99,
            'stock': 25
        },
        
        # Clothing
        {
            'category_id': clothing_cat.id if clothing_cat else None,
            'name': 'Cotton T-Shirt',
            'description': '100% cotton casual t-shirt, available in multiple colors',
            'price': 19.99,
            'stock': 75
        },
        {
            'category_id': clothing_cat.id if clothing_cat else None,
            'name': 'Denim Jeans',
            'description': 'Classic blue denim jeans with comfortable fit',
            'price': 49.99,
            'stock': 40
        },
        {
            'category_id': clothing_cat.id if clothing_cat else None,
            'name': 'Hoodie',
            'description': 'Warm fleece hoodie, perfect for winter',
            'price': 59.99,
            'stock': 30
        },
        
        # Food & Beverages
        {
            'category_id': food_cat.id if food_cat else None,
            'name': 'Organic Coffee Beans',
            'description': 'Premium arabica coffee beans, 1kg pack',
            'price': 15.99,
            'stock': 60
        },
        {
            'category_id': food_cat.id if food_cat else None,
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
                name=product_data['name'],
                description=product_data['description'],
                price=product_data['price'],
                stock=product_data['stock']
            )
            products.append(product)
        
        db.session.add_all(products)
        db.session.commit()
        print(f"✓ Created {len(products)} products")
        return products
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error seeding products: {e}")
        raise


def seed_test_data():
    """Run all seeders"""
    with app.app_context():
        print("\n" + "="*50)
        print("Starting test data seeding...")
        print("="*50 + "\n")
        
        try:
            clear_tables()
            seed_categories()
            seed_users()
            seed_products()
            
            print("\n" + "="*50)
            print("✓ Test data seeding completed successfully!")
            print("="*50 + "\n")
            
            # Print summary
            print("Summary:")
            print(f"  Users: {User.query.count()}")
            print(f"  Products: {Product.query.count()}")
            print(f"  Categories: {Category.query.count()}")
            print("\nTest Users (untuk login testing):")
            for user in User.query.all():
                print(f"  - {user.username} ({user.email}) - Role: {user.role}")
            
        except Exception as e:
            print(f"\n✗ Seeding failed: {e}")
            raise


if __name__ == '__main__':
    seed_test_data()
