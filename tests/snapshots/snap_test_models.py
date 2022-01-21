# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots['test_comment_model 1'] = {
    '_id': None,
    'created_at': None,
    'photo_id': None,
    'text': 'comment test',
    'user_id': None
}

snapshots['test_like_model 1'] = {
    '_id': None,
    'created_at': None,
    'photo_id': None,
    'user_id': None
}

snapshots['test_photo_model 1'] = {
    'URI': 's3://photoview/test.png',
    '_id': None,
    'created_at': None,
    'user_id': None,
    'visible': False
}

snapshots['test_user_model 1'] = {
    '_id': None,
    'admin': False,
    'created_at': None,
    'email': 'user@test.com',
    'name': 'user test',
    'password': None
}
