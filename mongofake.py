"""Simple in-memory mock for pymongo used in demos and unit tests.
The implementation covers the subset of API used by the FitTrack app
and its test suite:
* MongoClient
* Database (__getitem__) returning collections
* Collection queries with equality, range, and not-equal filters
* Collection methods: insert_one, find_one, find, update_one, delete_one,
  delete_many, count_documents, create_index, drop
* Cursor with chainable sort() and limit()
* drop_database operation
* ObjectId generation via bson.ObjectId (already a dependency)
"""

from typing import List, Dict, Any
from bson import ObjectId

_MISSING = object()


def _matches_filter(document: Dict[str, Any], filter: Dict[str, Any]) -> bool:
    for key, expected in filter.items():
        actual = document.get(key, _MISSING)
        if isinstance(expected, dict) and any(
            operator.startswith("$") for operator in expected
        ):
            for operator, value in expected.items():
                if operator == "$ne":
                    if actual == value or (actual is _MISSING and value is None):
                        return False
                elif operator in {"$gte", "$gt", "$lte", "$lt"}:
                    if actual is _MISSING:
                        return False
                    if operator == "$gte" and not actual >= value:
                        return False
                    if operator == "$gt" and not actual > value:
                        return False
                    if operator == "$lte" and not actual <= value:
                        return False
                    if operator == "$lt" and not actual < value:
                        return False
                else:
                    raise NotImplementedError(
                        f"FakeCollection does not support query operator {operator}"
                    )
        elif actual is _MISSING or actual != expected:
            return False
    return True


class FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id

class FakeUpdateResult:
    def __init__(self, matched_count: int, modified_count: int):
        self.matched_count = matched_count
        self.modified_count = modified_count

class FakeDeleteResult:
    def __init__(self, deleted_count: int):
        self.deleted_count = deleted_count

class FakeCursor:
    def __init__(self, docs: List[Dict[str, Any]]):
        self._docs = docs

    def sort(self, key: str, direction: int = 1):
        reverse = direction < 0
        self._docs.sort(key=lambda d: d.get(key), reverse=reverse)
        return self

    def limit(self, n: int):
        self._docs = self._docs[:n]
        return self

    def __iter__(self):
        return iter(self._docs)

    def __len__(self):
        return len(self._docs)

class FakeCollection:
    def __init__(self, name: str):
        self._name = name
        self._documents: List[Dict[str, Any]] = []
        self._indexes = []

    def insert_one(self, doc: Dict[str, Any]):
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        self._documents.append(dict(doc))
        return FakeInsertResult(doc["_id"])

    def insert_many(self, docs: List[Dict[str, Any]]):
        inserted_ids = []
        for doc in docs:
            if "_id" not in doc:
                doc["_id"] = ObjectId()
            self._documents.append(dict(doc))
            inserted_ids.append(doc["_id"])
        class FakeInsertManyResult:
            def __init__(self, ids):
                self.inserted_ids = ids
        return FakeInsertManyResult(inserted_ids)

    def find_one(self, filter: Dict[str, Any] = None):
        filter = filter or {}
        for d in self._documents:
            if _matches_filter(d, filter):
                return dict(d)
        return None

    def find(self, filter: Dict[str, Any] = None):
        filter = filter or {}
        matches = [dict(d) for d in self._documents if _matches_filter(d, filter)]
        return FakeCursor(matches)

    def update_one(self, filter: Dict[str, Any], update: Dict[str, Any]):
        for d in self._documents:
            if _matches_filter(d, filter):
                changes = update.get("$set", {})
                d.update(changes)
                return FakeUpdateResult(matched_count=1, modified_count=1)
        return FakeUpdateResult(matched_count=0, modified_count=0)

    def delete_one(self, filter: Dict[str, Any]):
        for index, document in enumerate(self._documents):
            if _matches_filter(document, filter):
                del self._documents[index]
                return FakeDeleteResult(deleted_count=1)
        return FakeDeleteResult(deleted_count=0)

    def delete_many(self, filter: Dict[str, Any]):
        to_delete = [d for d in self._documents if _matches_filter(d, filter)]
        count = len(to_delete)
        self._documents = [
            d for d in self._documents if not _matches_filter(d, filter)
        ]
        return FakeDeleteResult(deleted_count=count)

    def count_documents(self, filter: Dict[str, Any] = None):
        filter = filter or {}
        return sum(1 for d in self._documents if _matches_filter(d, filter))

    def create_index(self, *args, **kwargs):
        self._indexes.append((args, kwargs))
        return None

    def drop(self):
        self._documents.clear()
        self._indexes.clear()

class FakeDatabase:
    def __init__(self, name: str):
        self._name = name
        self._collections: Dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection(name)
        return self._collections[name]

    def __getattr__(self, name: str) -> FakeCollection:
        return self.__getitem__(name)

class FakeMongoClient:
    """Mimics pymongo.MongoClient with minimal behaviour.
    Accepts the same constructor signature but ignores all arguments.
    """
    def __init__(self, *args, **kwargs):
        self._databases: Dict[str, FakeDatabase] = {}
        self.admin = self

    def __getitem__(self, name: str) -> FakeDatabase:
        if name not in self._databases:
            self._databases[name] = FakeDatabase(name)
        return self._databases[name]

    def __getattr__(self, name: str) -> FakeDatabase:
        return self.__getitem__(name)

    def command(self, cmd: str):
        if cmd.lower() == "ping":
            return {"ok": 1}
        raise NotImplementedError(f"FakeMongoClient.command only implements 'ping', got {cmd}")

    def close(self):
        pass

    def drop_database(self, name: str):
        """Remove a database from the mock client.
        Accepts either a name (str) or a FakeDatabase instance.
        """
        if isinstance(name, str):
            self._databases.pop(name, None)
        else:
            self._databases.pop(getattr(name, "_name", None), None)
