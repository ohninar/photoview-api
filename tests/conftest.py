import pytest
from bson.objectid import ObjectId
from flask_bcrypt import generate_password_hash
from pymongo import MongoClient

from api import app as app_api
from api import config
from api.models import User
from api.store import UserStore


@pytest.fixture
def mongo_db(request):
    def setup():
        mongo_client = MongoClient(config.mongo_uri)
        request.addfinalizer(lambda: mongo_client.drop_database(config.mongo_db))
        return mongo_client[config.mongo_db]

    return setup


@pytest.fixture
def app():
    app_api.flask_app.config["TESTING"] = True
    app_api.flask_app.config["SERVER_NAME"] = "test."
    app_api.flask_app.config["DEBUG"] = True
    return app_api.flask_app


@pytest.fixture
def client(app):
    return app.test_client()


def get_token(user, client):
    data = {"email": user.email, "password": user.name}
    response = client.post("/signin", json=data)
    return response.json.get("token")


@pytest.fixture
def user_simple(mongo_db):
    user_store = UserStore(mongo_db())
    user = User(
        {
            "_id": ObjectId(),
            "name": "user simple",
            "email": "simple@test.com",
            "password": generate_password_hash("user simple").decode("utf8"),
        }
    )
    return user_store.save(user)


@pytest.fixture
def user_simple_token(user_simple, client):
    return get_token(user_simple, client)


@pytest.fixture
def user_admin(mongo_db):
    user_store = UserStore(mongo_db())
    user = User(
        {
            "_id": ObjectId(),
            "admin": True,
            "name": "user admin",
            "email": "admin@test.com",
            "password": generate_password_hash("user admin").decode("utf8"),
        }
    )
    return user_store.save(user)


@pytest.fixture
def user_admin_token(user_admin, client):
    return get_token(user_admin, client)
