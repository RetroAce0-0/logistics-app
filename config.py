import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/truck_logistics')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # It's crucial to set a strong, secret key in your environment for production.
    # You can generate one using: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY = os.getenv('SECRET_KEY', 'a-dev-secret-key-that-should-be-changed')
    # A separate, strong key for authenticating internal API requests.
    # Set this in your production environment.
    INTERNAL_API_KEY = os.getenv('INTERNAL_API_KEY', 'a-super-secret-internal-key-change-me')
