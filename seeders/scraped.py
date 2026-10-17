"""Baca hasil crawl di seeders/data/ dan ubah jadi baris siap-insert."""

import json
import os
import random

from seeders.descriptions import build_description
from seeders.scraper.catalog import CATALOG

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

DEFAULT_IMAGE_BASE_URL = "/static/images"

RANDOM_SEED = 20261016

OUT_OF_STOCK_RATIO = 0.06
SINGLE_STOCK_RATIO = 0.06

GALLERY_MIN = 3
GALLERY_MAX = 5


def image_base_url():
    return os.getenv("IMAGE_BASE_URL", DEFAULT_IMAGE_BASE_URL).rstrip("/")


def resolve_image_url(value, base=None):
    if not value:
        return None
    if value.startswith(("http://", "https://", "/")):
        return value
    return f"{base if base is not None else image_base_url()}/{value}"


def available_sub_categories():
    found = []
    for category, sub_category, _path, filename in CATALOG:
        path = os.path.join(DATA_DIR, f"{filename}.json")
        if os.path.exists(path):
            found.append((category, sub_category, path))
    return found


def load_products():
    grouped = {}
    for category, sub_category, path in available_sub_categories():
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
        grouped[sub_category] = {
            "category": category,
            "products": payload.get("products", []),
        }
    return grouped


def primary_image(product):
    images = product.get("images") or []
    return images[0] if images else None


def build_gallery(products, index, rng):
    own = primary_image(products[index])
    if not own:
        return []

    gallery = [own]
    total = len(products)
    wanted = rng.randint(GALLERY_MIN, GALLERY_MAX)

    offset = 1
    while len(gallery) < wanted and offset < total:
        candidate = primary_image(products[(index + offset) % total])
        if candidate and candidate not in gallery:
            gallery.append(candidate)
        offset += 1

    return gallery


def pick_stock(rng):
    roll = rng.random()
    if roll < OUT_OF_STOCK_RATIO:
        return 0
    if roll < OUT_OF_STOCK_RATIO + SINGLE_STOCK_RATIO:
        return 1
    return rng.randint(2, 500)


def make_slug(product, used_slugs):
    from app.utils.slug import slugify

    base = slugify(product["name"])[:280].strip("-") or "product"
    slug = f"{base}-{product['source_id']}"[:300]
    while slug in used_slugs:
        slug = f"{base[:270]}-{product['source_id']}-{len(used_slugs)}"[:300]
    used_slugs.add(slug)
    return slug


def build_rows(grouped, sub_category_ids, seller_ids):
    rng = random.Random(RANDOM_SEED)
    base = image_base_url()
    used_slugs = set()
    rows = []

    for sub_category, payload in grouped.items():
        sub_category_id = sub_category_ids.get(sub_category)
        if sub_category_id is None:
            continue

        category = payload["category"]
        products = payload["products"]

        for index, product in enumerate(products):
            rows.append(
                {
                    "sub_category_id": sub_category_id,
                    "seller_id": rng.choice(seller_ids) if seller_ids else None,
                    "name": product["name"][:255],
                    "slug": make_slug(product, used_slugs),
                    "description": build_description(product, category, rng),
                    "price": product["price"],
                    "stock": pick_stock(rng),
                    "images": [
                        resolve_image_url(name, base)[:500]
                        for name in build_gallery(products, index, rng)
                    ],
                }
            )
    return rows
