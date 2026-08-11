from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

RESULT_DIR = ROOT / "data" / "backtest" / "results"
PANEL_PATH = ROOT / "data" / "backtest" / "master_panel.csv"

DETAIL_PATH = (
    RESULT_DIR
    / "filter13_base_budget_calibration_detail.csv"
)

SUMMARY_PATH = (
    RESULT_DIR
    / "filter13_base_budget_calibration_summary.csv"
)

TEXT_PATH = (
    RESULT_DIR
    / "filter13_base_budget_calibration_summary.txt"
)


# ============================================================
# Production Base Budget Contract
# ============================================================

BASE_TO_SENTIMENT = {
    35: "FEAR",
    50: "OTHER",
    55: "NEUTRAL",
    70: "GREED",
}


# ============================================================
# Locate latest compatible Filter13 attribution output
# ============================================================

ATTRIBUTION_CANDIDATES = [
    RESULT_DIR / "filter13_budget_attribution_current_daily.csv",
    RESULT_DIR / "filter13_budget_attribution_final_daily.csv",
    RESULT_DIR / "filter13_budget_audit_daily.csv",
]


def locate_attribution_file() -> Path:

    for path in ATTRIBUTION_CANDIDATES:

        if not path.exists():
            continue

        try:
            sample = pd.read_csv(
                path,
                nrows=5,
            )
        except Exception:
            continue

        required = {
            "date",
            "base_budget",
        }

        if required.issubset(sample.columns):
            return path

    raise FileNotFoundError(
        "Base Budget이 포함된 Filter13 daily attribution 파일을 "
        "찾지 못했습니다.\n\n"
        "Checked:\n"
        + "\n".join(
            str(p)
            for p in ATTRIBUTION_CANDIDATES
        )
    )


# ============================================================
# Helpers
# ============================================================

def forward_return(
    price: pd.Series,
    horizon: int,
) -> pd.Series:

    return (
        price.shift(-horizon)
        / price
        - 1.0
    ) * 100.0


def safe_rate(
    condition: pd.Series,
) -> float:

    if len(condition) == 0:
        return np.nan

    return float(
        condition.mean()
    )


def classify_base_budget(
    x: float,
) -> str:

    if pd.isna(x):
        return "UNKNOWN"

    value = int(round(float(x)))

    return BASE_TO_SENTIMENT.get(
        value,
        f"UNEXPECTED_{value}",
    )


def summarize_group(
    group: pd.DataFrame,
    label: str,
) -> dict:

    r20 = pd.to_numeric(
        group["spy_return_20d"],
        errors="coerce",
    ).dropna()

    r60 = pd.to_numeric(
        group["spy_return_60d"],
        errors="coerce",
    ).dropna()

    return {
        "base_group": label,

        "days":
            len(group),

        "share_of_days":
            len(group),

        "avg_base_budget":
            group["base_budget"].mean(),

        "avg_final_budget":
            group["final_budget"].mean()
            if "final_budget" in group.columns
            else np.nan,

        "avg_base_to_final_change":
            (
                group["final_budget"]
                - group["base_budget"]
            ).mean()
            if "final_budget" in group.columns
            else np.nan,

        # -----------------------------
        # 20D forward outcome
        # -----------------------------

        "avg_spy_20d":
            r20.mean()
            if len(r20)
            else np.nan,

        "median_spy_20d":
            r20.median()
            if len(r20)
            else np.nan,

        "positive_20d_rate":
            safe_rate(r20 > 0),

        "negative_20d_rate":
            safe_rate(r20 < 0),

        "above_5pct_20d_rate":
            safe_rate(r20 >= 5),

        # -----------------------------
        # 60D forward outcome
        # -----------------------------

        "avg_spy_60d":
            r60.mean()
            if len(r60)
            else np.nan,

        "median_spy_60d":
            r60.median()
            if len(r60)
            else np.nan,

        "positive_60d_rate":
            safe_rate(r60 > 0),

        "negative_60d_rate":
            safe_rate(r60 < 0),

        "above_5pct_60d_rate":
            safe_rate(r60 >= 5),

        "above_10pct_60d_rate":
            safe_rate(r60 >= 10),

        "below_minus_5pct_60d_rate":
            safe_rate(r60 <= -5),

        "worst_60d":
            r60.min()
            if len(r60)
            else np.nan,

        "best_60d":
            r60.max()
            if len(r60)
            else np.nan,
    }


# ============================================================
# Main
# ============================================================

