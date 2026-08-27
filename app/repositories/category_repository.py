from app.models.categories import Category
from app.extensions import db


class CategoryRepository:

    @staticmethod
    def get_all(filters=None, sort_by='id', order='asc', page=1, limit=10):
        query = Category.query.filter_by(is_active=True)

        if filters:
            if filters.get('name'):
                query = query.filter(Category.name.ilike(f"%{filters['name']}%"))

        sort_columns = {
            'id': Category.id,
            'name': Category.name,
            'created_at': Category.created_at,
        }
        sort_column = sort_columns.get(sort_by, Category.id)

        if order == 'desc':
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        return query.paginate(page=page, per_page=limit, error_out=False)

    @staticmethod
    def get_by_id(category_id):
        return Category.query.filter_by(id=category_id, is_active=True).first()

    @staticmethod
    def find_by_name(name, exclude_id=None):
        query = Category.query.filter_by(name=name, is_active=True)
        if exclude_id is not None:
            query = query.filter(Category.id != exclude_id)
        return query.first()

    @staticmethod
    def create(data):
        category = Category(name=data['name'])
        db.session.add(category)
        db.session.commit()
        return category

    @staticmethod
    def update(category, data):
        if 'name' in data:
            category.name = data['name']

        db.session.commit()
        return category

    @staticmethod
    def soft_delete(category):
        category.is_active = False
        db.session.commit()
