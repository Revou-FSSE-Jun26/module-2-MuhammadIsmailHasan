"""
Start Flask development server with custom port support.

Usage:
    python3 run_server.py          # Port 5000
    python3 run_server.py 5001     # Port 5001
"""

import sys
import os
from app import app

def main(port=5000):
    """Start Flask development server."""
    print(f"🚀 Starting server at http://localhost:{port}")
    print(f"   Press Ctrl+C to stop\n")
    
    app.run(
        host='127.0.0.1',
        port=port,
        debug=False,
        use_reloader=False
    )

if __name__ == '__main__':
    port = 5000
    
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Error: Port must be a number")
            sys.exit(1)
    
    try:
        main(port)
    except KeyboardInterrupt:
        print("\n\n⛔ Server stopped")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
