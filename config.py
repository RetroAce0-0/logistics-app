import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/truck_logistics')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # It's crucial to set a strong, secret key in your environment for production.
    # You can generate one using: python -c 'import secrets; print(secrets.token_hex())'
    SECRET_KEY = os.getenv('SECRET_KEY', 'a-dev-secret-key-that-should-be-changed')
