"""
社区安防门禁系统 - 应用启动入口
"""
import os, sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
os.environ.setdefault('DATABASE_URL', 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'data', 'dev.db'))
os.environ.setdefault('FLASK_ENV', 'development')

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
