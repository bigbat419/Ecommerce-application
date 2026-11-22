import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # ── Application ──────────────────────────────────────────────────────────
    SITE_NAME = os.getenv('SITE_NAME', 'Flamingos')
    SITE_TAGLINE = os.getenv('SITE_TAGLINE', 'Style That Speaks')
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')

    # ── Database ─────────────────────────────────────────────────────────────
    MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'ecommerce_db')   # matches existing local DB
    MYSQL_CURSORCLASS = 'DictCursor'

    # ── File uploads ─────────────────────────────────────────────────────────
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024   # 10 MB

    # ── AWS S3 (optional) ────────────────────────────────────────────────────
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET')
    AWS_S3_REGION = os.getenv('AWS_S3_REGION', 'us-east-1')

    # ── Stripe (optional) ────────────────────────────────────────────────────
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

    # ── Paystack ─────────────────────────────────────────────────────────────
    PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY', '')
    PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY', '')

    TESTING = False
