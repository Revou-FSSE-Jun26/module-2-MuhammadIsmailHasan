"""Crawler listing produk Tokopedia -> JSON di seeders/data/.

Lihat seeders/README.md untuk opsi dan format datanya.
"""

import argparse
import gzip
import json
import os
import random
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from seeders.scraper.catalog import CATALOG, PRODUCT_PREFIX

BASE_URL = "https://www.tokopedia.com/p/{path}?page={page}"
PRODUCTS_PER_PAGE = 60
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, "seeders", "data")
IMAGE_DIR = os.path.join(PROJECT_ROOT, "app", "static", "images", PRODUCT_PREFIX)

PRODUCT_KEY_RE = re.compile(r'"(AceSearchProduct\d+)":\s*\{')


def fetch(url, retries=3):
    for attempt in range(1, retries + 1):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                raw = response.read()
                if response.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return raw.decode("utf-8", errors="replace")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as error:
            if attempt == retries:
                print(f"    gagal fetch {url}: {error}")
                return None
            time.sleep(2 * attempt)
    return None


def extract_json_object(html, start):
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(html)):
        char = html[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return html[start : index + 1]
    return None


def parse_products(html):
    products = []
    for match in PRODUCT_KEY_RE.finditer(html):
        brace = html.index("{", match.end() - 1)
        blob = extract_json_object(html, brace)
        if not blob:
            continue
        try:
            raw = json.loads(blob)
        except json.JSONDecodeError:
            continue

        name = (raw.get("name") or "").strip()
        price = raw.get("price_int")
        if not name or not price:
            continue

        products.append(
            {
                "source_id": str(raw.get("id")),
                "name": name,
                "price": int(price),
                "_signed_urls": [
                    url
                    for url in (raw.get("image_url_700"), raw.get("image_url"))
                    if url
                ],
            }
        )
    return products


def crawl_sub_category(path, target, delay):
    collected = {}
    max_pages = max(1, -(-target // PRODUCTS_PER_PAGE) + 2)

    for page in range(1, max_pages + 1):
        html = fetch(BASE_URL.format(path=path, page=page))
        if not html:
            break

        found = parse_products(html)
        if not found:
            print(f"    halaman {page}: 0 produk, berhenti")
            break

        before = len(collected)
        for product in found:
            collected.setdefault(product["source_id"], product)
        print(
            f"    halaman {page}: +{len(collected) - before} baru "
            f"(total {len(collected)})"
        )

        if len(collected) >= target:
            break
        time.sleep(delay)

    return list(collected.values())[:target]


def download_image(url, destination):
    if os.path.exists(destination) and os.path.getsize(destination) > 0:
        return True
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read()
        if not data:
            return False
        with open(destination, "wb") as handle:
            handle.write(data)
        return True
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return False


def download_images(products, mode, workers=8):
    if mode == "none":
        for product in products:
            product["images"] = list(product["_signed_urls"])
        return 0

    os.makedirs(IMAGE_DIR, exist_ok=True)
    jobs = []
    for product in products:
        urls = product["_signed_urls"]
        if mode == "thumb":
            urls = urls[-1:]
        product["images"] = []
        for order, url in enumerate(urls):
            filename = f"{product['source_id']}-{order}.jpg"
            jobs.append((url, os.path.join(IMAGE_DIR, filename), product, filename))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda job: download_image(job[0], job[1]), jobs))

    saved = 0
    for (url, _destination, product, filename), ok in zip(jobs, results):
        if ok:
            product["images"].append(f"{PRODUCT_PREFIX}/{filename}")
            saved += 1
        else:
            product["images"].append(url)
    return saved


def main():
    parser = argparse.ArgumentParser(description="Crawl produk Tokopedia untuk seeder")
    parser.add_argument("--target", type=int, default=200, help="produk per sub-category")
    parser.add_argument("--delay", type=float, default=1.5, help="jeda antar halaman (detik)")
    parser.add_argument("--only", nargs="*", default=None, help="nama file json yang dicrawl saja")
    parser.add_argument(
        "--images",
        choices=("both", "thumb", "none"),
        default="both",
        help="gambar yang didownload ke app/static/products",
    )
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)
    random.seed(20261016)

    total = 0
    for category, sub_category, path, filename in CATALOG:
        if args.only and filename not in args.only:
            continue

        print(f"\n[{category} / {sub_category}] {path}")
        products = crawl_sub_category(path, args.target, args.delay)
        if not products:
            print("    tidak ada produk, dilewati")
            continue

        saved = download_images(products, args.images)
        if args.images != "none":
            print(f"    gambar tersimpan: {saved}")

        for product in products:
            product.pop("_signed_urls", None)

        payload = {
            "category": category,
            "sub_category": sub_category,
            "source": f"https://www.tokopedia.com/p/{path}",
            "crawled_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "count": len(products),
            "products": products,
        }
        output = os.path.join(DATA_DIR, f"{filename}.json")
        with open(output, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=1)

        total += len(products)
        print(f"    tersimpan {len(products)} produk -> seeders/data/{filename}.json")

    print(f"\nSelesai. Total {total} produk.")


if __name__ == "__main__":
    main()
