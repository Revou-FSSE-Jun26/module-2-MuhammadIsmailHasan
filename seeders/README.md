# Seeders

Populates the database with test data. Product data lives as JSON under
`seeders/data/`, so **the seeder itself never touches the network** — crawling
is a separate step you run once.

```
seeders/
  scraper/
    catalog.py          # category/sub_category map + catalog image sources
    tokopedia.py        # crawler: listing pages -> seeders/data/*.json + images
    catalog_images.py   # downloads the category / sub-category images
  data/                 # crawl output (JSON is committed, images are not)
  scraped.py            # JSON -> insert-ready rows (slug, stock, gallery)
  descriptions.py       # per-category product description generator
  review.py             # HTML review page built from the database
  seeders.py            # main seeder
```

Images are kept apart by kind, and the same layout is mirrored in object
storage so `aws s3 sync` maps one to one:

```
app/static/images/        <- gitignored
  products/               4400 files, ~149MB
  categories/             5 files
  sub-categories/         11 files
```

What the database stores is the key only — `products/103628491497-0.jpg`,
`categories/books.jpg`, `sub-categories/women.jpg` — joined to
`IMAGE_BASE_URL` at seed time.

## 1. Crawl products (one-off)

```bash
python -m seeders.scraper.tokopedia                      # 200 products/sub-category
python -m seeders.scraper.tokopedia --target 100         # fewer
python -m seeders.scraper.tokopedia --only law drink     # selected sub-categories
python -m seeders.scraper.tokopedia --images thumb       # 200px thumbnails only
python -m seeders.scraper.tokopedia --images none        # skip image download

python -m seeders.scraper.catalog_images                 # category + sub-category images
python -m seeders.scraper.catalog_images --force         # re-download existing ones
```

This writes one JSON file per sub-category into `seeders/data/` (~0.46MB total).
Those files are committed so seeding can be repeated without crawling again.
Each record holds only the four fields the seeder actually reads — a name, a
price, and image **filenames**:

```json
{
 "source_id": "102456536454",
 "name": "Buku Himpunan Peraturan dan Undang Undang Tentang Agraria ...",
 "price": 223250,
 "images": ["102456536454-0.jpg", "102456536454-1.jpg"]
}
```

`source_id` is kept because the image filenames are derived from it. Other
fields the listing pages expose (ratings, review counts, per-product URLs) are
deliberately not stored.

### IMAGE_BASE_URL

The JSON stores filenames, not full URLs. The prefix is decided at seed time
through the `IMAGE_BASE_URL` environment variable, so the same dataset works
across environments **without re-crawling and without a database migration**:

```bash
IMAGE_BASE_URL=/static/images                            # local (default)
IMAGE_BASE_URL=https://BUCKET.s3.REGION.amazonaws.com    # S3
IMAGE_BASE_URL=https://images.yourdomain.com             # CDN later
```

`IMAGE_BASE_URL` is the root the three key prefixes hang off, so one variable
covers product, category and sub-category images at once.

Seeding a hosted database with images served from S3:

```bash
DATABASE_URL="postgresql://...@...supabase.com:5432/postgres" \
IMAGE_BASE_URL="https://BUCKET.s3.ap-southeast-3.amazonaws.com" \
python -m seeders.seeders
```

Note on Supabase: use port **5432** (session mode) for the seeder, not 6543
(transaction pooler) — pgbouncer in transaction mode tends to clash with
SQLAlchemy prepared statements during bulk inserts. The application itself can
use 6543.

### Why images are downloaded

The image URLs returned by the listing pages are signed and **expire after
about an hour** (`x-expires`); stripping the signature returns 403. The crawler
therefore downloads the files into `app/static/images/products/` (gitignored, ~149MB
for 2200 products with `--images both`) and the database only ever stores a
filename joined to `IMAGE_BASE_URL`. With `--images none` the original signed
URLs are stored instead, and those images will break once the signature
expires.

## 2. Run the seeder

```bash
# Option 1: module execution
python -m seeders.seeders

# Option 2: direct import
python -c "from seeders.seeders import seed_test_data; seed_test_data()"

# Option 3: from the project root
python -c "from seeders import seed_test_data; seed_test_data()"
```

## What gets seeded

### Users (5)
- john_doe (admin)
- jane_smith (buyer)
- bob_wilson (buyer)
- alice_brown (seller)
- charlie_davis (seller)

### Categories (5) and Sub Categories (11)

| Category | Sub categories |
| --- | --- |
| Electronics | Television, iPhone, Android Phone |
| Clothing | Men, Women |
| Food & Beverages | Cakes, Instant Food, Drink |
| Books | Law, Self Improvement, Economy and Business |
| Sports | *(deliberately left empty: no sub-categories, no products)* |

`Sports` stays empty on purpose, as an empty-state test case.

Category and sub-category images are Unsplash photos, downloaded by
`python -m seeders.scraper.catalog_images` into `app/static/images/` and served
from your own storage like everything else. The Unsplash URLs they came from
stay in `scraper/catalog.py` as the source of truth, so re-downloading or
swapping a photo is a one-line change there.

### Products

Up to 200 products per sub-category (~2200 total). Names and prices are real;
everything else is generated:

