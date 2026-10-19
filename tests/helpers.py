"""Shared test helpers: an in-memory stand-in for a pymongo collection."""

from bson import ObjectId


class FakeCollection:
    """Minimal fake of a pymongo collection (no database needed)."""

    def __init__(self, docs=None, aggregate_results=None):
        self.docs = {}
        for doc in docs or []:
            self.insert_one(doc)
        # Canned results, returned one per aggregate() call (Cosmos does the maths).
        self.aggregate_results = list(aggregate_results or [])

    def insert_one(self, doc):
        doc["_id"] = ObjectId()
        self.docs[doc["_id"]] = dict(doc)

    def find(self):
        return [dict(d) for d in self.docs.values()]

    def find_one(self, query):
        doc = self.docs.get(query["_id"])
        return dict(doc) if doc else None

    def update_one(self, query, update):
        doc = self.docs[query["_id"]]
        doc.update(update.get("$set", {}))
        for field, amount in update.get("$inc", {}).items():
            doc[field] += amount

    def delete_one(self, query):
        self.docs.pop(query["_id"], None)

    def aggregate(self, pipeline):
        return self.aggregate_results.pop(0)
