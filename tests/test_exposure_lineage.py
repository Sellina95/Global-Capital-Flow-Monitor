import unittest

from filters.strategist_filters import apply_geo_overlay_to_final_state


class TestExposureLineage(unittest.TestCase):

    def test_geo_constraint_preserves_f15_base_and_records_adjusted_exposure(self):
        market_data = {
            "RECOMMENDED_EXPOSURE": 60.0,
            "F15_RECOMMENDED_EXPOSURE": 60.0,
            "FINAL_STATE": {
                "VIX": 25.0,
                "risk_budget": 60,
                "risk_action": "HOLD",
            },
            "GEO_EW": {
                "level": "HIGH",
                "score": 2.0,
            },
            "_STALE": False,
        }

        apply_geo_overlay_to_final_state(market_data)

        self.assertEqual(market_data["F15_RECOMMENDED_EXPOSURE"], 60.0)
        self.assertEqual(market_data["GEO_BASE_F15_EXPOSURE"], 60.0)
        self.assertEqual(market_data["GEO_ADJUSTED_EXPOSURE"], 40.0)
        self.assertEqual(market_data["RECOMMENDED_EXPOSURE"], 40.0)

    def test_geo_watch_only_does_not_change_executable_exposure(self):
        market_data = {
            "RECOMMENDED_EXPOSURE": 60.0,
            "F15_RECOMMENDED_EXPOSURE": 60.0,
            "FINAL_STATE": {
                "risk_budget": 60,
                "risk_action": "HOLD",
            },
            "GEO_EW": {
                "level": "HIGH",
                "score": 2.0,
            },
            "_STALE": False,
        }

        apply_geo_overlay_to_final_state(market_data)

        self.assertEqual(market_data["F15_RECOMMENDED_EXPOSURE"], 60.0)
        self.assertEqual(market_data["GEO_BASE_F15_EXPOSURE"], 60.0)
        self.assertEqual(market_data["GEO_ADJUSTED_EXPOSURE"], 60.0)
        self.assertEqual(market_data["RECOMMENDED_EXPOSURE"], 60.0)
        self.assertEqual(market_data["GEO_OVERLAY"]["status"], "WATCH_ONLY")

    def test_sew_alone_cannot_confirm_geo_transmission(self):
        market_data = {
            "RECOMMENDED_EXPOSURE": 60.0,
            "F15_RECOMMENDED_EXPOSURE": 60.0,
            "FINAL_STATE": {
                "risk_budget": 60,
                "risk_action": "HOLD",
            },
            "GEO_EW": {
                "level": "HIGH",
                "score": 2.0,
            },
            "SEW_STATUS": "DEADMAN",
            "_STALE": False,
        }

        apply_geo_overlay_to_final_state(market_data)

        self.assertEqual(market_data["RECOMMENDED_EXPOSURE"], 60.0)
        self.assertEqual(market_data["GEO_ADJUSTED_EXPOSURE"], 60.0)
        self.assertFalse(
            market_data["GEO_OVERLAY"]["transmission_confirmed"]
        )
        self.assertEqual(market_data["GEO_OVERLAY"]["status"], "WATCH_ONLY")


if __name__ == "__main__":
    unittest.main()
