"""Survey routes: listing, creating, and the equipment stock rules."""

import unittest
from unittest.mock import patch

import app as reefwatch
from tests.helpers import FakeCollection


class SurveysTest(unittest.TestCase):
    def setUp(self):
        self.surveys = FakeCollection()
        self.equipment = FakeCollection([
            {"name": "Camera", "available_quantity": 5, "low_stock_threshold": 2},
        ])
        self.camera_id = next(iter(self.equipment.docs))
        collections = {"surveys": self.surveys, "equipment": self.equipment}
        patcher = patch.object(reefwatch, "get_collection", side_effect=collections.get)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = reefwatch.app.test_client()

    def form(self, quantity):
        return {
            "survey_date": "2026-10-15",
            "researcher_name": " Dr Jones ",
            "researcher_email": "jones@uni.edu",
            "species": "Clownfish, Manta Ray, ",
            "survey_cost": "1200.50",
            f"qty_{self.camera_id}": str(quantity),
        }

    def test_create_saves_survey_and_reduces_stock(self):
        response = self.client.post("/surveys/new", data=self.form(2))
        self.assertEqual(response.status_code, 302)
        survey = self.surveys.find()[0]
        self.assertEqual(survey["researcher"]["name"], "Dr Jones")
        self.assertEqual(survey["species_observed"], ["Clownfish", "Manta Ray"])
        self.assertEqual(survey["equipment_used"][0]["quantity"], 2)
        self.assertEqual(self.equipment.docs[self.camera_id]["available_quantity"], 3)

    def test_not_enough_stock_is_rejected(self):
        response = self.client.post("/surveys/new", data=self.form(99))
        self.assertEqual(response.status_code, 200)  # form shown again with an error
        self.assertIn(b"Not enough Camera", response.data)
        self.assertEqual(self.surveys.docs, {})
        self.assertEqual(self.equipment.docs[self.camera_id]["available_quantity"], 5)

    def test_list_shows_newest_first(self):
        for day in ("2026-10-01", "2026-10-20"):
            self.surveys.insert_one({
                "survey_date": day, "researcher": {"name": f"R{day}", "email": "a@b.c"},
                "species_observed": [], "equipment_used": [], "survey_cost": 1.0,
            })
        response = self.client.get("/surveys")
        self.assertEqual(response.status_code, 200)
        self.assertLess(response.data.index(b"R2026-10-20"), response.data.index(b"R2026-10-01"))


if __name__ == "__main__":
    unittest.main()
