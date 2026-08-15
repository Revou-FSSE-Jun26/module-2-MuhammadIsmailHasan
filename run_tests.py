"""
Run API endpoint tests with automatic port management.

Usage:
    python3 run_tests.py          # Default port 5001
    python3 run_tests.py 5002     # Custom port
"""

import sys
import os
import subprocess
import socket

def is_port_open(port):
    """Check if port is listening."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
    
    print("\n" + "="*60)
    print("🧪 API Test Suite")
    print("="*60)
    print(f"Port: {port}")
    print(f"URL: http://localhost:{port}\n")
    
    if not is_port_open(port):
        print(f"❌ Server not running on port {port}")
        print(f"\nStart server with:")
        print(f"  python3 run_server.py {port}")
        sys.exit(1)
    
    print("✓ Server is ready")
    print("\nStarting tests...\n")
    
    os.environ['FLASK_TEST_URL'] = f'http://localhost:{port}'
    result = subprocess.run([sys.executable, 'tests/test_endpoints.py'])
    sys.exit(result.returncode)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n⛔ Tests stopped")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
