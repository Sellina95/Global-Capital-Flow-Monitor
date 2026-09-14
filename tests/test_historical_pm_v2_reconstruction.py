from __future__ import annotations

import subprocess
import sys
import unittest
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.audit_historical_pm_v2_reconstruction import audit  # noqa: E402
from scripts.historical_pm_v2_reconstruction import FIELD_SPECS, build_population  # noqa: E402


class HistoricalPmV2ReconstructionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, "scripts/build_pm_site.py"], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        cls.result = audit(ROOT / "_site")
        cls.population = build_population()

    def test_full_population_contract_passes(self) -> None:
        self.assertEqual(self.result["verdict"], "PASS", self.result["issues"][:5])
        self.assertEqual(self.result["audited_calendar_dates"], 246)
        self.assertEqual(self.result["pm_v2_surface_coverage"]["total"], 246)

    def test_exact_clock_boundary_never_uses_nearest_date(self) -> None:
        self.assertEqual(self.result["canonical_exact_clock_reports"], 88)
        for record in self.population:
            for field in record["fields"].values():
                if field["status"] == "A":
                    self.assertEqual(field["source_clock"], record["data_as_of"])

    def test_every_inventory_field_has_provenance(self) -> None:
        self.assertEqual(len(FIELD_SPECS), 65)
        for record in self.population:
            self.assertEqual(len(record["fields"]), len(FIELD_SPECS))
            for field in record["fields"].values():
                self.assertIn(field["status"], {"A", "B", "C"})
                self.assertTrue(field["authority_sha256"])

    def test_unavailable_never_carries_default_or_invented_value(self) -> None:
        for record in self.population:
            for field in record["fields"].values():
                if field["status"] == "C":
                    self.assertEqual(field["value"], "Unavailable")

    def test_existing_public_reliability_contract_remains_closed(self) -> None:
        self.assertEqual(self.result["legacy_reliability_v1"]["verdict"], "PASS")
        self.assertEqual(self.result["legacy_reliability_v1"]["failures"], 0)

    def test_unavailable_has_distinct_presentation_semantics(self) -> None:
        for record in self.population:
            if record["source_schema"] == "PM_V2_COMPLETE":
                continue
            page = (ROOT / "_site/history" / f"{record['report_date']}.html").read_text(encoding="utf-8")
            cockpit = page.split('<section class="panel reconstruction-contract"', 1)[0]
            self.assertNotRegex(cockpit, r'class="[^"]*pm-neutral[^"]*"[^>]*>\s*Unavailable\s*<')
            self.assertNotRegex(cockpit, r'[🔴🟢🟡][^<]{0,32}Unavailable')
            for attrs in re.findall(r'<(?:strong|span|b)([^>]*)>\s*Unavailable\s*</(?:strong|span|b)>', cockpit):
                self.assertIn("pm-unavailable", attrs)
                self.assertIn('data-availability="unavailable"', attrs)


if __name__ == "__main__":
    unittest.main()
