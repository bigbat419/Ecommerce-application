import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import Config

ALLOWED_EXT = {'png','jpg','jpeg','gif'}

def hash_password(plain):
    return generate_password_hash(plain)

def verify_password(hash, plain):
    return check_password_hash(hash, plain)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

def save_upload_local(fileobj, upload_folder=None):
    upload_folder = upload_folder or Config.UPLOAD_FOLDER
    os.makedirs(upload_folder, exist_ok=True)
    filename = secure_filename(fileobj.filename)
    path = os.path.join(upload_folder, filename)
    fileobj.save(path)
    return path

def save_upload_s3(fileobj, key=None):
    import boto3
    s3 = boto3.client('s3',
                      aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
                      region_name=Config.AWS_S3_REGION)
    filename = secure_filename(fileobj.filename)
    key = key or filename
    s3.upload_fileobj(fileobj, Config.AWS_S3_BUCKET, key)
    url = f"https://{Config.AWS_S3_BUCKET}.s3.{Config.AWS_S3_REGION}.amazonaws.com/{key}"
    return url

def save_upload(fileobj):
    # prefer S3 if configured
    if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY and Config.AWS_S3_BUCKET:
        return save_upload_s3(fileobj)
    return save_upload_local(fileobj)
