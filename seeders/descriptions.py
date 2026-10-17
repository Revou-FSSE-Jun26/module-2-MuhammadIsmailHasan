"""Generator deskripsi produk per kategori."""

import re

OPENINGS = {
    "Electronics": (
        "{name} tersedia dengan harga {price}.",
        "Jual {name} unit baru bersegel.",
        "{name} ready stock, siap kirim hari ini.",
        "{name} dengan harga {price}, bergaransi resmi.",
    ),
    "Clothing": (
        "{name} dengan bahan yang nyaman dipakai sehari-hari.",
        "{name} tersedia dengan harga {price}.",
        "{name} dengan potongan yang pas dan jahitan rapi.",
        "Koleksi {name}, cocok untuk pemakaian harian maupun acara santai.",
    ),
    "Food & Beverages": (
        "{name} dibuat dari bahan pilihan.",
        "{name} tersedia dengan harga {price}.",
        "{name}, diproduksi segar setiap hari.",
        "{name} dengan rasa yang pas, bukan terlalu manis.",
    ),
    "Books": (
        "{name} kondisi baru dan masih tersegel.",
        "{name} tersedia dengan harga {price}.",
        "Buku {name}, cetakan terbaru dari penerbit.",
        "{name}, tersedia stok terbatas.",
    ),
}

DETAILS = {
    "Electronics": (
        "Produk original dan sudah melewati pengecekan kualitas sebelum dikirim.",
        "Unit dites menyala lebih dulu, kelengkapan dus sesuai standar pabrik.",
        "Bergaransi resmi distributor, bebas tukar bila unit cacat dari pabrik.",
    ),
    "Clothing": (
        "Bahan tidak mudah melar dan warnanya tidak cepat pudar.",
        "Tersedia beberapa ukuran, mohon cek tabel ukuran sebelum membeli.",
        "Sablon dan jahitan dicek satu per satu sebelum dikemas.",
    ),
    "Food & Beverages": (
        "Dikemas higienis tanpa pengawet berlebih.",
        "Simpan di tempat kering dan sejuk, jauhkan dari sinar matahari langsung.",
        "Tanggal kedaluwarsa tercantum pada kemasan, selalu dikirim yang terbaru.",
    ),
    "Books": (
        "Buku original dari penerbit, bukan hasil fotokopi.",
        "Halaman lengkap dan tidak ada cacat cetak.",
        "Cocok untuk koleksi pribadi maupun bahan referensi belajar.",
    ),
}

CLOSINGS = {
    "Electronics": (
        "Dikemas bubble wrap berlapis agar aman sampai tujuan.",
        "Pengiriman memakai kardus tambahan untuk barang elektronik.",
        "Silakan chat penjual lebih dulu untuk memastikan ketersediaan warna.",
    ),
    "Clothing": (
        "Disarankan dicuci dengan air dingin dan jangan memakai pemutih.",
        "Dikemas rapi dalam plastik kedap agar tidak kotor di perjalanan.",
        "Bisa tukar ukuran selama label belum dilepas.",
    ),
    "Food & Beverages": (
        "Dikirim dengan kemasan aman agar tidak rusak di perjalanan.",
        "Untuk pengiriman luar kota disarankan memilih kurir instan.",
        "Sebaiknya segera dikonsumsi setelah kemasan dibuka.",
    ),
    "Books": (
        "Dikemas dengan plastik pelindung agar tidak lecet saat pengiriman.",
        "Pengiriman setiap hari kerja sebelum pukul 15.00.",
        "Tersedia juga untuk pembelian dalam jumlah banyak.",
    ),
}

ATTRIBUTE_PATTERNS = (
    (re.compile(r"(\d{2,3})\s*(?:inch|inc|in\b|\")", re.I), "Ukuran {0} inch."),
    (re.compile(r"(\d+)\s*/\s*(\d+)\s*gb", re.I), "Kapasitas RAM {0}GB dan memori {1}GB."),
    (re.compile(r"(\d+)\s*tb\b", re.I), "Kapasitas penyimpanan {0}TB."),
    (re.compile(r"(\d+)\s*gb\b", re.I), "Kapasitas {0}GB."),
    (re.compile(r"(\d+)\s*(?:kg|kilo)\b", re.I), "Berat bersih {0} kg."),
    (re.compile(r"(\d+)\s*(?:gr|gram|g)\b", re.I), "Berat bersih {0} gram."),
    (re.compile(r"(\d+)\s*(?:ml|mililiter)\b", re.I), "Isi {0} ml per kemasan."),
    (re.compile(r"(\d+)\s*(?:liter|ltr|l)\b", re.I), "Isi {0} liter per kemasan."),
    (re.compile(r"(\d+)\s*(?:pcs|pc|pack|pak|box|dus)\b", re.I), "Isi {0} pcs per paket."),
    (re.compile(r"\b(?:size\s*)?(s|m|l|xl|xxl|xxxl)\b", re.I), "Tersedia ukuran {0}."),
    (re.compile(r"(\d{3,4})\s*halaman", re.I), "Terdiri dari {0} halaman."),
)


def format_rupiah(price):
    return "Rp" + f"{int(price):,}".replace(",", ".")


def extract_attribute(name):
    for pattern, template in ATTRIBUTE_PATTERNS:
        match = pattern.search(name)
        if match:
            groups = [g.upper() if g.isalpha() else g for g in match.groups()]
            return template.format(*groups)
    return None


def shorten(name, limit=120):
    if len(name) <= limit:
        return name
    return name[: limit - 3].rstrip(" -,/") + "..."


def build_description(product, category, rng):
    openings = OPENINGS.get(category, OPENINGS["Electronics"])
    details = DETAILS.get(category, DETAILS["Electronics"])
    closings = CLOSINGS.get(category, CLOSINGS["Electronics"])

    parts = [
        rng.choice(openings).format(
            name=shorten(product["name"]), price=format_rupiah(product["price"])
        )
    ]

    attribute = extract_attribute(product["name"])
    if attribute:
        parts.append(attribute)

    parts.append(rng.choice(details))
    parts.append(rng.choice(closings))

    return " ".join(parts)[:1000]
