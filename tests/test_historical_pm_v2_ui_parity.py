from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_historical_pm_v2_ui_parity import CONTRACT_PATH, audit  # noqa: E402
from scripts.historical_pm_v2_reconstruction import build_population  # noqa: E402


class HistoricalPmV2UiParityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, "scripts/build_pm_site.py"], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        cls.result = audit(ROOT / "_site")
        cls.records = {item["report_date"]: item for item in build_population()}

    def test_authoritative_0912_contract_is_complete(self) -> None:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(contract["authority"]["template_date"], "2026-09-12")
        self.assertEqual(
            contract["counts"]["sections"],
            len(contract["sections"]),
        )
        self.assertEqual(
            contract["counts"]["fields"],
            len(contract["fields"]),
        )

        field_ids = [field_id for field_id, _ in contract["fields"]]

        self.assertIn("confirmation.term_premium", field_ids)

        us10y_index = field_ids.index("confirmation.us10y")
        term_premium_index = field_ids.index(
            "confirmation.term_premium"
        )

        self.assertEqual(
            term_premium_index,
            us10y_index + 1,
        )

    def test_complete_population_has_literal_structural_parity(self) -> None:
        self.assertEqual(self.result["verdict"], "PASS", self.result["issues"][:10])

        expected = len(self.records)
        expected_coverage = f"{expected}/{expected}"

        self.assertEqual(self.result["calendar_dates"], expected)
        self.assertEqual(self.result["reports"], expected)
        self.assertEqual(self.result["structural_parity"], expected_coverage)
        self.assertEqual(self.result["phase_coverage"], expected_coverage)
        self.assertEqual(self.result["f13_f15_f18_structure"], expected_coverage)
        self.assertEqual(self.result["allocation_structure"], expected_coverage)
        self.assertEqual(self.result["f19_structure"], expected_coverage)
        self.assertEqual(
            self.result["macro_market_constraint_structure"],
            expected_coverage,
        )

    def test_known_0828_engine_state_is_not_lost_to_legacy_schema(self) -> None:
        record = self.records["2026-08-28"]
        expected = {
            "decision.regime": "RISK-ON / REFLATION", "f13.risk_budget": "58",
            "f15.recommended_exposure": "52%", "f18.exposure_ceiling": "52.0%",
            "f18.allocated_equity": "50.6%", "f18.tactical_reserve": "1.4%", "f18.cash": "49.4%",
        }
        for key, value in expected.items():
            self.assertEqual(record["fields"][key]["status"], "B")
            self.assertEqual(record["fields"][key]["value"], value)
            self.assertEqual(record["fields"][key]["authority"], "reports/daily_report_2026-08-28.md")
        self.assertEqual(len(record["sector_weights"]), 6)
        self.assertEqual(len(record["execution_rows"]), 6)
        self.assertEqual(len(record["breadth_rows"]), 4)

    def test_unavailable_is_proven_and_never_defaulted(self) -> None:
        self.assertEqual(self.result["fabricated_defaults"], 0)
        for record in self.records.values():
            for item in record["fields"].values():
                if item["status"] == "C":
                    self.assertEqual(item["value"], "Unavailable")
                    self.assertFalse(item["reconstruction_possible"])
                    self.assertGreaterEqual(len(item["sources_checked"]), 3)

    def test_existing_reliability_contracts_stay_closed(self) -> None:
        self.assertEqual(self.result["failure_total"], 0)
        self.assertGreater(self.result["existing_reconstruction_checks"], 0)
        self.assertGreater(self.result["existing_reliability_checks"], 0)


if __name__ == "__main__":
    unittest.main()
