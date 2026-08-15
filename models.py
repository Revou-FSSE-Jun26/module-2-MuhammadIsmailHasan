from utils import db

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.FetchedValue())



class OrderItem(db.Model):
    __tablename__ = 'order_items'
    __table_args__ = (
        db.CheckConstraint('price_ordered >= 0::numeric'),
        db.CheckConstraint('quantity_ordered > 0')
    )

    order_id = db.Column(db.ForeignKey('orders.id', ondelete='CASCADE'), primary_key=True, nullable=False, index=True)
    product_id = db.Column(db.ForeignKey('products.id', ondelete='RESTRICT'), primary_key=True, nullable=False, index=True)
    price_ordered = db.Column(db.Numeric(14, 2), nullable=False)
    quantity_ordered = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue())
    discount = db.Column(db.Numeric(3, 2))

    order = db.relationship('Order', primaryjoin='OrderItem.order_id == Order.id', backref='order_items')
    product = db.relationship('Product', primaryjoin='OrderItem.product_id == Product.id', backref='order_items')



class Order(db.Model):
    __tablename__ = 'orders'
    __table_args__ = (
        db.CheckConstraint("status::text = ANY (ARRAY['waitingForPayment'::character varying, 'processing'::character varying, 'shipped'::character varying, 'delivered'::character varying, 'cancelled'::character varying]::text[])"),
        db.CheckConstraint('total_amount >= 0::numeric')
    )

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    user_id = db.Column(db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)
    total_amount = db.Column(db.Numeric(14, 2), nullable=False)
    status = db.Column(db.String(25), nullable=False, server_default=db.FetchedValue())
    ordered_at = db.Column(db.DateTime, server_default=db.FetchedValue())

    user = db.relationship('User', primaryjoin='Order.user_id == User.id', backref='orders')



class Product(db.Model):
    __tablename__ = 'products'
    __table_args__ = (
        db.CheckConstraint('price > 0::numeric'),
    )

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    category_id = db.Column(db.ForeignKey('categories.id', ondelete='SET NULL'), index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(1000))
    price = db.Column(db.Numeric(11, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False, server_default=db.FetchedValue())
    created_at = db.Column(db.DateTime, server_default=db.FetchedValue())

    category = db.relationship('Category', primaryjoin='Product.category_id == Category.id', backref='products')



class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, server_default=db.FetchedValue())
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.FetchedValue())
