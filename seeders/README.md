# Seeders

Package untuk populate test data ke database.

## Usage

### Jalankan seeder
```bash
# Cara 1: Module execution
python -m seeders.seeders

# Cara 2: Direct import
python -c "from seeders.seeders import seed_test_data; seed_test_data()"

# Cara 3: Dari project root
python -c "from seeders import seed_test_data; seed_test_data()"
```

## Data yang di-seed

### Users (5)
- john_doe (admin)
- jane_smith (user)
- bob_wilson (user)
- alice_brown (user)
- charlie_davis (seller)

### Categories (5)
- Electronics
- Clothing
- Food & Beverages
- Books
- Sports

### Products (10)
- 5 Electronics products
- 3 Clothing products
- 2 Food & Beverages products

## Functions

### `seed_test_data()`
Main function yang menjalankan semua seeders

### `clear_tables()`
Hapus semua data dari tables

### `seed_categories()`
Populate categories

### `seed_users()`
Populate users dengan bcrypt hashed passwords

### `seed_products()`
Populate products dengan kategori relationships

## Notes

- Semua user passwords di-hash dengan bcrypt
- Auto-increment ID di-generate oleh database
- Timestamps di-set otomatis dari Python defaults
- Foreign keys dengan CASCADE/SET NULL constraints
