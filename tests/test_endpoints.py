"""
Test script untuk testing products dan users endpoints
Jalankan dengan: python test_endpoints.py
"""

import requests
import json
import time
import os

BASE_URL = os.getenv('FLASK_TEST_URL', 'http://localhost:5000')

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(test_name):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}TEST: {test_name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.YELLOW}→ {message}{Colors.END}")

def print_response(response):
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")


# ==================== USERS ENDPOINT TESTS ====================

def test_register_user():
    """Test registrasi user baru"""
    print_test("Register New User")
    
    payload = {
        'username': 'testuser_new',
        'email': 'testuser@example.com',
        'password': 'testpassword123'
    }
    
    print_info(f"Registering user: {payload['username']}")
    response = requests.post(f'{BASE_URL}/users/register', json=payload)
    print_response(response)
    
    if response.status_code == 201:
        print_success("User registered successfully")
        return response.json()['data']
    else:
        print_error("Failed to register user")
        return None


def test_register_duplicate_user():
    """Test registrasi user dengan username yang sudah ada"""
    print_test("Register Duplicate User")
    
    payload = {
        'username': 'john_doe',
        'email': 'different@example.com',
        'password': 'testpassword123'
    }
    
    print_info(f"Trying to register duplicate username: {payload['username']}")
    response = requests.post(f'{BASE_URL}/users/register', json=payload)
    print_response(response)
    
    if response.status_code == 409:
        print_success("Correctly rejected duplicate username")
    else:
        print_error("Should reject duplicate username")


def test_register_missing_field():
    """Test registrasi tanpa field yang required"""
    print_test("Register Missing Required Field")
    
    payload = {
        'username': 'testuser',
        # Missing email and password
    }
    
    print_info(f"Trying to register without email and password")
    response = requests.post(f'{BASE_URL}/users/register', json=payload)
    print_response(response)
    
    if response.status_code == 400:
        print_success("Correctly rejected incomplete data")
    else:
        print_error("Should reject incomplete data")


def test_get_user():
    """Test get user by ID"""
    print_test("Get User by ID")
    
    user_id = 1
    print_info(f"Getting user with ID: {user_id}")
    response = requests.get(f'{BASE_URL}/users/{user_id}')
    print_response(response)
    
    if response.status_code == 200:
        print_success(f"User retrieved successfully")
        return response.json()['data']
    elif response.status_code == 404:
        print_info("User not found")
    else:
        print_error("Failed to get user")
    
    return None


def test_get_nonexistent_user():
    """Test get user yang tidak ada"""
    print_test("Get Non-existent User")
    
    user_id = 99999
    print_info(f"Trying to get non-existent user ID: {user_id}")
    response = requests.get(f'{BASE_URL}/users/{user_id}')
    print_response(response)
    
    if response.status_code == 404:
        print_success("Correctly returned 404 for non-existent user")
    else:
        print_error("Should return 404 for non-existent user")


# ==================== PRODUCTS ENDPOINT TESTS ====================

def test_get_all_products():
    """Test mendapatkan semua produk"""
    print_test("Get All Products")
    
    print_info("Fetching all products")
    response = requests.get(f'{BASE_URL}/products/')
    print_response(response)
    
    if response.status_code == 200:
        products = response.json()['data']
        print_success(f"Retrieved {len(products)} products")
        return products
    else:
        print_error("Failed to get products")
        return []


def test_get_single_product():
    """Test mendapatkan single product"""
    print_test("Get Single Product")
    
    product_id = 1
    print_info(f"Getting product with ID: {product_id}")
    response = requests.get(f'{BASE_URL}/products/{product_id}')
    print_response(response)
    
    if response.status_code == 200:
        print_success("Product retrieved successfully")
        return response.json()['data']
    elif response.status_code == 404:
        print_info("Product not found")
    else:
        print_error("Failed to get product")
    
    return None


def test_create_product():
    """Test membuat produk baru"""
    print_test("Create New Product")
    
    payload = {
        'name': 'Test Product',
        'description': 'This is a test product',
        'price': 99.99,
        'stock': 20,
        'category_id': 1
    }
    
    print_info(f"Creating product: {payload['name']}")
    response = requests.post(f'{BASE_URL}/products/', json=payload)
    print_response(response)
    
    if response.status_code == 201:
        print_success("Product created successfully")
        return response.json()['data']
    else:
        print_error("Failed to create product")
        return None


