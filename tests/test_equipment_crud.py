"""Equipment CRUD routes. Run all tests with:  python -m unittest -v"""

import unittest
from unittest.mock import patch

import app as reefwatch
from tests.helpers import FakeCollection

FORM = {
    "name": "  Camera  ",
    "category": "Imaging",
    "replacement_cost": "450.50",
    "available_quantity": "5",
    "low_stock_threshold": "2",
    "status": "Active",
}


class EquipmentCrudTest(unittest.TestCase):
    def setUp(self):
        self.collection = FakeCollection()
        patcher = patch.object(reefwatch, "get_collection", return_value=self.collection)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = reefwatch.app.test_client()

    def create_item(self):
        self.client.post("/equipment/save", data=FORM)
        return next(iter(self.collection.docs))

    def test_create(self):
        response = self.client.post("/equipment/save", data=FORM)
        self.assertEqual(response.status_code, 302)
        item = self.collection.find()[0]
        self.assertEqual(item["name"], "Camera")  # whitespace stripped
        self.assertEqual(item["replacement_cost"], 450.50)
        self.assertEqual(item["available_quantity"], 5)

    def test_read(self):
        self.create_item()
        response = self.client.get("/equipment")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Camera", response.data)

    def test_update(self):
        item_id = self.create_item()
        self.client.post("/equipment/save", data={**FORM, "id": str(item_id), "available_quantity": "9"})
        self.assertEqual(len(self.collection.docs), 1)  # updated, not duplicated
        self.assertEqual(self.collection.docs[item_id]["available_quantity"], 9)

    def test_delete(self):
        item_id = self.create_item()
        self.client.post("/equipment/delete", data={"id": str(item_id)})
        self.assertEqual(self.collection.docs, {})


if __name__ == "__main__":
    unittest.main()
