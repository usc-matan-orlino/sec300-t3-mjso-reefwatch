"""Dashboard route: today's totals and the weekly chart data."""

import unittest
from datetime import date
from unittest.mock import patch

import app as reefwatch
from tests.helpers import FakeCollection


class DashboardTest(unittest.TestCase):
    def get_dashboard(self, rows):
        surveys = FakeCollection(aggregate_results=[rows])
        with patch.object(reefwatch, "get_collection", return_value=surveys), \
                patch.object(reefwatch, "render_template", return_value="ok") as render:
            response = reefwatch.app.test_client().get("/dashboard")
        self.assertEqual(response.status_code, 200)
        return render.call_args.kwargs

    def test_today_totals_and_week_shape(self):
        today = date.today().isoformat()
        context = self.get_dashboard([{"_id": today, "surveys": 3, "cost": 450.0}])
        self.assertEqual(context["today_surveys"], 3)
        self.assertEqual(context["today_cost_text"], "$450.00")
        self.assertEqual(len(context["week_labels"]), 7)
        self.assertEqual(sum(context["week_survey_counts"]), 3)

    def test_large_cost_uses_short_form(self):
        context = self.get_dashboard([{"_id": date.today().isoformat(), "surveys": 1, "cost": 32400.0}])
        self.assertEqual(context["today_cost_text"], "$32.4k")

    def test_no_surveys_today(self):
        context = self.get_dashboard([])
        self.assertEqual(context["today_surveys"], 0)
        self.assertEqual(context["today_cost_text"], "$0.00")


if __name__ == "__main__":
    unittest.main()
