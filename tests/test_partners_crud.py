"""Partners CRUD routes."""

import unittest
from unittest.mock import patch

import app as reefwatch
from tests.helpers import FakeCollection

FORM = {
    "organisation_name": "  Reef Trust ",
    "contact_name": "Sam Lee",
    "contact_email": "sam@reeftrust.org",
    "contact_phone": "0400 000 000",
    "conservation_areas": "Lizard Island, , Heron Island",
}


class PartnersCrudTest(unittest.TestCase):
    def setUp(self):
        self.collection = FakeCollection()
        patcher = patch.object(reefwatch, "get_collection", return_value=self.collection)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = reefwatch.app.test_client()

    def create_partner(self):
        self.client.post("/partners/save", data=FORM)
        return next(iter(self.collection.docs))

    def test_create(self):
        response = self.client.post("/partners/save", data=FORM)
        self.assertEqual(response.status_code, 302)
        partner = self.collection.find()[0]
        self.assertEqual(partner["organisation_name"], "Reef Trust")
        self.assertEqual(partner["contact"]["email"], "sam@reeftrust.org")
        self.assertEqual(partner["conservation_areas"], ["Lizard Island", "Heron Island"])

    def test_read(self):
        self.create_partner()
        response = self.client.get("/partners")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Reef Trust", response.data)

    def test_update(self):
        partner_id = self.create_partner()
        self.client.post("/partners/save", data={**FORM, "id": str(partner_id), "contact_name": "Alex Kim"})
        self.assertEqual(len(self.collection.docs), 1)
        self.assertEqual(self.collection.docs[partner_id]["contact"]["name"], "Alex Kim")

    def test_delete(self):
        partner_id = self.create_partner()
        self.client.post("/partners/delete", data={"id": str(partner_id)})
        self.assertEqual(self.collection.docs, {})


if __name__ == "__main__":
    unittest.main()
