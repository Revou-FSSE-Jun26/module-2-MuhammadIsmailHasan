from models import Category


def validation_category_data(data, required_all=True):
    name = data.get('name')

    if required_all and name is None:
        return "name is required", 400
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            return "name cannot be empty", 400
        if len(name) > 255:
            return "name cannot exceed 255 characters", 422

    return None, None


def validation_products_data(data, required_all=True):
    name = data.get('name')
    price = data.get('price')
    stock = data.get('stock')
    description = data.get('description')
    category_id = data.get('category_id')
    
    if required_all and name is None:
        return "name is required", 400
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            return "name cannot be empty", 400
        if len(name) > 255:
            return "name cannot exceed 255 characters", 422
    
    if required_all and price is None:
        return "price is required", 400
    if price is not None:
        if not isinstance(price, (int, float)) or isinstance(price, bool):
            return "price must be a number", 400
        if price > 10**11:
            return "price cannot exceed 11 digits number", 422
        if price < 0:
            return "price must be greater than 0", 422
        
    if required_all and stock is None:
        return "stock is required", 400
    if stock is not None:
        if not isinstance(stock, int) or isinstance(stock, bool):
            return "stock must be number", 400
    
    if description is not None:
        if len(description) > 1000:
            return "description cannot exceed 1000 characters", 422
    
    if category_id is not None:
        if not isinstance(category_id, int) or isinstance(category_id, bool):
            return "category_id must be a number", 400
        category = Category.query.filter_by(id=category_id, is_active=True).first()
        if category is None:
            return "category id not found", 404
        
    return None, None
    