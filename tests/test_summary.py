"""Daily summary generation (Cosmos aggregation -> Azure SQL row)."""

import unittest
from unittest.mock import MagicMock, patch

import summary
from tests.helpers import FakeCollection


def fake_connection(existing=False):
    conn = MagicMock()
    conn.cursor.return_value.fetchone.return_value = (1,) if existing else None
    return conn


class GenerateSummaryTest(unittest.TestCase):
    def run_summary(self, conn):
        surveys = FakeCollection(aggregate_results=[
            [{"_id": None, "total_surveys": 2, "total_cost": 300.0}],  # totals
            [{"_id": "Clownfish", "total": 4}],                        # top species
        ])
        equipment = FakeCollection(aggregate_results=[[{"name": "Camera"}, {"name": "Tank"}]])
        collections = {"surveys": surveys, "equipment": equipment}
        with patch.object(summary, "get_sql_connection", return_value=conn), \
                patch.object(summary, "get_collection", side_effect=collections.get):
            return summary.generate_summary("2026-10-15")

    def test_saves_summary(self):
        conn = fake_connection()
        saved, message = self.run_summary(conn)
        self.assertTrue(saved)
        self.assertIn("saved", message)
        insert_args = conn.cursor.return_value.execute.call_args.args[1]
        self.assertEqual(insert_args, ("2026-10-15", 2, 300.0, "Clownfish", "Camera, Tank"))
        conn.commit.assert_called_once()
        conn.close.assert_called_once()

    def test_duplicate_date_is_not_saved(self):
        conn = fake_connection(existing=True)
        saved, message = self.run_summary(conn)
        self.assertFalse(saved)
        self.assertIn("already exists", message)
        conn.commit.assert_not_called()
        conn.close.assert_called_once()

    def test_get_summaries_returns_rows(self):
        conn = MagicMock()
        conn.cursor.return_value.fetchall.return_value = [{"summary_date": "2026-10-15"}]
        with patch.object(summary, "get_sql_connection", return_value=conn):
            self.assertEqual(summary.get_summaries(), [{"summary_date": "2026-10-15"}])
        conn.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
