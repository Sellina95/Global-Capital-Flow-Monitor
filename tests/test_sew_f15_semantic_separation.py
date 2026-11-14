import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HIST = ROOT / "scripts" / "historical_pm_v2_reconstruction.py"
FILTERS = ROOT / "filters" / "strategist_filters.py"
REPORT = ROOT / "scripts" / "generate_report.py"


class SewF15SemanticSeparationTest(unittest.TestCase):

    def test_historical_reconstruction_does_not_map_sew_to_f15(self):
        text = HIST.read_text(encoding="utf-8")

        forbidden = [
            'put("f15.exposure_control", text, "SEW")',
            '"f15.exposure_control": row["sew_status"]',
            'reason": f"Explicit same-date SEW state:',
            '"reason": "Explicit same-date SEW state: STABLE / NORMAL."',
        ]

        for pattern in forbidden:
            self.assertNotIn(pattern, text)

    def test_f15_uses_separate_control_status_key(self):
        text = FILTERS.read_text(encoding="utf-8")

        self.assertIn(
            'market_data["FILTER15_EXPOSURE_CONTROL_STATUS"] = status',
            text,
        )

    def test_production_sew_status_remains_sew_status(self):
        text = REPORT.read_text(encoding="utf-8")

        self.assertIn(
            'market_data["SEW_STATUS"] = sew_status',
            text,
        )


if __name__ == "__main__":
    unittest.main()
