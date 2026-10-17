"""Peta category -> sub_category -> path listing, dan sumber gambar katalog."""

CATEGORIES = ("Electronics", "Clothing", "Food & Beverages", "Books", "Sports")

EMPTY_CATEGORIES = ("Sports",)

CATALOG = (
    ("Electronics", "Television", "elektronik/tv-aksesoris/televisi", "television"),
    ("Electronics", "iPhone", "handphone-tablet/handphone/ios", "iphone"),
    ("Electronics", "Android Phone", "handphone-tablet/handphone/android-os", "android-phone"),
    ("Clothing", "Men", "fashion-pria/atasan-pria", "men"),
    ("Clothing", "Women", "fashion-wanita/atasan-wanita", "women"),
    ("Food & Beverages", "Cakes", "makanan-minuman/kue", "cakes"),
    ("Food & Beverages", "Instant Food", "makanan-minuman/makanan-jadi", "instant-food"),
    ("Food & Beverages", "Drink", "makanan-minuman/minuman", "drink"),
    ("Books", "Law", "buku/buku-hukum", "law"),
    ("Books", "Self Improvement", "buku/buku-pengembangan-diri-karir", "self-improvement"),
    ("Books", "Economy and Business", "buku/buku-ekonomi-bisnis", "economy-and-business"),
)

PRODUCT_PREFIX = "products"
CATEGORY_PREFIX = "categories"
SUB_CATEGORY_PREFIX = "sub-categories"

_UNSPLASH = "https://images.unsplash.com/{photo}?w=600&h=600&fit=crop&crop=center&q=80"

CATEGORY_IMAGE_SOURCES = {
    "electronics": _UNSPLASH.format(photo="photo-1498049794561-7780e7231661"),
    "clothing": _UNSPLASH.format(photo="photo-1483985988355-763728e1935b"),
    "food-beverages": _UNSPLASH.format(photo="photo-1509440159596-0249088772ff"),
    "books": _UNSPLASH.format(photo="photo-1544947950-fa07a98d237f"),
    "sports": _UNSPLASH.format(photo="photo-1461896836934-ffe607ba8211"),
}

SUB_CATEGORY_IMAGE_SOURCES = {
    "television": _UNSPLASH.format(photo="photo-1593359677879-a4bb92f829d1"),
    "iphone": _UNSPLASH.format(photo="photo-1592750475338-74b7b21085ab"),
    "android-phone": _UNSPLASH.format(photo="photo-1511707171634-5f897ff02aa9"),
    "men": _UNSPLASH.format(photo="photo-1516257984-b1b4d707412e"),
    "women": _UNSPLASH.format(photo="photo-1485968579580-b6d095142e6e"),
    "cakes": _UNSPLASH.format(photo="photo-1578985545062-69928b1d9587"),
    "instant-food": _UNSPLASH.format(photo="photo-1612929633738-8fe44f7ec841"),
    "drink": _UNSPLASH.format(photo="photo-1544145945-f90425340c7e"),
    "law": _UNSPLASH.format(photo="photo-1589829085413-56de8ae18c73"),
    "self-improvement": _UNSPLASH.format(photo="photo-1455390582262-044cdead277a"),
    "economy-and-business": _UNSPLASH.format(photo="photo-1507679799987-c73779587ccf"),
}


def category_image_key(slug):
    return f"{CATEGORY_PREFIX}/{slug}.jpg" if slug in CATEGORY_IMAGE_SOURCES else None


def sub_category_image_key(slug):
    return f"{SUB_CATEGORY_PREFIX}/{slug}.jpg" if slug in SUB_CATEGORY_IMAGE_SOURCES else None
