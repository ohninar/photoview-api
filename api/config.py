import os

secret_key = os.environ.get("SECRET_KEY")
server_name = os.environ.get("SERVER_NAME")

mongo_uri = os.environ.get("ORMONGO_URL", "localhost:27017")
mongo_db = os.environ.get("MONGO_DB", "photoview")
mongo_read_preference = os.environ.get("MONGO_READ_PREFERENCE", "PRIMARY")

jwt_secret_key = os.environ.get("JWT_SECRET_KEY", "t1NP63m4wnBg6nyHYKfmc2TpCOGI4nss")

aws_access = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
s3_bucket = os.environ.get("AWS_S3_BUCKET_NAME")
s3_host = os.environ.get("AWS_S3_HOST", "https://s3.amazonaws.com")
