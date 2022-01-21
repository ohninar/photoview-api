import boto3
from bson.objectid import ObjectId
from furl import furl

from api import config

s3_session = boto3.Session()


def get_s3_bucket():
    s3 = s3_session.resource(
        "s3",
        aws_access_key_id=config.aws_access,
        aws_secret_access_key=config.aws_secret,
    )
    return s3.Bucket(config.s3_bucket)


def get_s3_key(file_name):
    return f"{ObjectId()}-{file_name}"


def get_s3_uri(file):
    bucket = get_s3_bucket()
    key = get_s3_key(file.filename)
    bucket.Object(key).put(Body=file.read())
    return furl(f"{config.s3_host}/{config.s3_bucket}/{key}").url
