import os
import pytest

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from app.extensions import db as _db
from app.models.users import User
from app.models.categories import Category
from app.models.products import Product
from app.auth import hash_password


@pytest.fixture(scope='session')
def app():
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-secret-key',
    })

    with app.app_context():
        _db.create_all()

    yield app

    with app.app_context():
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture(scope='function')
def client(app, db):
    return app.test_client()


@pytest.fixture(scope='function')
def seed_users(db):
    buyer = User(
        username='buyer_test',
        email='buyer@test.com',
        password_hash=hash_password('password123'),
        role='buyer'
    )
    seller = User(
        username='seller_test',
        email='seller@test.com',
        password_hash=hash_password('password123'),
        role='seller'
    )
    seller2 = User(
        username='seller2_test',
        email='seller2@test.com',
        password_hash=hash_password('password123'),
        role='seller'
    )
    admin = User(
        username='admin_test',
        email='admin@test.com',
        password_hash=hash_password('password123'),
        role='admin'
    )

    db.session.add_all([buyer, seller, seller2, admin])
    db.session.commit()

    return {'buyer': buyer, 'seller': seller, 'seller2': seller2, 'admin': admin}


@pytest.fixture(scope='function')
def seed_categories(db):
    cat1 = Category(name='Electronics')
    cat2 = Category(name='Clothing')

    db.session.add_all([cat1, cat2])
    db.session.commit()

    return [cat1, cat2]


@pytest.fixture(scope='function')
def seed_products(db, seed_users, seed_categories):
    categories = seed_categories
    seller = seed_users['seller']

    p1 = Product(
        name='Laptop',
        slug='laptop',
        price=999.99,
        stock=10,
        category_id=categories[0].id,
        seller_id=seller.id
    )
    p2 = Product(
        name='T-Shirt',
        slug='t-shirt',
        price=19.99,
        stock=50,
        category_id=categories[1].id,
        seller_id=seller.id
    )

    db.session.add_all([p1, p2])
    db.session.commit()

    return [p1, p2]


def get_auth_token(client, email, password):
    response = client.post('/api/v1/auth/login', json={
        'email': email,
        'password': password
    })
    data = response.get_json()
    return data.get('access_token')


def auth_header(token):
    return {'Authorization': f'Bearer {token}'}
