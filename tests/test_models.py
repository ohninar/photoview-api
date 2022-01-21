from api.models import Comment, Like, Photo, User


def test_user_model(snapshot):
    instance = User({"name": "user test", "email": "user@test.com"})
    snapshot.assert_match(instance.to_primitive())


def test_photo_model(snapshot):
    instance = Photo({"URI": "s3://photoview/test.png"})
    snapshot.assert_match(instance.to_primitive())


def test_comment_model(snapshot):
    instance = Comment({"text": "comment test"})
    snapshot.assert_match(instance.to_primitive())


def test_like_model(snapshot):
    instance = Like()
    snapshot.assert_match(instance.to_primitive())
