"""
Gunicorn 生产环境启动配置
"""
import os

bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
workers = int(os.getenv('GUNICORN_WORKERS', '2'))
worker_class = 'gevent'
timeout = 120
keepalive = 5
preload_app = True