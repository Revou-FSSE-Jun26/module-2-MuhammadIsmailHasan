from flask import jsonify


def make_response(message, data=None, status_code=200, status=True, **extra):
    payload = {'status': status, 'message': message}
    if data is not None:
        payload['data'] = data
    payload.update(extra)
    return jsonify(payload), status_code


def paginate_meta(paginated):
    return {
        'page': paginated.page,
        'limit': paginated.per_page,
        'total_items': paginated.total,
        'total_pages': paginated.pages,
    }
