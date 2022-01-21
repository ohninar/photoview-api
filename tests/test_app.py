import io
from unittest import mock

from bson.objectid import ObjectId

from api.models import Photo, User
from api.store import PhotoStore, UserStore


def test_api_signup(client, mongo_db):
    data = {"name": "user test", "email": "test@test.com", "password": "password"}
    response = client.post("/signup", json=data)
    assert response.status_code == 201


def test_api_signup_user_invalid(client, mongo_db):
    user_store = UserStore(mongo_db())
    user = User(
        {
            "_id": ObjectId(),
            "name": "user test",
            "email": "test@test.com",
            "password": "password",
        }
    )
    user_store.save(user)
    data = {"name": user.name, "email": user.email, "password": "password"}
    response = client.post("/signup", json=data)
    assert response.status_code == 400


def test_api_login(user_simple, client, mongo_db):
    data = {"email": user_simple.email, "password": user_simple.name}
    response = client.post("/signin", json=data)
    assert response.status_code == 200


def test_api_login_invalid(user_simple, client, mongo_db):
    data = {"email": user_simple.email, "password": "wrong anwser"}
    response = client.post("/signin", json=data)
    assert response.status_code == 401


@mock.patch("api.app.get_s3_uri")
def test_api_create_photo(get_s3_bucket_mocked, user_admin_token, client, mongo_db):
    photo_store = PhotoStore(mongo_db())

    get_s3_bucket_mocked.return_value = "s3://bucket/file.jpg"
    headers = {"Authorization": f"Bearer {user_admin_token}"}
    data = {"name": "photo test", "file": (io.BytesIO(b"abcdef"), "test.jpg")}
    response = client.post("/photos", data=data, headers=headers)
    assert response.status_code == 201

    photo_id = response.json["body"]["photo_id"]
    photo = photo_store.get_by_id(photo_id)
    assert photo.URI == "s3://bucket/file.jpg"


def test_api_create_photo_user_invalid(user_simple_token, client, mongo_db):
    headers = {"Authorization": f"Bearer {user_simple_token}"}
    data = {"name": "photo test", "file": (io.BytesIO(b"abcdef"), "test.jpg")}
    response = client.post("/photos", data=data, headers=headers)
    assert response.status_code == 403


def test_api_get_gallery(user_simple, user_simple_token, client, mongo_db):
    photo_store = PhotoStore(mongo_db())

    first_photo = Photo(
        {
            "_id": ObjectId(),
            "URI": "s3://photoview/test1.png",
            "user_id": user_simple._id,
        }
    )
    photo_store.save(first_photo)

    second_photo = Photo(
        {
            "_id": ObjectId(),
            "URI": "s3://photoview/test2.png",
            "visible": True,
            "user_id": user_simple._id,
        }
    )
    photo_store.save(second_photo)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {user_simple_token}",
    }

    response = client.get("/photos", headers=headers)
    assert response.status_code == 200
    assert len(response.json["photos"]) == 1
    assert response.json["photos"][0]["uri"] == second_photo["URI"]


def test_api_photo_authorized(user_admin, user_admin_token, client, mongo_db):
    photo_store = PhotoStore(mongo_db())

    first_photo = Photo(
        {
            "_id": ObjectId(),
            "URI": "s3://photoview/test1.png",
            "user_id": user_admin._id,
        }
    )
    photo_store.save(first_photo)

    photo = photo_store.get_by_id(first_photo._id)
    assert photo.visible is False

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {user_admin_token}",
    }

    response = client.put(f"/photos/{first_photo._id}/authorized", headers=headers)
    assert response.status_code == 200

    photo = photo_store.get_by_id(first_photo._id)
    assert photo.visible is True


def test_api_photo_authorized_user_not_admin(
    user_simple, user_simple_token, client, mongo_db
):
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

    photo = photo_store.get_by_id(first_photo._id)
    assert photo.visible is False

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {user_simple_token}",
    }

    response = client.put(f"/photos/{first_photo._id}/authorized", headers=headers)
    assert response.status_code == 403

    photo = photo_store.get_by_id(first_photo._id)
    assert photo.visible is False


def test_api_photo_liked(user_simple, user_simple_token, client, mongo_db):
    photo_store = PhotoStore(mongo_db())
    user_id = ObjectId()

    first_photo = Photo(
        {
            "_id": ObjectId(),
            "URI": "s3://photoview/test1.png",
            "user_id": user_id,
            "visible": True,
        }
    )
    photo_store.save(first_photo)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {user_simple_token}",
    }

    response = client.post(f"/photos/{first_photo._id}/liked", headers=headers)
    assert response.status_code == 200


def test_api_photo_comment(user_simple, user_simple_token, client, mongo_db):
    photo_store = PhotoStore(mongo_db())

    first_photo = Photo(
        {
            "_id": ObjectId(),
            "URI": "s3://photoview/test1.png",
            "user_id": user_simple._id,
            "visible": True,
        }
    )
    photo_store.save(first_photo)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {user_simple_token}",
    }

    data = {
        "text": "test text",
    }
    response = client.post(
        f"/photos/{first_photo._id}/comment", json=data, headers=headers
    )
    assert response.status_code == 200
