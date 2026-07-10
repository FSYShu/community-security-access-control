import os, sys
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DATABASE_URL', 'sqlite:///' + os.path.join(os.path.dirname(__file__), 'data', 'dev.db'))
os.environ.setdefault('FLASK_ENV', 'development')
from app import create_app
app = create_app()
app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
