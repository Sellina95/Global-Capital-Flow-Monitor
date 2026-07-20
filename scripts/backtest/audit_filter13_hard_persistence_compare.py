from pathlib import Path
import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "backtest"
RESULTS = DATA / "results"

ATTR_PATH = RESULTS / "filter13_budget_attribution_final_daily.csv"
MACRO_PATH = DATA / "macro_data.csv"

OUTPUT_DAILY = (
    RESULTS
    / "filter13_hard_persistence_compare_daily.csv"
)

OUTPUT_SUMMARY = (
    RESULTS
    / "filter13_hard_persistence_compare_summary.csv"
)


RAW_COLS = [
    "US10Y",
    "DXY",
    "VIX",
    "WTI",
]


def is_hard(x):
    return str(x).upper().startswith(
        "HARD RISK-OFF"
    )


def direction(curr, prev):

    if pd.isna(curr) or pd.isna(prev):
        return "N/A"

    if curr > prev:
        return "UP"

    if curr < prev:
        return "DOWN"

    return "FLAT"


def classify_trigger(row):

    regime = str(
        row.get(
            "market_regime",
            "",
        )
    ).upper()

    macro = str(
        row.get(
            "macro_narrative",
            "",
        )
    ).upper()

    if macro == "CREDIT_STRESS":
        return "CREDIT_STRESS"

    if (
        "STAGFLATION" in macro
        or "INFLATION SHOCK" in regime
    ):
        return (
            "STAGFLATION_OR_"
            "INFLATION_SHOCK"
        )

    if (
        macro
        == "TIGHTENING_GROWTH_SCARE"
    ):
        return "GROWTH_SCARE_VIX"

    return "OTHER"


