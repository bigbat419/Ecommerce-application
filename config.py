import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY','change-me')
    MYSQL_HOST = os.getenv('MYSQL_HOST','db')
    MYSQL_USER = os.getenv('MYSQL_USER','root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD','example')
    MYSQL_DB = os.getenv('MYSQL_DB','ecommerce_db')
    MYSQL_CURSORCLASS = 'DictCursor'
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER','uploads')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET')
    AWS_S3_REGION = os.getenv('AWS_S3_REGION','us-east-1')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
    TESTING = False
