from app.models.products import Product
from app.models.orders import Order, OrderItem
from app.extensions import db


class ProductRepository:
    """
    Repository layer for Product entity.
    Responsible ONLY for data access — no business logic here.
    """

    @staticmethod
    def get_all(filters=None, sort_by='id', order='asc', page=1, limit=10):
        """
        Retrieve paginated products with optional filters.

        Args:
            filters (dict): Optional filters (name, category_id, min_price, max_price)
            sort_by (str): Column to sort by
            order (str): 'asc' or 'desc'
            page (int): Page number
            limit (int): Items per page

        Returns:
            Pagination object from SQLAlchemy
        """
        query = Product.query.filter_by(is_active=True)

        if filters:
            if filters.get('name'):
                query = query.filter(Product.name.ilike(f"%{filters['name']}%"))
            if filters.get('category_id'):
                query = query.filter_by(category_id=filters['category_id'])
            if filters.get('min_price') is not None:
                query = query.filter(Product.price >= filters['min_price'])
            if filters.get('max_price') is not None:
                query = query.filter(Product.price <= filters['max_price'])

        sort_columns = {
            'id': Product.id,
            'name': Product.name,
            'price': Product.price,
            'created_at': Product.created_at,
        }
        sort_column = sort_columns.get(sort_by, Product.id)

        if order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        return query.paginate(page=page, per_page=limit, error_out=False)

    @staticmethod
    def get_by_id(product_id):
        """Find a single active product by ID."""
        return Product.query.filter_by(id=product_id, is_active=True).first()

    @staticmethod
    def create(data):
        """
        Persist a new product to the database.

        Args:
            data (dict): Product fields (name, description, price, stock, category_id)

        Returns:
            Product instance
        """
        product = Product(
            name=data['name'],
            description=data.get('description'),
            price=data['price'],
            stock=data.get('stock', 0),
            category_id=data.get('category_id'),
        )
        db.session.add(product)
        db.session.commit()
        return product

    @staticmethod
    def update(product, data):
        """
        Update an existing product with provided fields.

        Args:
            product (Product): The product instance to update
            data (dict): Fields to update (only non-None values will be applied)

        Returns:
            Product instance
        """
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = data['price']
        if 'stock' in data:
            product.stock = data['stock']
        if 'category_id' in data:
            product.category_id = data['category_id']

        db.session.commit()
        return product

    @staticmethod
    def soft_delete(product):
        """Soft-delete a product by setting is_active to False."""
        product.is_active = False
        db.session.commit()

    @staticmethod
    def has_active_orders(product_id, active_statuses):
        """
        Check if a product has any active orders.

        Args:
            product_id (int): The product ID to check
            active_statuses (tuple): Statuses considered 'active'

        Returns:
            bool
        """
        exists = db.session.query(OrderItem).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            OrderItem.product_id == product_id,
            Order.is_active == True,
            Order.status.in_(active_statuses),
        ).first()

        return exists is not None
