from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "backtest"
RESULTS = DATA / "results"

ATTR_PATH = RESULTS / "filter13_budget_attribution_final_daily.csv"
MACRO_PATH = DATA / "macro_data.csv"

OUTPUT = RESULTS / "filter13_hard_nextday_raw.csv"


RAW_COLS = [
    "US10Y",
    "DXY",
    "VIX",
    "WTI",
]


def is_hard(x):
    return str(x).upper().startswith("HARD RISK-OFF")


def direction(curr, prev):
    if pd.isna(curr) or pd.isna(prev):
        return "N/A"

    if curr > prev:
        return "UP"

    if curr < prev:
        return "DOWN"

    return "FLAT"


def main():

    # ==================================================
    # 1. Load
    # ==================================================

    a = pd.read_csv(ATTR_PATH)
    m = pd.read_csv(MACRO_PATH)

    a["date"] = pd.to_datetime(
        a["date"],
        errors="coerce",
    )

    m["date"] = pd.to_datetime(
        m["date"],
        errors="coerce",
    )

    m = (
        m
        .dropna(subset=["date"])
        .sort_values("date")
        .drop_duplicates(
            subset=["date"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    # ==================================================
    # 2. Validate required raw columns
    # ==================================================

    missing = [
        c for c in RAW_COLS
        if c not in m.columns
    ]

    if missing:
        raise RuntimeError(
            f"Missing raw columns: {missing}"
        )

    # ==================================================
    # 3. Add raw daily directions
    #
    # IMPORTANT:
    # 관찰용이다.
    # Production regime을 재계산하지 않는다.
    # ==================================================

    for col in RAW_COLS:

        m[f"{col}_PREV"] = m[col].shift(1)

        m[f"{col}_DIR"] = [
            direction(curr, prev)
            for curr, prev in zip(
                m[col],
                m[f"{col}_PREV"],
            )
        ]

    # 필요한 컬럼만 merge
    raw_keep = ["date"]

    for col in RAW_COLS:
        raw_keep += [
            col,
            f"{col}_PREV",
            f"{col}_DIR",
        ]

    x = a.merge(
        m[raw_keep],
        on="date",
        how="left",
        validate="one_to_one",
    )

    # ==================================================
    # 4. Find EXACT one-day HARD episodes
    # ==================================================

    rows = []

    for i in range(len(x)):

        row = x.iloc[i]

        if not is_hard(
            row.get("market_regime")
        ):
            continue

        prev_hard = (
            i > 0
            and is_hard(
                x.iloc[i - 1].get(
                    "market_regime"
                )
            )
        )

        next_hard = (
            i + 1 < len(x)
            and is_hard(
                x.iloc[i + 1].get(
                    "market_regime"
                )
            )
        )

        # 하루짜리 HARD만
        if prev_hard or next_hard:
            continue

        if i + 1 >= len(x):
            next_row = None
        else:
            next_row = x.iloc[i + 1]

        out = {

            "hard_date":
                row["date"].strftime(
                    "%Y-%m-%d"
                ),

            "hard_regime":
                row.get(
                    "market_regime"
                ),

            "hard_macro":
                row.get(
                    "macro_narrative"
                ),

            "hard_phase_cap":
                row.get(
                    "phase_cap"
                ),

            "hard_phase_cut":
                row.get(
                    "phase_cap_effect"
                ),

            "hard_final_budget":
                row.get(
                    "final_budget"
                ),

            "hard_hy_oas":
                row.get(
                    "hy_oas_today"
                ),
        }

        # HARD 당일 raw
        for col in RAW_COLS:

            out[
                f"hard_{col.lower()}"
            ] = row.get(col)

            out[
                f"hard_{col.lower()}_dir"
            ] = row.get(
                f"{col}_DIR"
            )

        # 다음 거래일
        if next_row is not None:

            out["next_date"] = (
                next_row["date"]
                .strftime("%Y-%m-%d")
            )

            out["next_regime"] = (
                next_row.get(
                    "market_regime"
                )
            )

            out["next_macro"] = (
                next_row.get(
                    "macro_narrative"
                )
            )

            out["next_phase_cap"] = (
                next_row.get(
                    "phase_cap"
                )
            )

            out["next_final_budget"] = (
                next_row.get(
                    "final_budget"
                )
            )

            out["next_hy_oas"] = (
                next_row.get(
                    "hy_oas_today"
                )
            )

            for col in RAW_COLS:

                out[
                    f"next_{col.lower()}"
                ] = next_row.get(col)

                out[
                    f"next_{col.lower()}_dir"
                ] = next_row.get(
                    f"{col}_DIR"
                )

                out[
                    f"{col.lower()}_dir_changed"
                ] = (
                    row.get(
                        f"{col}_DIR"
                    )
                    !=
                    next_row.get(
                        f"{col}_DIR"
                    )
                )

        rows.append(out)

    out = pd.DataFrame(rows)

    # ==================================================
    # 5. Save
    # ==================================================

    out.to_csv(
        OUTPUT,
        index=False,
    )

    # ==================================================
    # 6. Print audit
    # ==================================================

    print(
        "\n=== FILTER13 ONE-DAY HARD → NEXT DAY RAW AUDIT ==="
    )

    print("\n[COUNT]")
    print(
        "ONE-DAY HARD:",
        len(out),
    )

    if out.empty:
        print("NONE")
        return

    print(
        "\n=== HARD → NEXT REGIME ==="
    )

    print(
        out["next_regime"]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    print(
        "\n=== HARD → NEXT MACRO ==="
    )

    print(
        out[
            [
                "hard_macro",
                "next_macro",
            ]
        ]
        .value_counts(
            dropna=False
        )
        .to_string()
    )

    print(
        "\n=== RAW DIRECTION CHANGES ==="
    )

    for col in RAW_COLS:

        c = f"{col.lower()}_dir_changed"

        if c in out.columns:

            print(
                f"{col}:",
                int(
                    out[c]
                    .fillna(False)
                    .sum()
                ),
                "/",
                len(out),
                "changed direction",
            )

    print(
        "\n=== DETAIL ==="
    )

    detail_cols = [

        "hard_date",
        "hard_macro",

        "hard_us10y_dir",
        "hard_dxy_dir",
        "hard_vix_dir",
        "hard_wti_dir",
        "hard_hy_oas",

        "hard_phase_cut",
        "hard_final_budget",

        "next_date",
        "next_regime",
        "next_macro",

        "next_us10y_dir",
        "next_dxy_dir",
        "next_vix_dir",
        "next_wti_dir",
        "next_hy_oas",

        "next_final_budget",
    ]

    detail_cols = [
        c for c in detail_cols
        if c in out.columns
    ]

    print(
        out[detail_cols]
        .to_string(
            index=False
        )
    )

    print(
        "\n[SAVED]",
        OUTPUT,
    )

    print(
        "\nAUDIT COMPLETE."
    )

    print(
        "This is a diagnostic audit only."
    )

    print(
        "No production Filter13 logic was modified."
    )


if __name__ == "__main__":
    main()