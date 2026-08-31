import pytest

from app.utils.slug import slugify


@pytest.mark.parametrize('name,expected', [
    ('Laptop Pro 15"', 'laptop-pro-15'),
    ('  Wireless   Mouse  ', 'wireless-mouse'),
    ('T-Shirt', 't-shirt'),
    ('USB-C Cable', 'usb-c-cable'),
    ('Café Latté', 'cafe-latte'),
    ('!!!', 'product'),
    ('', 'product'),
    (None, 'product'),
    ('Green Tea 50%', 'green-tea-50'),
])
def test_slugify(name, expected):
    assert slugify(name) == expected
