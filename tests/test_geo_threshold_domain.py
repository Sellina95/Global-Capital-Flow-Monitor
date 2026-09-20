import unittest

from filters.strategist_filters import GEO_THRESHOLDS


def classify(score: float) -> str:
    for name, lo, hi in GEO_THRESHOLDS:
        if score >= lo and score < hi:
            return name
    return "N/A"


class TestGeoThresholdDomain(unittest.TestCase):
    def test_complete_domain_coverage(self):
        cases = {
            -100.0: "NORMAL",
            -1.00: "NORMAL",
            -0.77: "NORMAL",
            -0.75: "NORMAL",
            0.00: "NORMAL",
            0.74: "NORMAL",
            0.75: "ELEVATED",
            1.49: "ELEVATED",
            1.50: "HIGH",
            2.49: "HIGH",
            2.50: "CONFLICT",
            100.0: "CONFLICT",
        }

        for score, expected in cases.items():
            with self.subTest(score=score):
                self.assertEqual(classify(score), expected)

    def test_no_finite_score_returns_na(self):
        for score in (-10, -1, -0.77, 0, 0.75, 1.5, 2.5, 10):
            self.assertNotEqual(classify(score), "N/A")


if __name__ == "__main__":
    unittest.main()
