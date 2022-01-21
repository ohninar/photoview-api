from bson.objectid import ObjectId

from api.models import Photo
from api.store import PhotoStore


def test_photo_store_get_visible_photos(mongo_db):
    photo_store = PhotoStore(mongo_db())
    user_id = ObjectId()

    first_photo = Photo(
        {
            "_id": ObjectId(),
            "URI": "s3://photoview/test1.png",
            "user_id": user_id,
        }
    )
    photo_store.save(first_photo)

    second_photo = Photo(
        {
            "_id": ObjectId(),
            "URI": "s3://photoview/test2.png",
            "visible": True,
            "user_id": user_id,
        }
    )
    photo_store.save(second_photo)

    total_photo, photos_visible = photo_store.get_visible_photos()
    assert total_photo == 1
    assert photos_visible[0]["uri"] == second_photo["URI"]


def test_photo_store_authorized(mongo_db):
    photo_store = PhotoStore(mongo_db())
    photo = Photo(
        {
            "_id": ObjectId(),
            "URI": "s3://photoview/test1.png",
            "user_id": ObjectId(),
        }
    )
    photo_store.save(photo)
    photo = photo_store.get_by_id(photo._id)
    assert photo.visible is False

    photo_store.authorized(photo._id)
    photo = photo_store.get_by_id(photo._id)
    assert photo.visible is True