def main():

    # ==================================================
    # 1. Load
    # ==================================================

    a = pd.read_csv(
        ATTR_PATH
    )

    m = pd.read_csv(
        MACRO_PATH
    )

    a["date"] = pd.to_datetime(
        a["date"],
        errors="coerce",
    )

    m["date"] = pd.to_datetime(
        m["date"],
        errors="coerce",
    )

    a = (
        a
        .dropna(subset=["date"])
        .sort_values("date")
        .reset_index(drop=True)
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
    # 2. Raw directions
    # ==================================================

    missing = [
        c
        for c in RAW_COLS
        if c not in m.columns
    ]

    if missing:

        raise RuntimeError(
            f"Missing raw columns: "
            f"{missing}"
        )

    for col in RAW_COLS:

        m[
            f"{col}_PREV"
        ] = m[col].shift(1)

        m[
            f"{col}_DIR"
        ] = [

            direction(
                curr,
                prev,
            )

            for curr, prev in zip(
                m[col],
                m[f"{col}_PREV"],
            )
        ]

    raw_keep = ["date"]

    for col in RAW_COLS:

        raw_keep += [
            col,
            f"{col}_DIR",
        ]

    d = a.merge(

        m[raw_keep],

        on="date",

        how="left",

        validate="one_to_one",
    )

    # ==================================================
    # 3. Detect HARD episodes
    #
    # 중요:
    # HARD의 모든 날짜를 비교하지 않는다.
    #
    # 각 episode의 "진입일"만 비교한다.
    #
    # ONE_DAY:
    #   HARD가 정확히 1거래일 지속
    #
    # PERSISTENT:
    #   HARD가 2거래일 이상 지속
    # ==================================================

    episodes = []

    i = 0

    while i < len(d):

        if not is_hard(
            d.iloc[i].get(
                "market_regime"
            )
        ):

            i += 1
            continue

        start = i

        j = i

        while (
            j + 1 < len(d)
            and is_hard(
                d.iloc[
                    j + 1
                ].get(
                    "market_regime"
                )
            )
        ):

            j += 1

        duration = (
            j - start + 1
        )

        entry = d.iloc[start]

        exit_row = (
            d.iloc[j + 1]
            if j + 1 < len(d)
            else None
        )

        episode_type = (

            "ONE_DAY"

            if duration == 1

            else "PERSISTENT"
        )

        row = {

            "episode_type":
                episode_type,

            "duration_days":
                duration,

            "entry_date":
                entry[
                    "date"
                ].strftime(
                    "%Y-%m-%d"
                ),

            "end_date":
                d.iloc[j][
                    "date"
                ].strftime(
                    "%Y-%m-%d"
                ),

            "trigger":
                classify_trigger(
                    entry
                ),

            "entry_regime":
                entry.get(
                    "market_regime"
                ),

            "entry_macro":
                entry.get(
                    "macro_narrative"
                ),

            "entry_hy_oas":
                entry.get(
                    "hy_oas_today"
                ),

            "entry_pre_cap_budget":
                entry.get(
                    "pre_cap_budget"
                ),

            "entry_phase_cap":
                entry.get(
                    "phase_cap"
                ),

            "entry_phase_cut":
                entry.get(
                    "phase_cap_effect"
                ),

            "entry_final_budget":
                entry.get(
                    "final_budget"
                ),

            "exit_regime":
                (
                    exit_row.get(
                        "market_regime"
                    )
                    if exit_row
                    is not None
                    else None
                ),

            "exit_macro":
                (
                    exit_row.get(
                        "macro_narrative"
                    )
                    if exit_row
                    is not None
                    else None
                ),
        }

        for col in RAW_COLS:

            row[
                f"entry_"
                f"{col.lower()}"
            ] = entry.get(
                col
            )

            row[
                f"entry_"
                f"{col.lower()}_dir"
            ] = entry.get(
                f"{col}_DIR"
            )

        episodes.append(
            row
        )

        i = j + 1

    out = pd.DataFrame(
        episodes
    )

    # ==================================================
    # 4. Save daily/episode detail
    # ==================================================

    out.to_csv(
        OUTPUT_DAILY,
        index=False,
    )

    # ==================================================
    # 5. Summary
    # ==================================================

    summary_rows = []

    for group_name in [
        "ONE_DAY",
        "PERSISTENT",
    ]:

        g = out[
            out[
                "episode_type"
            ]
            == group_name
        ]

        if g.empty:
            continue

        summary_rows.append({

            "episode_type":
                group_name,

            "episodes":
                len(g),

            "avg_duration":
                g[
                    "duration_days"
                ].mean(),

            "avg_hy_oas":
                pd.to_numeric(
                    g[
                        "entry_hy_oas"
                    ],
                    errors="coerce",
                ).mean(),

            "avg_phase_cut":
                pd.to_numeric(
                    g[
                        "entry_phase_cut"
                    ],
                    errors="coerce",
                ).mean(),

            "avg_final_budget":
                pd.to_numeric(
                    g[
                        "entry_final_budget"
                    ],
                    errors="coerce",
                ).mean(),

            "vix_up_rate":
                (
                    g[
                        "entry_vix_dir"
                    ]
                    == "UP"
                ).mean(),

            "dxy_up_rate":
                (
                    g[
                        "entry_dxy_dir"
                    ]
                    == "UP"
                ).mean(),

            "us10y_up_rate":
                (
                    g[
                        "entry_us10y_dir"
                    ]
                    == "UP"
                ).mean(),

            "wti_up_rate":
                (
                    g[
                        "entry_wti_dir"
                    ]
                    == "UP"
                ).mean(),
        })

    summary = pd.DataFrame(
        summary_rows
    )

    summary.to_csv(
        OUTPUT_SUMMARY,
        index=False,
    )

    # ==================================================
    # 6. Print
    # ==================================================

    print(
        "\n=== FILTER13 HARD "
        "PERSISTENCE COMPARISON ==="
    )

    print(
        "\n[EPISODES]"
    )

    print(
        out[
            "episode_type"
        ]
        .value_counts()
        .to_string()
    )

    print(
        "\n=== SUMMARY ==="
    )

    print(
        summary.to_string(
            index=False
        )
    )

    print(
        "\n=== TRIGGER × "
        "PERSISTENCE ==="
    )

    print(
        pd.crosstab(
            out["trigger"],
            out[
                "episode_type"
            ],
        ).to_string()
    )

    print(
        "\n=== ONE-DAY "
        "ENTRY DIRECTIONS ==="
    )

    one = out[
        out[
            "episode_type"
        ]
        == "ONE_DAY"
    ]

    for col in RAW_COLS:

        print(
            f"\n{col}"
        )

        print(
            one[
                f"entry_"
                f"{col.lower()}_dir"
            ]
            .value_counts(
                dropna=False
            )
            .to_string()
        )

    print(
        "\n=== PERSISTENT "
        "ENTRY DIRECTIONS ==="
    )

    per = out[
        out[
            "episode_type"
        ]
        == "PERSISTENT"
    ]

    for col in RAW_COLS:

        print(
            f"\n{col}"
        )

        print(
            per[
                f"entry_"
                f"{col.lower()}_dir"
            ]
            .value_counts(
                dropna=False
            )
            .to_string()
        )

    print(
        "\n=== EPISODE DETAIL ==="
    )

    cols = [

        "episode_type",
        "duration_days",

        "entry_date",
        "end_date",

        "trigger",

        "entry_macro",

        "entry_us10y_dir",
        "entry_dxy_dir",
        "entry_vix_dir",
        "entry_wti_dir",

        "entry_hy_oas",

        "entry_phase_cut",
        "entry_final_budget",

        "exit_regime",
        "exit_macro",
    ]

    print(
        out[cols]
        .to_string(
            index=False
        )
    )

    print(
        "\n[SAVED]",
        OUTPUT_DAILY
    )

    print(
        "[SAVED]",
        OUTPUT_SUMMARY
    )

    print(
        "\nAUDIT COMPLETE."
    )

    print(
        "Entry-day information only "
        "was used for comparison."
    )

    print(
        "Do NOT modify production "
        "Filter13 from this audit alone."
    )


if __name__ == "__main__":
    main()