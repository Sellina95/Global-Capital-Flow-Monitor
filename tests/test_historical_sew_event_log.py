from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_pm_site import load_sew_events_for_report_date


class HistoricalSewEventLogTest(unittest.TestCase):
    def test_0918_binds_only_persisted_deadman_window(self) -> None:
        events = load_sew_events_for_report_date("2026-09-18")

        self.assertEqual(len(events), 2)

        transitions = [event["transition"] for event in events]
        self.assertEqual(transitions, ["CLEARED", "TRIGGERED"])

        trigger = next(
            event for event in events
            if event["transition"] == "TRIGGERED"
        )

        self.assertEqual(
            trigger["timestamp_kst"],
            "2026-09-17T22:34:58+09:00",
        )
        self.assertIn("HARD DEADMAN", trigger["reason"])
        self.assertIn("extreme=3", trigger["reason"])

    def test_0918_diagnostics_card_renders_persisted_events(self) -> None:
        subprocess.run(
            [sys.executable, "scripts/build_pm_site.py"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
        )

        page = (
            ROOT
            / "_site"
            / "history"
            / "2026-09-18-diagnostics.html"
        ).read_text(encoding="utf-8")

        self.assertIn("RECENT SYSTEM ALERTS", page)
        self.assertIn("DEADMAN · TRIGGERED", page)
        self.assertIn("DEADMAN · CLEARED", page)
        self.assertIn("2026-09-17T22:34:58+09:00", page)
        self.assertIn("extreme=3", page)
        self.assertNotIn(
            "Current lifecycle events are not shown on historical reports.",
            page,
        )


if __name__ == "__main__":
    unittest.main()
