import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PositioningMissingSemanticsTest(unittest.TestCase):

    def test_fetch_failure_is_not_neutral_zero(self):
        text = (ROOT / "scripts/fetch_positioning_data.py").read_text()

        self.assertIn(
            "return None, None, None",
            text,
            "Positioning fetch failure must remain unavailable.",
        )

        self.assertNotIn(
            "모든 fallback ticker 실패 → 0.0 반환",
            text,
        )

    def test_report_attach_preserves_missing_z_scores(self):
        text = (ROOT / "scripts/generate_report.py").read_text()

        for key in ("SP500_POS_Z", "US10Y_POS_Z", "DXY_POS_Z"):
            self.assertIn(
                f'"{key}": None',
                text,
                f"{key} missingness must not default to neutral 0.0.",
            )


if __name__ == "__main__":
    unittest.main()
