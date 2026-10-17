"""Download gambar category dan sub-category: python -m seeders.scraper.catalog_images."""

import argparse
import os
import urllib.error
import urllib.request

from seeders.scraper.catalog import (
    CATEGORY_IMAGE_SOURCES,
    CATEGORY_PREFIX,
    SUB_CATEGORY_IMAGE_SOURCES,
    SUB_CATEGORY_PREFIX,
)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMAGE_ROOT = os.path.join(PROJECT_ROOT, "app", "static", "images")

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def download(url, destination, force=False):
    if not force and os.path.exists(destination) and os.path.getsize(destination) > 0:
        return "skip"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as error:
        print(f"    gagal {os.path.basename(destination)}: {error}")
        return "fail"
    if not data:
        return "fail"
    with open(destination, "wb") as handle:
        handle.write(data)
    return "ok"


def download_group(sources, prefix, force):
    directory = os.path.join(IMAGE_ROOT, prefix)
    os.makedirs(directory, exist_ok=True)

    counts = {"ok": 0, "skip": 0, "fail": 0}
    for slug, url in sources.items():
        filename = f"{slug}.jpg"
        result = download(url, os.path.join(directory, filename), force)
        counts[result] += 1
        size = os.path.join(directory, filename)
        size = os.path.getsize(size) if os.path.exists(size) else 0
        print(f"    {result:4}  {prefix}/{filename:28} {size // 1024} KB")
    return counts


def main():
    parser = argparse.ArgumentParser(description="Download gambar category/sub-category")
    parser.add_argument("--force", action="store_true", help="download ulang walau file sudah ada")
    args = parser.parse_args()

    total = {"ok": 0, "skip": 0, "fail": 0}
    for sources, prefix in (
        (CATEGORY_IMAGE_SOURCES, CATEGORY_PREFIX),
        (SUB_CATEGORY_IMAGE_SOURCES, SUB_CATEGORY_PREFIX),
    ):
        print(f"\n[{prefix}] {len(sources)} gambar")
        counts = download_group(sources, prefix, args.force)
        for key in total:
            total[key] += counts[key]

    print(f"\nSelesai. {total['ok']} baru, {total['skip']} dilewati, {total['fail']} gagal.")


if __name__ == "__main__":
    main()
