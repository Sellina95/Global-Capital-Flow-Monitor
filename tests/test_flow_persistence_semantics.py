import unittest

from scripts.monitor_sew import classify_flow_transition


class FlowPersistenceSemanticsTest(unittest.TestCase):

    def test_same_day_rerun_does_not_increment(self):
        r = classify_flow_transition(
            "CONFIRMED_FLOW", 5, "CONFIRMED_FLOW", 5,
            prev_persistence_days=1,
            prev_observation_date="2026-11-15",
            current_observation_date="2026-11-15",
        )
        self.assertEqual(r["persistence_days"], 1)

    def test_new_observation_day_increments_once(self):
        r = classify_flow_transition(
            "CONFIRMED_FLOW", 5, "CONFIRMED_FLOW", 5,
            prev_persistence_days=1,
            prev_observation_date="2026-11-15",
            current_observation_date="2026-11-16",
        )
        self.assertEqual(r["persistence_days"], 2)

    def test_flow_break_resets_persistence(self):
        r = classify_flow_transition(
            "CONFIRMED_FLOW", 5, "NO CLEAR FLOW", 0,
            prev_persistence_days=4,
            prev_observation_date="2026-11-15",
            current_observation_date="2026-11-16",
        )
        self.assertEqual(r["persistence_days"], 0)

    def test_legacy_state_restarts_from_one(self):
        r = classify_flow_transition(
            "CONFIRMED_FLOW", 5, "CONFIRMED_FLOW", 5,
            prev_persistence_days=99,
            prev_observation_date=None,
            current_observation_date="2026-11-15",
        )
        self.assertEqual(r["persistence_days"], 1)


if __name__ == "__main__":
    unittest.main()
