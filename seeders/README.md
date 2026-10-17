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
`IMAGE_BASE_URL` by the API when it builds a response.

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

Neither the JSON nor the database stores a full URL. Both store a **key**:

```
products/103628491497-0.jpg
categories/books.jpg
sub-categories/women.jpg
```

The API joins that key to `IMAGE_BASE_URL` when it serializes a response, so
changing where images are served from is an environment variable and a restart
— no re-crawl, no re-seed, no database update:

```bash
IMAGE_BASE_URL=/static/images                            # local (default)
IMAGE_BASE_URL=https://BUCKET.s3.REGION.amazonaws.com    # S3
IMAGE_BASE_URL=https://images.yourdomain.com             # CDN later
```

One variable covers product, category and sub-category images at once, because
all three keys hang off the same root.

Where it is applied: `build_image_url()` in `app/utils/images.py`, used by
`ImageUrlField` (`app/schemas/fields.py`) in the response schemas and by the
models' `to_dict()`. Values that are already absolute are passed through
unchanged, so rows written before this change keep working.

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

## 3. Deploy: images to S3, data to Supabase

Run this from your laptop, not from Render — the images live locally and the
free Render tier has no shell. Steps 1 and 2 are one-off; step 4 is what you
repeat whenever the dataset changes.

### 1. Create the bucket (once)

```bash
BUCKET=revoshop-images
REGION=ap-southeast-1

aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
  --create-bucket-configuration LocationConstraint="$REGION"

aws s3api put-public-access-block --bucket "$BUCKET" \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=false,RestrictPublicBuckets=false"

aws s3api put-bucket-policy --bucket "$BUCKET" --policy '{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadCatalogImages",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": [
      "arn:aws:s3:::revoshop-images/products/*",
      "arn:aws:s3:::revoshop-images/categories/*",
      "arn:aws:s3:::revoshop-images/sub-categories/*"
    ]
  }]
}'
```

ACLs are disabled on new buckets, so `--acl public-read` would fail; a bucket
policy is the supported way. Scoping `Resource` to the three prefixes keeps
anything else you later store in this bucket private.

### 2. Upload the images

```bash
aws configure set default.s3.max_concurrent_requests 32

aws s3 sync app/static/images/ s3://revoshop-images/ \
  --exclude "review.html" --exclude "*.DS_Store" --exclude "Thumbs.db" \
  --cache-control "public, max-age=31536000, immutable"
```

The local folder layout mirrors the bucket, so one `sync` covers products,
categories and sub-categories. It is restartable: re-running only uploads what
is missing. The excludes matter: `sync` copies every file it finds, and macOS
drops a `.DS_Store` into any folder you open in Finder. Verify one object:

```bash
curl -sI https://revoshop-images.s3.ap-southeast-1.amazonaws.com/categories/books.jpg | head -3
```

### 3. Bring the Supabase schema up to date

```bash
export SUPABASE_URL="postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres"

DATABASE_URL="$SUPABASE_URL" FLASK_APP=run.py python -m flask db current
DATABASE_URL="$SUPABASE_URL" FLASK_APP=run.py python -m flask db upgrade
```

**Use the Session pooler host, not the direct one.** `db.<ref>.supabase.co`
resolves to an IPv6 address only, so on an IPv4-only network it fails with
`could not translate host name`. The pooler host has IPv4. Note the username
becomes `postgres.<project-ref>`.

Port **5432** (session mode) is required here and in the next step: the
transaction pooler on 6543 clashes with SQLAlchemy prepared statements during
bulk inserts. Your deployed app should still use 6543.

### 4. Seed

```bash
DATABASE_URL="$SUPABASE_URL" python -m seeders.seeders
```

The seeder does not need `IMAGE_BASE_URL` — it writes keys. The base URL is
applied by the API at response time, so it belongs on the host (step 5).

`seed_test_data()` calls `clear_tables()` first, so **everything already in
that database is deleted**, including users and orders created through the API.

Check the result:

```bash
DATABASE_URL="$SUPABASE_URL" python -c "
from app import create_app; from app.extensions import db; from sqlalchemy import text
a=create_app(); a.config['SQLALCHEMY_ECHO']=False
with a.app_context():
    q=lambda s: db.session.execute(text(s)).scalar()
    print('products  :', q('select count(*) from products'))
    print('images    :', q('select count(*) from product_images'))
    print('bad keys  :', q(\"select count(*) from product_images where url not like 'products/%'\"))
    print('sample    :', q('select url from product_images limit 1'))
"
```

Expect 2200 products, 8775 images, 0 bad keys, and a sample like
`products/103628491497-0.jpg`.

### 5. Deploy the code

```bash
git push
```

Then set one environment variable on the host, or every image URL it returns
will point at the API's own domain and 404:

```
IMAGE_BASE_URL = https://revoshop-images.s3.ap-southeast-1.amazonaws.com
```

On Render that is Dashboard → your service → Environment → Add Environment
Variable, which triggers a restart. The API only ever returns URLs; browsers
fetch the images straight from S3 without the API being involved.

One thing to set up though: this project has no `render.yaml`, and `Procfile`
only starts gunicorn, so **deploys do not run migrations**. Either put
`flask db upgrade` in the host's pre-deploy command, or keep running step 3 by
hand after every new migration.

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
| `build_image_url()` | `app/utils/images.py` — key + `IMAGE_BASE_URL` -> full URL |
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
- `GET /api/v1/products/` still issues one `product_images` query per product
  (N+1) because each row resolves its primary image. At `limit=10` that is 12
  queries per page, so it is tolerable — but it is the obvious first candidate
  for Redis caching. The nested category endpoints no longer have this problem:
  they cap the products per group and eager-load the images
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