- **slug** — product name plus source id, to guarantee uniqueness
- **description** — 3–4 sentences from `descriptions.py`: opening, body and
  closing lines that differ per category, plus one attribute sentence derived
  from the product name (screen size in inches, GB/TB capacity, piece count,
  weight in grams). All 2200 descriptions are distinct
- **stock** — randomised with a fixed seed: about 6% at **stock 0** (sold out)
  and 6% at **stock 1** (last item), the rest between 2 and 500
- **seller_id** — spread across users with the `seller` role

### Product Images

**3–5 images per product** (~8775 rows). `order` 0 is always the product's own
photo; the rest is a **synthetic gallery** borrowed from other products in the
same sub-category, using a fixed offset so the result is deterministic and a
product never borrows its own photo.

Why synthetic: the listing pages only expose one photo per product (in two
sizes rendered from the same file), and the real galleries are only available
through an API that rejects non-browser clients. Crawling product detail pages
does not help either — their `og:image` is the exact same photo. So the extra
gallery images are dummy data, there to let the frontend gallery component be
tested against a realistic number of images.

Tune the count with `GALLERY_MIN` / `GALLERY_MAX` in `seeders/scraped.py`.

### Orders (7), Carts, Profiles, Addresses

Orders are created across every status (`waiting_for_payment`, `paid`,
`processing`, `shipped`, `delivered`, `returned`, `cancelled`) using products
that still have enough stock.

## Reviewing the seeded data

```bash
python -m seeders.review
```

Generates `app/static/images/review.html` (gitignored) showing each product's
gallery, price, stock and description — a quick way to judge whether the data is
good enough without running a frontend. Open
`http://localhost:5000/static/images/review.html`.

## Functions

| Function | Description |
| --- | --- |
| `seed_test_data()` | Runs every seeder in order |
| `clear_tables()` | Deletes all rows from the tables |
| `seed_categories()` | Categories, from `scraper/catalog.py` |
| `seed_sub_categories()` | Sub categories, from `scraper/catalog.py` |
| `seed_users()` | Users with bcrypt-hashed passwords |
| `seed_products()` | Products from `seeders/data/`, returns rows with ids |
| `seed_product_images()` | Product images, from the `seed_products()` return value |
| `resolve_image_url()` | `scraped.py` — filename + `IMAGE_BASE_URL` -> full URL |
| `generate()` | `review.py` — HTML review page from the database |
| `category_image_key()` | `catalog.py` — slug -> `categories/<slug>.jpg` |
| `sub_category_image_key()` | `catalog.py` — slug -> `sub-categories/<slug>.jpg` |

## Notes

- All user passwords are hashed with bcrypt
- Auto-increment ids come from the database
- Products and product images are inserted via `bulk_insert_mappings`
- Stock and seller assignment use `random.Random(20261016)`, so repeated runs
  produce identical data
- If `seeders/data/` is empty, `seed_products()` stops with a message telling
  you to run the crawler first
- `GET /api/v1/products/` issues one `product_images` query per product (N+1).
  With 3–5 images per product this is the obvious first candidate for Redis
  caching
- The list endpoint needs its trailing slash — `/api/v1/products` returns a 308
  redirect

## Data provenance and acceptable use

Product names and prices in this dataset were collected from public marketplace
category listing pages in October 2026. No seller account data, buyer data,
contact details, or any other personal information was collected or stored.

Category and sub-category images are separate: they come from Unsplash and are
covered by the Unsplash License, which permits free use including commercial
use without attribution. The restrictions below apply to the product
photographs only.

### What is real and what is generated

Most of this dataset is **not** real:

| Field | Origin |
| --- | --- |
| `name`, `price` | Real, from the public listing |
| `product_images[0]` | Real product photo, downloaded at crawl time |
| `product_images[1..n]` | **Generated.** Borrowed from other products in the same sub-category so the gallery component has a realistic image count |
| `description` | **Generated** by `seeders/descriptions.py` from the product name. Not written by any seller |
| `stock`, `seller_id` | **Generated** with a fixed random seed |
| category / sub-category images | Unsplash stock photos, not related to the products |
| users, orders, carts, addresses | **Entirely fictional** |

Nothing here should be treated as an accurate reflection of any real product,
price, seller, or shop.

### Intended use and limitations

This dataset exists to populate a **learning project** with enough realistic
volume to practise pagination, caching and query tuning. It is not intended for
commercial use, price comparison, market research, resale, or redistribution as
a dataset.

Two limits are worth stating plainly:

1. **Automated collection is against the source marketplace's Terms of
   Service.** The crawler under `seeders/scraper/` is published as a reference
   implementation, not as an invitation to re-run it at scale. Reusing it is
   your own decision and your own responsibility.
2. **Product photographs remain the property of their respective sellers or of
   the marketplace.** No copyright in those images is claimed here, and no
   licence to them is granted by this repository. That is also why the images
   are **not committed** — `.gitignore` excludes `app/static/images/`, and
   only filenames are stored in the JSON.

If you are a rights holder and want material relating to your products removed
from this repository, please open an issue and it will be taken down.

### If you deploy this publicly

Serving these photographs from a public bucket or CDN means republishing someone
else's copyrighted images. For a local or private development environment that
is a low-exposure choice; for anything public-facing, prefer replacing them with
placeholders or your own photography. Access control such as signed URLs
restricts *who can fetch* an image — it does not change *who owns* it.
