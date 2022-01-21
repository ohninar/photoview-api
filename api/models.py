from flask_bcrypt import check_password_hash, generate_password_hash
from schematics.contrib.mongo import ObjectIdType
from schematics.models import Model
from schematics.types import BooleanType, DateTimeType, EmailType, StringType


class User(Model):
    _id = ObjectIdType(required=True)
    name = StringType(required=True)
    email = EmailType(required=True)
    password = StringType(required=True)
    admin = BooleanType(default=False)
    created_at = DateTimeType()


class Photo(Model):
    _id = ObjectIdType(required=True)
    URI = StringType(required=True)
    user_id = ObjectIdType(required=True)
    visible = BooleanType(default=False)
    created_at = DateTimeType()


class Comment(Model):
    _id = ObjectIdType(required=True)
    photo_id = ObjectIdType(required=True)
    user_id = ObjectIdType(required=True)
    text = StringType(required=True)
    created_at = DateTimeType()


class Like(Model):
    _id = ObjectIdType(required=True)
    photo_id = ObjectIdType(required=True)
    user_id = ObjectIdType(required=True)
    created_at = DateTimeType()
