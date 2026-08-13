from __future__ import annotations

from copy import deepcopy


CONFIRM_DAYS = 3


def step(
    state: dict,
    raw_rank: str,
    raw_weights: dict[str, float],
    today: str,
    deleveraging: bool = False,
) -> tuple[dict, dict[str, float], str]:

    s = deepcopy(state)

    accepted_rank = str(
        s.get("accepted_rank", "") or ""
    )

    accepted_target_weights = (
        s.get("accepted_target_weights", {})
        or {}
    )

    pending_rank = str(
        s.get("pending_rank", "") or ""
    )

    pending_count = int(
        s.get("pending_count", 0) or 0
    )

    last_processed_date = str(
        s.get("last_processed_date", "") or ""
    )

    if deleveraging:

        accepted_rank = raw_rank
        accepted_target_weights = dict(raw_weights)

        pending_rank = ""
        pending_count = 0

        output = dict(raw_weights)
        action = "FORCED_DELEVERAGE_ACCEPT"

    elif not accepted_rank:

        accepted_rank = raw_rank
        accepted_target_weights = dict(raw_weights)

        pending_rank = ""
        pending_count = 0

        output = dict(raw_weights)
        action = "INITIAL_ACCEPT"

    elif raw_rank == accepted_rank:

        accepted_target_weights = dict(raw_weights)

        pending_rank = ""
        pending_count = 0

        output = dict(raw_weights)
        action = "ACCEPTED_RANK_UPDATE"

    else:

        same_day_rerun = (
            last_processed_date == today
        )

        if not same_day_rerun:

            if pending_rank == raw_rank:
                pending_count += 1

            else:
                pending_rank = raw_rank
                pending_count = 1

        if (
            pending_rank == raw_rank
            and pending_count >= CONFIRM_DAYS
        ):

            accepted_rank = raw_rank
            accepted_target_weights = dict(raw_weights)

            pending_rank = ""
            pending_count = 0

            output = dict(raw_weights)
            action = "RANK_CONFIRMED"

        else:

            output = {
                str(k): float(v)
                for k, v
                in accepted_target_weights.items()
            }

            action = "RANK_CHANGE_SUPPRESSED"

    next_state = {
        "accepted_rank":
            accepted_rank,

        "accepted_target_weights":
            dict(accepted_target_weights),

        "pending_rank":
            pending_rank,

        "pending_count":
            pending_count,

        "last_processed_date":
            today,

        "last_output_target_weights":
            dict(output),

        "last_action":
            action,
    }

    return (
        next_state,
        output,
        action,
    )


def main():

    state = {
        "accepted_rank": "",
        "accepted_target_weights": {},
        "pending_rank": "",
        "pending_count": 0,
        "last_processed_date": "",
        "last_output_target_weights": {},
        "last_action": "UNINITIALIZED",
    }

    rank_a = "Technology|Health Care|Financials"
    rank_b = "Health Care|Technology|Financials"

    weights_a = {
        "Technology": 20.0,
        "Health Care": 10.0,
        "Financials": 5.0,
    }

    weights_b = {
        "Technology": 10.0,
        "Health Care": 20.0,
        "Financials": 5.0,
    }

    # 1. Initial
    state, output, action = step(
        state,
        rank_a,
        weights_a,
        "2026-08-10",
    )

    assert action == "INITIAL_ACCEPT"
    assert output == weights_a
    assert state["accepted_rank"] == rank_a

    # 2. New rank day 1
    state, output, action = step(
        state,
        rank_b,
        weights_b,
        "2026-08-11",
    )

    assert action == "RANK_CHANGE_SUPPRESSED"
    assert output == weights_a
    assert state["pending_rank"] == rank_b
    assert state["pending_count"] == 1

    # 3. Same-day rerun — MUST NOT increment
    state2, output2, action2 = step(
        state,
        rank_b,
        weights_b,
        "2026-08-11",
    )

    assert action2 == "RANK_CHANGE_SUPPRESSED"
    assert output2 == weights_a
    assert state2["pending_count"] == 1

    state = state2

    # 4. New rank day 2
    state, output, action = step(
        state,
        rank_b,
        weights_b,
        "2026-08-12",
    )

    assert action == "RANK_CHANGE_SUPPRESSED"
    assert output == weights_a
    assert state["pending_count"] == 2

    # 5. New rank day 3 → confirm
    state, output, action = step(
        state,
        rank_b,
        weights_b,
        "2026-08-13",
    )

    assert action == "RANK_CONFIRMED"
    assert output == weights_b
    assert state["accepted_rank"] == rank_b
    assert state["pending_rank"] == ""
    assert state["pending_count"] == 0

    # 6. Deleveraging bypass
    weights_safe = {
        "Health Care": 5.0,
    }

    state, output, action = step(
        state,
        rank_a,
        weights_safe,
        "2026-08-14",
        deleveraging=True,
    )

    assert action == "FORCED_DELEVERAGE_ACCEPT"
    assert output == weights_safe
    assert state["accepted_rank"] == rank_a
    assert state["pending_rank"] == ""
    assert state["pending_count"] == 0

    print()
    print("FILTER18 RANK3D STATE MACHINE CONTRACT: PASS")
    print()
    print("Validated:")
    print("- INITIAL_ACCEPT")
    print("- Day1 suppression")
    print("- Same-day rerun idempotency")
    print("- Day2 suppression")
    print("- Day3 confirmation")
    print("- Deleveraging immediate bypass")


if __name__ == "__main__":
    main()
