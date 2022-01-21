import datetime

from bson.errors import InvalidId
from bson.objectid import ObjectId
from flask import Flask, jsonify, request
from flask_bcrypt import Bcrypt, generate_password_hash
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)

from api import config
from api.models import Comment, Like, Photo, User
from api.s3 import get_s3_uri
from api.store import CommentStore, LikeStore, PhotoStore, UserStore, mongo_db


def create_app():
    app = Flask(__name__)
    app.secret_key = config.secret_key
    app.url_map.strict_slashes = False
    app.config["SERVER_NAME"] = config.server_name
    app.config["JWT_SECRET_KEY"] = config.jwt_secret_key
    return app


flask_app = create_app()
bcrypt = Bcrypt(flask_app)
jwt = JWTManager(flask_app)

user_store = UserStore(mongo_db)
photo_store = PhotoStore(mongo_db)
like_store = LikeStore(mongo_db)
comment_store = CommentStore(mongo_db)


@flask_app.route("/health", methods=["GET"])
def health():
    return jsonify({"message": "healthy"})


@flask_app.route("/signup", methods=["POST"])
def signup():
    json_data = request.get_json(force=True)
    name = json_data.get("name")
    email = json_data.get("email")
    password = json_data.get("password")
    user = user_store.get_by_email(email)
    if user:
        return jsonify({"error": "email invalid"}), 400

    user = User(
        {
            "_id": ObjectId(),
            "name": name,
            "email": email,
            "password": generate_password_hash(password).decode("utf8"),
        }
    )
    user_store.save(user)
    return jsonify({"message": "success", "body": {"user_id": str(user._id)}}), 201


@flask_app.route("/signin", methods=["POST"])
def signin():
    body = request.get_json()
    email = body.get("email")
    password = body.get("password")
    user = user_store.get_by_email(email)
    if not user:
        return {"error": "Email or password invalid"}, 401

    authorized = user_store.check_password(user._id, password)
    if not authorized:
        return {"error": "Email or password invalid"}, 401

    expires = datetime.timedelta(days=7)
    access_token = create_access_token(identity=str(user._id), expires_delta=expires)

    return {"token": access_token}, 200


@flask_app.route("/photos", methods=["POST"])
@jwt_required()
def add_photo():
    photo_file = request.files["file"]
    if photo_file.filename == "":
        error = "No file in request"
        return jsonify({"error": error}), 400

    user_id = get_jwt_identity()
    user = user_store.get_by_id(user_id)
    if not user or not user.admin:
        return jsonify({"detail": "not found"}), 403

    s3_uri = get_s3_uri(photo_file)

    photo = Photo(
        {
            "_id": ObjectId(),
            "user_id": user_id,
            "URI": s3_uri,
        }
    )
    photo_store.save(photo)

    return jsonify({"message": "success", "body": {"photo_id": str(photo._id)}}), 201


@flask_app.route("/photos", methods=["GET"])
@jwt_required()
def list_photos():
    offset = request.args.get("offset", 0)
    per_page = request.args.get("per_page", 10)

    total_photos, photos = photo_store.get_visible_photos(
        offset=offset, per_page=per_page
    )

    return jsonify(
        {
            "total": total_photos,
            "offset": offset,
            "per_page": per_page,
            "photos": photos,
        }
    )


@flask_app.route("/photos/pendent", methods=["GET"])
@jwt_required()
def list_pendent_photos():
    user_id = get_jwt_identity()
    user = user_store.get_by_id(user_id)
    if not user:
        return jsonify({"detail": "not found"}), 404

    if not user.admin:
        return jsonify({"detail": "forbidden"}), 403

    photos = photo_store.get_pendent_photos()

    return jsonify(
        {
            "photos": photos,
        }
    )


@flask_app.route(
    "/photos/<string:photo_id>/authorized", methods=["PUT"], endpoint="authorized_photo"
)
@jwt_required()
def photo_authorized(photo_id):
    try:
        photo_store.get_by_id(photo_id)
    except InvalidId:
        return jsonify({"detail": "not found"}), 404

    user_id = get_jwt_identity()
    user = user_store.get_by_id(user_id)
    if not user:
        return jsonify({"detail": "not found"}), 404

    if not user.admin:
        return jsonify({"detail": "forbidden"}), 403

    photo_store.authorized(photo_id)
    return jsonify({"photo_id": photo_id, "status": "authorized"})


@flask_app.route("/photos/<string:photo_id>/liked", methods=["POST"])
@jwt_required()
def photo_liked(photo_id):
    try:
        photo_store.get_by_id(photo_id)
    except InvalidId:
        return jsonify({"detail": "not found"}), 404

    user_id = get_jwt_identity()
    like = Like({"_id": ObjectId(), "photo_id": photo_id, "user_id": user_id})
    like_store.save(like)
    return jsonify(like.to_primitive())


@flask_app.route("/photos/<string:photo_id>/comment", methods=["POST"])
@jwt_required()
def photo_add_comment(photo_id):
    try:
        photo_store.get_by_id(photo_id)
    except InvalidId:
        return jsonify({"detail": "not found"}), 404

    user_id = get_jwt_identity()
    json_data = request.get_json(force=True)
    text = json_data.get("text")

    comment = Comment(
        {"_id": ObjectId(), "photo_id": photo_id, "user_id": user_id, "text": text}
    )
    comment_store.save(comment)
    return jsonify(comment.to_primitive())