def test_create_product_invalid_price():
    """Test membuat produk dengan harga invalid (negative)"""
    print_test("Create Product with Invalid Price")
    
    payload = {
        'name': 'Invalid Product',
        'description': 'This product has negative price',
        'price': -50.00,
        'stock': 10
    }
    
    print_info(f"Trying to create product with negative price: {payload['price']}")
    response = requests.post(f'{BASE_URL}/products/', json=payload)
    print_response(response)
    
    if response.status_code == 400:
        print_success("Correctly rejected invalid price")
    else:
        print_info("Check if constraint is working at database level")


def test_update_product():
    """Test update produk"""
    print_test("Update Product")
    
    product_id = 1
    payload = {
        'name': 'Updated Product Name',
        'price': 149.99,
        'stock': 50
    }
    
    print_info(f"Updating product ID: {product_id}")
    response = requests.put(f'{BASE_URL}/products/{product_id}', json=payload)
    print_response(response)
    
    if response.status_code == 200:
        print_success("Product updated successfully")
        return response.json()['data']
    elif response.status_code == 404:
        print_info("Product not found")
    else:
        print_error("Failed to update product")
    
    return None


def test_delete_product():
    """Test delete produk"""
    print_test("Delete Product")
    
    # First create a product to delete
    create_payload = {
        'name': 'Product to Delete',
        'description': 'This product will be deleted',
        'price': 29.99,
        'stock': 5
    }
    
    print_info("First, creating a product to delete...")
    create_response = requests.post(f'{BASE_URL}/products/', json=create_payload)
    
    if create_response.status_code == 201:
        product_id = create_response.json()['data']['id']
        print_success(f"Product created with ID: {product_id}")
        
        print_info(f"Now deleting product ID: {product_id}")
        delete_response = requests.delete(f'{BASE_URL}/products/{product_id}')
        print_response(delete_response)
        
        if delete_response.status_code == 200:
            print_success("Product deleted successfully")
        else:
            print_error("Failed to delete product")
    else:
        print_error("Failed to create product for deletion test")


def test_delete_nonexistent_product():
    """Test delete produk yang tidak ada"""
    print_test("Delete Non-existent Product")
    
    product_id = 99999
    print_info(f"Trying to delete non-existent product ID: {product_id}")
    response = requests.delete(f'{BASE_URL}/products/{product_id}')
    print_response(response)
    
    if response.status_code == 404:
        print_success("Correctly returned 404 for non-existent product")
    else:
        print_error("Should return 404 for non-existent product")


# ==================== PERFORMANCE TESTS ====================

def test_get_products_performance():
    """Test performance mendapatkan banyak produk"""
    print_test("Products Get Performance")
    
    print_info("Fetching all products and measuring response time...")
    start_time = time.time()
    response = requests.get(f'{BASE_URL}/products/')
    end_time = time.time()
    
    response_time = (end_time - start_time) * 1000
    
    if response.status_code == 200:
        product_count = len(response.json()['data'])
        print_success(f"Retrieved {product_count} products in {response_time:.2f}ms")
    else:
        print_error("Failed to get products")


# ==================== MAIN RUNNER ====================

def run_all_tests():
    """Run all tests"""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}STARTING ENDPOINT TESTS{Colors.END}")
    print(f"{Colors.YELLOW}Base URL: {BASE_URL}{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")
    
    try:
        # Users endpoint tests
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}USERS ENDPOINT TESTS{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        test_get_user()
        test_get_nonexistent_user()
        test_register_user()
        test_register_duplicate_user()
        test_register_missing_field()
        
        # Products endpoint tests
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}PRODUCTS ENDPOINT TESTS{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        test_get_all_products()
        test_get_single_product()
        test_create_product()
        test_create_product_invalid_price()
        test_update_product()
        test_delete_product()
        test_delete_nonexistent_product()
        
        # Performance tests
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}PERFORMANCE TESTS{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}")
        
        test_get_products_performance()
        
        print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
        print(f"{Colors.YELLOW}ALL TESTS COMPLETED{Colors.END}")
        print(f"{Colors.YELLOW}{'='*60}{Colors.END}\n")
        
    except requests.exceptions.ConnectionError:
        print_error(f"Could not connect to {BASE_URL}")
        print_info("Make sure Flask app is running: python app.py")
    except Exception as e:
        print_error(f"Test error: {e}")


if __name__ == '__main__':
    run_all_tests()
