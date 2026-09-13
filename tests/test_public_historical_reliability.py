from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_public_historical_reliability import (  # noqa: E402
    TRANSITIONAL_ALLOWLIST,
    audit,
    schema_is_allowed,
    schema_of,
)


class PublicHistoricalReliabilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(
            [sys.executable, "scripts/build_pm_site.py"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        cls.result = audit(ROOT / "_site")

    def test_full_population_contract_passes(self) -> None:
        self.assertEqual(self.result["verdict"], "PASS", self.result["issues"][:5])
        self.assertEqual(
            self.result["audited_calendar_dates"],
            self.result["audited_reports"],
        )

    def test_all_pre_contract_reports_use_lossless_snapshots(self) -> None:
        population = self.result["rendering_population"]
        schemas = self.result["schema_population"]
        expected_snapshots = sum(
            count for name, count in schemas.items() if name != "PM_V2_COMPLETE"
        )
        self.assertEqual(population["lossless_snapshot_reports"], expected_snapshots)

    def test_new_incomplete_schema_is_rejected(self) -> None:
        self.assertFalse(schema_is_allowed("2026-09-14", "PM_V2_TRANSITIONAL"))
        for allowed_date in TRANSITIONAL_ALLOWLIST:
            self.assertTrue(schema_is_allowed(allowed_date, "PM_V2_TRANSITIONAL"))

    def test_schema_classifier_does_not_promote_partial_pm_view(self) -> None:
        partial = "# Global Capital Flow – Daily PM View\n1. EXECUTIVE VIEW\n"
        self.assertEqual(schema_of(partial), "PM_V2_TRANSITIONAL")


if __name__ == "__main__":
    unittest.main()
