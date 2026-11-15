import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILTERS = ROOT / "filters" / "strategist_filters.py"


class InstitutionalFlowSemanticContractTest(unittest.TestCase):

    def test_sew_does_not_modify_core_flow_score(self):
        """
        Institutional Flow measures accumulation/flow evidence.
        SEW is an intraday anomaly monitor and must not add to or
        subtract from the core Institutional Flow score.
        """
        text = FILTERS.read_text(encoding="utf-8")

        forbidden = [
            'if sew_status == "STABLE":\n        flow_score += 1',
            'elif sew_status in ["WATCH", "ALERT"]:\n        flow_score -= 1',
            'reasons.append("No shock yet")',
            'reasons.append("Shock already leaking into tape")',
        ]

        for pattern in forbidden:
            self.assertNotIn(
                pattern,
                text,
                msg=f"SEW still contaminates Institutional Flow score: {pattern}",
            )


if __name__ == "__main__":
    unittest.main()
