from collections import Iterable

import backoff
from bson.codec_options import CodecOptions
from bson.objectid import ObjectId
from pymongo import ASCENDING, DESCENDING, ReadPreference, UpdateOne
from pymongo.errors import (
    BulkWriteError,
    ConnectionFailure,
    ServerSelectionTimeoutError,
)
from schematics.contrib.mongo import ObjectIdType

from api.config import mongo_read_preference


class MongoErrorCodes:
    """See: https://github.com/mongodb/mongo/blob/master/src/mongo/base/error_codes.err"""

    DuplicateKey = 11000


ALLOWED_MONGO_READ_PREFERENCES = {
    "PRIMARY": ReadPreference.PRIMARY,
    "SECONDARY": ReadPreference.SECONDARY,
    "PRIMARY_PREFERRED": ReadPreference.PRIMARY_PREFERRED,
    "SECONDARY_PREFERRED": ReadPreference.SECONDARY_PREFERRED,
}

MONGO_SORT_ORDERS = {"ASC": ASCENDING, "DESC": DESCENDING}


class StorageMixin:
    tz_aware = False
    role = None
    on_save_defaults = None
    on_update_defaults = None

    @backoff.on_exception(
        backoff.expo, (ConnectionFailure, ServerSelectionTimeoutError), max_tries=12
    )
    def __init__(self, db, read_preference=mongo_read_preference):
        options = CodecOptions(tz_aware=self.tz_aware)
        self.db = db.get_collection(
            self.namespace,
            codec_options=options,
            read_preference=ALLOWED_MONGO_READ_PREFERENCES[read_preference],
        )

    def validate(self, obj):
        self.collection(obj).validate()

    def _ensure_object_id(self, value):
        if value is None:
            return
        elif isinstance(value, ObjectId):
            return value
        return ObjectId(value)

    def _convert_keys_to_object_id(self, obj):
        for field_name, field_type in self.collection.fields.items():
            if isinstance(field_type, ObjectIdType):
                obj_value = obj.get(field_name)
                obj_value = self._ensure_object_id(obj_value)
                if obj_value is not None:
                    obj[field_name] = obj_value

    def _model_to_dict(self, obj):
        if not isinstance(obj, dict):
            obj = obj.to_native(role=self.role)
        self._convert_keys_to_object_id(obj)
        return obj

    def format_return(self, ret):
        if ret is None:
            return
        elif isinstance(ret, Iterable) and not isinstance(ret, dict):
            return tuple(self.format_return(value) for value in ret)
        return self.collection(ret)

    def apply_hook(self, obj, hook):
        for k, v_fn in (hook or {}).items():
            obj[k] = v_fn()

        return obj

    @backoff.on_exception(
        backoff.expo, (ConnectionFailure, ServerSelectionTimeoutError), max_tries=12
    )
    def save(self, obj, apply_hook=True):
        hooks = self.on_save_defaults if apply_hook else {}
        obj = self.apply_hook(self._model_to_dict(obj), hooks)

        self.validate(obj)

        self.db.insert_one(obj).inserted_id
        return self.collection(obj)

    @backoff.on_exception(
        backoff.expo, (ConnectionFailure, ServerSelectionTimeoutError), max_tries=12
    )
    def save_many(self, obj_list):
        if len(obj_list) == 0:
            return 0

        try:
            objs = []
            for obj in obj_list:
                obj = self.apply_hook(self._model_to_dict(obj), self.on_save_defaults)
                self.validate(obj)
                objs.append(obj)

            result = self.db.insert_many(objs, ordered=False)
            return len(result.inserted_ids)
        except BulkWriteError as bwe:
            bulk_api_result = bwe.details
            errors = bulk_api_result["writeErrors"]
            if any(error["code"] != MongoErrorCodes.DuplicateKey for error in errors):
                raise bwe
            return bulk_api_result["nInserted"]

    @backoff.on_exception(
        backoff.expo, (ConnectionFailure, ServerSelectionTimeoutError), max_tries=12
    )
    def get(self, where):
        return self.format_return(self.db.find_one(where))

    def build_sort(self, field, order):
        return lambda query: query.sort(field, MONGO_SORT_ORDERS[order.upper()])

    @backoff.on_exception(
        backoff.expo, (ConnectionFailure, ServerSelectionTimeoutError), max_tries=12
    )
    def get_random_match(self, matcher):
        pipeline = [{"$match": matcher}, {"$sample": {"size": 1}}]
        results = list(self.db.aggregate(pipeline))
        if not results:
            return None

        return self.format_return(results[0])

    def find(self, where, sort=None, limit=None, fields=None):
        return tuple(
            self.format_return(value)
            for value in self.find_without_format(where, sort, limit, fields)
        )

    @backoff.on_exception(
        backoff.expo, (ConnectionFailure, ServerSelectionTimeoutError), max_tries=12
    )
    def find_without_format(self, where, sort=None, limit=50, fields=None, skip=0):
        query = self.db.find(where, fields)
        query.skip(skip)

        if limit:
            query.limit(limit)

        if sort is not None:
            query.sort(sort)

        return query

    def get_by_id(self, id):
        return self.get({"_id": self._ensure_object_id(id)})

    def remove_by_id(self, id):
        return self.db.remove({"_id": self._ensure_object_id(id)})

    @backoff.on_exception(
        backoff.expo, (ConnectionFailure, ServerSelectionTimeoutError), max_tries=12
    )
    def update(self, where, changes):
        changes = self.apply_hook(changes, self.on_update_defaults)
        return self.db.update_many(where, {"$set": changes})

    @backoff.on_exception(
        backoff.expo, (ConnectionFailure, ServerSelectionTimeoutError), max_tries=12
    )
    def bulk_upsert_by_id(self, objs):
        objs_to_upsert = {
            self._ensure_object_id(obj["_id"]): self.apply_hook(
                self._model_to_dict(obj), self.on_update_defaults
            )
            for obj in objs
        }

        return self.db.bulk_write(
            [
                UpdateOne({"_id": _id}, {"$set": obj}, upsert=True)
                for _id, obj in objs_to_upsert.items()
            ],
            ordered=False,
        )

    def upsert_by_id(self, obj):
        self.upsert({"_id": self._ensure_object_id(obj["_id"])}, obj)

    @backoff.on_exception(
        backoff.expo, (ConnectionFailure, ServerSelectionTimeoutError), max_tries=12
    )
    def upsert(self, where, obj):
        obj = self.apply_hook(self._model_to_dict(obj), self.on_update_defaults)
        not_null_obj = {k: obj[k] for k in obj if obj[k] is not None}
        self.validate(obj)
        return self.db.update_one(where, {"$set": not_null_obj}, upsert=True)

    def update_by_id(self, id, changes):
        changes = self.apply_hook(changes, self.on_update_defaults)
        return self.update({"_id": self._ensure_object_id(id)}, changes)
