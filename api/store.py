from datetime import datetime

from flask_bcrypt import check_password_hash, generate_password_hash
from pymongo import MongoClient

from api import config
from api.models import Comment, Like, Photo, User
from api.storage import StorageMixin

mongo_client = MongoClient(config.mongo_uri)
mongo_db = mongo_client[config.mongo_db]


class UserStore(StorageMixin):
    namespace = "user"
    collection = User

    on_save_defaults = {  # type: ignore
        "created_at": datetime.utcnow,
    }

    def get_by_email(self, email):
        return self.get({"email": email})

    def set_hash_password(self, user_id, password):
        hash_password = generate_password_hash(password).decode("utf8")
        self.update_by_id(user_id, {"password": hash_password})

    def check_password(self, user_id, password):
        user_target = self.get_by_id(user_id)
        return check_password_hash(user_target.password, password)


class PhotoStore(StorageMixin):
    namespace = "photo"
    collection = Photo

    on_save_defaults = {  # type: ignore
        "created_at": datetime.utcnow,
    }

    def get_visible_photos(self, offset=0, per_page=10):
        photos = self.find({"visible": True})
        delivery_photos = []
        for photo in photos[offset: offset + per_page]:
            delivery_photos.append({"id": str(photo._id), "uri": photo.URI})
        return len(photos), delivery_photos

    def get_pendent_photos(self):
        photos = self.find({"visible": False})
        pendent_photos = []
        for photo in photos:
            pendent_photos.append({"id": str(photo._id), "uri": photo.URI})
        return pendent_photos

    def authorized(self, photo_id):
        self.update_by_id(photo_id, {"visible": True})


class CommentStore(StorageMixin):
    namespace = "comment"
    collection = Comment

    on_save_defaults = {  # type: ignore
        "created_at": datetime.utcnow,
    }


class LikeStore(StorageMixin):
    namespace = "like"
    collection = Like

    on_save_defaults = {  # type: ignore
        "created_at": datetime.utcnow,
    }
