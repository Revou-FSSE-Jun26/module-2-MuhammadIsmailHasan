# Tests

Automated test suite untuk testing API endpoints.

## Usage

### Jalankan test
```bash
# Cara 1: Direct python
python tests/test_endpoints.py

# Cara 2: Module execution
python -m tests.test_endpoints
```

## Requirements

Sebelum menjalankan tests, pastikan:
1. Flask app sudah running: `python app.py`
2. Database sudah di-seed: `python -m seeders.seeders`
3. Requests library terinstall: `pip install requests`

## Test Coverage

### Users Endpoint (5 tests)
- ✅ Register new user
- ✅ Register duplicate user (should fail)
- ✅ Register with missing field (should fail)
- ✅ Get user by ID
- ✅ Get non-existent user (should return 404)

### Products Endpoint (7 tests)
- ✅ Get all products
- ✅ Get single product
- ✅ Create product
- ✅ Create product with invalid price (should fail)
- ✅ Update product
- ✅ Delete product
- ✅ Delete non-existent product (should return 404)

### Performance Tests (1 test)
- ✅ Measure response time for get all products

## Output Example

Tests akan menampilkan colored output:
- 🟢 Green: Success
- 🔴 Red: Error
- 🟡 Yellow: Info
- 🔵 Blue: Section headers

## Troubleshooting

### Connection refused
Flask app tidak running. Jalankan:
```bash
python app.py
```

### ModuleNotFoundError
Pastikan Anda di project root directory:
```bash
cd /Users/ismail/Documents/LEARNING/Bootcamp/module-2-MuhammadIsmailHasan
```

### Assertion errors
Database mungkin tidak ter-seed dengan proper data. Re-seed:
```bash
python -m seeders.seeders
```
