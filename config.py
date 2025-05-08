import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'app.log')