def main() -> None:

    attribution_path = locate_attribution_file()

    print(
        f"Using attribution file: "
        f"{attribution_path}"
    )

    audit = pd.read_csv(
        attribution_path
    )

    panel = pd.read_csv(
        PANEL_PATH
    )
    if "signal_date" not in audit.columns and "date" in audit.columns:
        audit = audit.rename(
            columns={"date": "signal_date"}
        )

    # ========================================================
    # Dates
    # ========================================================

    audit["signal_date"] = pd.to_datetime(
        audit["signal_date"],
        errors="coerce",
    )

    panel["signal_date"] = pd.to_datetime(
        panel["signal_date"],
        errors="coerce",
    )

    audit = (
        audit
        .dropna(subset=["signal_date"])
        .sort_values("signal_date")
        .drop_duplicates(
            "signal_date",
            keep="last",
        )
        .reset_index(drop=True)
    )

    panel = (
        panel
        .dropna(subset=["signal_date"])
        .sort_values("signal_date")
        .drop_duplicates(
            "signal_date",
            keep="last",
        )
        .reset_index(drop=True)
    )

    # ========================================================
    # Numeric
    # ========================================================

    audit["base_budget"] = pd.to_numeric(
        audit["base_budget"],
        errors="coerce",
    )

    panel["SPY"] = pd.to_numeric(
        panel["SPY"],
        errors="coerce",
    )

    # ========================================================
    # Locate final Filter13 budget column
    # ========================================================

    possible_final_cols = [
        "production_risk_budget",
        "audit_final_budget",
        "final_budget",
        "risk_budget_13",
    ]

    final_col = None

    for col in possible_final_cols:

        if col in audit.columns:
            final_col = col
            break

    if final_col is not None:

        audit["final_budget"] = pd.to_numeric(
            audit[final_col],
            errors="coerce",
        )

    # ========================================================
    # Forward returns
    #
    # IMPORTANT:
    # These are evaluation labels only.
    # They are NOT used to produce Base Budget.
    # ========================================================

    market = panel[
        [
            "signal_date",
            "SPY",
        ]
    ].copy()

    market["spy_return_20d"] = forward_return(
        market["SPY"],
        20,
    )

    market["spy_return_60d"] = forward_return(
        market["SPY"],
        60,
    )

    df = audit.merge(
        market,
        on="signal_date",
        how="left",
    )

    # ========================================================
    # Base Budget Contract Validation
    # ========================================================

    df["base_budget_rounded"] = (
        df["base_budget"]
        .round()
    )

    df["sentiment_base_state"] = (
        df["base_budget"]
        .apply(
            classify_base_budget
        )
    )

    expected_values = {
        35,
        50,
        55,
        70,
    }

    unexpected_mask = (
        df["base_budget"]
        .notna()
        &
        ~df["base_budget_rounded"]
        .isin(expected_values)
    )

    unexpected_count = int(
        unexpected_mask.sum()
    )

    # ========================================================
    # Low / High Base definitions
    #
    # Research grouping only.
    # Not a proposed production threshold.
    # ========================================================

    df["base_bucket"] = np.select(
        [
            df["base_budget"] <= 35,
            (
                (df["base_budget"] > 35)
                &
                (df["base_budget"] <= 50)
            ),
            (
                (df["base_budget"] > 50)
                &
                (df["base_budget"] <= 55)
            ),
            df["base_budget"] > 55,
        ],
        [
            "VERY_LOW_35",
            "LOW_50",
            "MID_55",
            "HIGH_70",
        ],
        default="UNKNOWN",
    )

    # ========================================================
    # False Conservative / False Aggressive
    # ========================================================

    # Low Base but strong subsequent market
    df["false_conservative_60d_5pct"] = (
        df["base_budget"].le(50)
        &
        df["spy_return_60d"].ge(5)
    )

    df["false_conservative_60d_10pct"] = (
        df["base_budget"].le(50)
        &
        df["spy_return_60d"].ge(10)
    )

    # High Base but subsequent loss
    df["false_aggressive_60d"] = (
        df["base_budget"].ge(70)
        &
        df["spy_return_60d"].lt(0)
    )

    df["false_aggressive_60d_minus5"] = (
        df["base_budget"].ge(70)
        &
        df["spy_return_60d"].le(-5)
    )

    # ========================================================
    # Summary
    # ========================================================

    summary_rows = []

    ordered_groups = [
        "VERY_LOW_35",
        "LOW_50",
        "MID_55",
        "HIGH_70",
    ]

    for label in ordered_groups:

        group = df[
            df["base_bucket"] == label
        ].copy()

        if len(group) == 0:
            continue

        summary_rows.append(
            summarize_group(
                group,
                label,
            )
        )

    summary = pd.DataFrame(
        summary_rows
    )

    if not summary.empty:

        summary["share_of_days"] = (
            summary["days"]
            / summary["days"].sum()
        )

    # ========================================================
    # Overall diagnostics
    # ========================================================

    valid_60 = df[
        df["spy_return_60d"].notna()
    ].copy()

    low_base = valid_60[
        valid_60["base_budget"] <= 50
    ]

    high_base = valid_60[
        valid_60["base_budget"] >= 70
    ]

    false_conservative_5 = int(
        low_base[
            "spy_return_60d"
        ].ge(5).sum()
    )

    false_conservative_10 = int(
        low_base[
            "spy_return_60d"
        ].ge(10).sum()
    )

    false_aggressive = int(
        high_base[
            "spy_return_60d"
        ].lt(0).sum()
    )

    false_aggressive_minus5 = int(
        high_base[
            "spy_return_60d"
        ].le(-5).sum()
    )

    # ========================================================
    # Save
    # ========================================================

    detail_cols = [
        "signal_date",
        "base_budget",
        "sentiment_base_state",
        "base_bucket",
    ]

    if "final_budget" in df.columns:
        detail_cols.append(
            "final_budget"
        )

    detail_cols.extend(
        [
            "SPY",
            "spy_return_20d",
            "spy_return_60d",
            "false_conservative_60d_5pct",
            "false_conservative_60d_10pct",
            "false_aggressive_60d",
            "false_aggressive_60d_minus5",
        ]
    )

    df[
        detail_cols
    ].to_csv(
        DETAIL_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    summary.to_csv(
        SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    # ========================================================
    # Text report
    # ========================================================

    lines = []

    lines.append(
        "=" * 78
    )

    lines.append(
        "FILTER13 BASE BUDGET CALIBRATION AUDIT"
    )

    lines.append(
        "=" * 78
    )

    lines.append(
        f"Source : {attribution_path}"
    )

    lines.append(
        f"Period : "
        f"{df['signal_date'].min().date()} "
        f"~ "
        f"{df['signal_date'].max().date()}"
    )

    lines.append(
        f"Rows   : {len(df):,}"
    )

    lines.append("")

    lines.append(
        f"Average Base Budget : "
        f"{df['base_budget'].mean():.2f}"
    )

    if "final_budget" in df.columns:

        lines.append(
            f"Average Final Budget: "
            f"{df['final_budget'].mean():.2f}"
        )

    lines.append("")

    lines.append(
        "Production Base Contract:"
    )

    lines.append(
        "FEAR=35 / OTHER=50 / "
        "NEUTRAL=55 / GREED=70"
    )

    lines.append("")

    lines.append(
        f"Unexpected Base Values: "
        f"{unexpected_count}"
    )

    lines.append("")

    lines.append(
        "Base Budget Outcome Summary:"
    )

    lines.append(
        summary.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "False Conservative Diagnostics"
    )

    lines.append(
        "--------------------------------"
    )

    lines.append(
        f"Low Base days (<=50): "
        f"{len(low_base):,}"
    )

    lines.append(
        f"Low Base + SPY 60D >= +5% : "
        f"{false_conservative_5:,}"
    )

    lines.append(
        f"Low Base + SPY 60D >= +10%: "
        f"{false_conservative_10:,}"
    )

    if len(low_base):

        lines.append(
            f"False Conservative +5% Rate : "
            f"{false_conservative_5 / len(low_base):.1%}"
        )

        lines.append(
            f"False Conservative +10% Rate: "
            f"{false_conservative_10 / len(low_base):.1%}"
        )

    lines.append("")

    lines.append(
        "False Aggressive Diagnostics"
    )

    lines.append(
        "-----------------------------"
    )

    lines.append(
        f"High Base days (>=70): "
        f"{len(high_base):,}"
    )

    lines.append(
        f"High Base + SPY 60D < 0% : "
        f"{false_aggressive:,}"
    )

    lines.append(
        f"High Base + SPY 60D <= -5%: "
        f"{false_aggressive_minus5:,}"
    )

    if len(high_base):

        lines.append(
            f"False Aggressive Rate: "
            f"{false_aggressive / len(high_base):.1%}"
        )

        lines.append(
            f"Severe False Aggressive Rate: "
            f"{false_aggressive_minus5 / len(high_base):.1%}"
        )

    report = "\n".join(
        lines
    )

    TEXT_PATH.write_text(
        report,
        encoding="utf-8",
    )

    # ========================================================
    # Terminal
    # ========================================================

    print(report)

    print()
    print("Saved:")
    print(DETAIL_PATH)
    print(SUMMARY_PATH)
    print(TEXT_PATH)


if __name__ == "__main__":
    main()