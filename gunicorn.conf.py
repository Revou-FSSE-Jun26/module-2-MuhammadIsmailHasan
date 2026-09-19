import os

bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))
threads = int(os.environ.get("GUNICORNS_THREADS", "1"))
timeout = 30
graceful_timeout = 20
keepalive = 5

max_requests = 1000
max_requests_jitter = 100

accesslog = "-"
errorlog = "-"

forwarded_allow_ips = os.environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1")