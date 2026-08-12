from __future__ import annotations

import contextlib
import copy
import io
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


# ============================================================
# Path bootstrap
# ============================================================

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"

for path in (ROOT, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


import scripts.backtest.run_backtest as rb
import filters.strategist_filters as sf


# ============================================================
# Paths
# ============================================================

DATA_DIR = ROOT / "data" / "backtest"
RESULT_DIR = DATA_DIR / "results"

PANEL_PATH = DATA_DIR / "master_panel.csv"

ATTR_PATH = (
    RESULT_DIR
    / "filter13_budget_attribution_final_daily.csv"
)

EXISTING_POSITIONS_PATH = (
    RESULT_DIR
    / "daily_positions.csv"
)

DETAIL_PATH = (
    RESULT_DIR
    / "filter13_candidate_full_pipeline_detail.csv"
)

SUMMARY_PATH = (
    RESULT_DIR
    / "filter13_candidate_full_pipeline_summary.csv"
)

TEXT_PATH = (
    RESULT_DIR
    / "filter13_candidate_full_pipeline_summary.txt"
)


LIMITS = [
    15.0,
    20.0,
    25.0,
    30.0,
]


# ============================================================
# Generic helpers
# ============================================================

def find_column(
    df: pd.DataFrame,
    candidates: list[str],
) -> str | None:

    for col in candidates:
        if col in df.columns:
            return col

    return None


def production_clamp(
    x: float,
) -> float:

    if pd.isna(x):
        return np.nan

    return max(
        0,
        min(
            100,
            int(x),
        ),
    )


def portfolio_metrics(
    returns: pd.Series,
) -> dict[str, float]:

    r = pd.to_numeric(
        returns,
        errors="coerce",
    ).dropna()

    if len(r) == 0:

        return {
            "total_return": np.nan,
            "cagr": np.nan,
            "mdd": np.nan,
            "volatility": np.nan,
            "sharpe": np.nan,
        }

    equity = (
        1.0 + r
    ).cumprod()

    total_return = (
        equity.iloc[-1]
        - 1.0
    )

    years = (
        len(r)
        / 252.0
    )

    cagr = (
        equity.iloc[-1] ** (1.0 / years)
        - 1.0
        if years > 0
        else np.nan
    )

    drawdown = (
        equity
        / equity.cummax()
        - 1.0
    )

    std = r.std(ddof=1)

    volatility = (
        std
        * np.sqrt(252.0)
    )

    sharpe = (
        (
            r.mean()
            / std
        )
        * np.sqrt(252.0)
        if std > 0
        else np.nan
    )

    return {
        "total_return":
            total_return * 100.0,

        "cagr":
            cagr * 100.0,

        "mdd":
            drawdown.min() * 100.0,

        "volatility":
            volatility * 100.0,

        "sharpe":
            sharpe,
    }


# ============================================================
# Filter13 candidate
# ============================================================

def calc_candidate_budget(
    row: pd.Series,
    limit: float,
) -> float:

    base = pd.to_numeric(
        row.get(
            "base_budget"
        ),
        errors="coerce",
    )

    macro_delta = pd.to_numeric(
        row.get(
            "macro_delta"
        ),
        errors="coerce",
    )

    pre_cap = pd.to_numeric(
        row.get(
            "pre_cap_budget"
        ),
        errors="coerce",
    )

    phase_cap = pd.to_numeric(
        row.get(
            "phase_cap"
        ),
        errors="coerce",
    )

    v2_cap = pd.to_numeric(
        row.get(
            "v2_cap"
        ),
        errors="coerce",
    )

    if pd.isna(pre_cap):
        return np.nan

    # --------------------------------------------------------
    # Production baseline Phase Cap
    # --------------------------------------------------------

    baseline_after_phase = (
        min(
            pre_cap,
            phase_cap,
        )
        if pd.notna(
            phase_cap
        )
        else pre_cap
    )

    baseline_phase_cut = max(
        pre_cap
        - baseline_after_phase,
        0.0,
    )

    # --------------------------------------------------------
    # Candidate eligibility
    # --------------------------------------------------------

    both_cut = (
        pd.notna(base)
        and round(
            float(base)
        ) == 70
        and pd.notna(
            macro_delta
        )
        and float(
            macro_delta
        ) < 0
        and baseline_phase_cut > 0
    )

    candidate_after_phase = (
        baseline_after_phase
    )

    if both_cut:

        macro_cut_amount = max(
            -float(
                macro_delta
            ),
            0.0,
        )

        allowed_phase_cut = max(
            float(limit)
            - macro_cut_amount,
            0.0,
        )

        candidate_phase_cut = min(
            baseline_phase_cut,
            allowed_phase_cut,
        )

        candidate_after_phase = (
            pre_cap
            - candidate_phase_cut
        )

    # --------------------------------------------------------
    # Reapply v2 cap mechanically
    # --------------------------------------------------------

    candidate_after_v2 = (
        min(
            candidate_after_phase,
            v2_cap,
        )
        if pd.notna(
            v2_cap
        )
        else candidate_after_phase
    )

    return production_clamp(
        candidate_after_v2
    )


# ============================================================
# Filter15 historical normalization
# ============================================================

def normalize_historical_filter15_inputs(
    market_data: dict[str, Any],
) -> None:

    cross_asset_tape = (
        market_data.get(
            "CROSS_ASSET_TAPE",
            {},
        )
        or {}
    )

    if not isinstance(
        cross_asset_tape,
        dict,
    ):
        cross_asset_tape = {}

    vix_z = (
        cross_asset_tape.get(
            "VIX_Z"
        )
    )

    try:

        vix_z = float(
            vix_z
        )

        if pd.isna(
            vix_z
        ):
            vix_z = 0.0

    except (
        TypeError,
        ValueError,
    ):
        vix_z = 0.0

    cross_asset_tape[
        "VIX_Z"
    ] = vix_z

    market_data[
        "CROSS_ASSET_TAPE"
    ] = cross_asset_tape


# ============================================================
# Filter13 budget injection
# ============================================================

def patch_filter13_budget(
    market_data: dict[str, Any],
    candidate_budget: float,
) -> None:

    market_data[
        "RISK_BUDGET"
    ] = float(
        candidate_budget
    )

    final_state = (
        market_data.get(
            "FINAL_STATE",
            {},
        )
        or {}
    )

    if isinstance(
        final_state,
        dict,
    ):

        final_state = copy.deepcopy(
            final_state
        )

        final_state[
            "risk_budget"
        ] = float(
            candidate_budget
        )

        market_data[
            "FINAL_STATE"
        ] = final_state


# ============================================================
# Actual 13 → 15 → 18 execution
# ============================================================

def run_engine_candidate(
    market_data: dict[str, Any],
    previous_exposure: float,
    candidate_budget: float | None,
) -> dict[str, Any]:

    rb.disable_live_side_effects(
        previous_exposure
    )

    rb.neutralize_all_side_effects(
        previous_exposure
    )

    captured: dict[
        str,
        Any,
    ] = {}

    original_builder = (
        sf.build_tactical_allocation
    )

    def capture_allocation(
        *args,
        **kwargs,
    ):

        result = original_builder(
            *args,
            **kwargs,
        )

        captured[
            "allocation"
        ] = result

        return result

    sf.build_tactical_allocation = (
        capture_allocation
    )

    try:

        with contextlib.redirect_stdout(
            io.StringIO()
        ):

            # ------------------------------------------------
            # Filter13 production function
            # ------------------------------------------------

            sf.narrative_engine_filter(
                market_data
            )

            production_budget = (
                market_data.get(
                    "RISK_BUDGET"
                )
            )

            # ------------------------------------------------
            # Candidate Filter13 budget injection
            # ------------------------------------------------

            if (
                candidate_budget
                is not None
                and pd.notna(
                    candidate_budget
                )
            ):

                patch_filter13_budget(
                    market_data,
                    float(
                        candidate_budget
                    ),
                )

            # ------------------------------------------------
            # Historical contract normalization
            # ------------------------------------------------

            normalize_historical_filter15_inputs(
                market_data
            )

            # ------------------------------------------------
            # Filter15 production function unchanged
            # ------------------------------------------------

            exposure_report = (
                sf.volatility_controlled_exposure_filter(
                    market_data
                )
            )

            # ------------------------------------------------
            # Filter18 production function unchanged
            # ------------------------------------------------

            sf.sector_allocation_filter(
                market_data
            )

        allocation = (
            captured.get(
                "allocation"
            )
        )

        if allocation is None:
            raise RuntimeError(
                "Filter18 allocation 결과를 "
                "포착하지 못했습니다."
            )

        deadman_reason = ""
        brake_drivers = ""

        for line in str(
            exposure_report
        ).splitlines():

            clean = (
                line
                .replace(
                    "**",
                    "",
                )
                .strip()
            )

            if clean.startswith(
                "- Reason:"
            ):

                deadman_reason = (
                    clean.split(
                        ":",
                        1,
                    )[1].strip()
                )

            elif clean.startswith(
                "- Brake Drivers:"
            ):

                brake_drivers = (
                    clean.split(
                        ":",
                        1,
                    )[1].strip()
                )

        return {
            "production_budget":
                production_budget,

            "risk_budget":
                market_data.get(
                    "RISK_BUDGET"
                ),

            "exposure_15":
                market_data.get(
                    "RECOMMENDED_EXPOSURE"
                ),

            "allocation":
                allocation,

            "deadman_reason":
                deadman_reason,

            "brake_drivers":
                brake_drivers,
        }

    finally:

        sf.build_tactical_allocation = (
            original_builder
        )


# ============================================================
# Allocation helpers
# ============================================================

def allocation_equity(
    allocation: dict[str, Any],
) -> float:

    for key in [
        "allocated_equity",
        "allocated_equity_18",
        "allocated_exposure",
        "total_allocated_equity",
    ]:

        if key in allocation:

            value = pd.to_numeric(
                allocation.get(
                    key
                ),
                errors="coerce",
            )

            if pd.notna(
                value
            ):
                return float(
                    value
                )

    weights = (
        allocation.get(
            "weights",
            {},
        )
        or {}
    )

    if not isinstance(
        weights,
        dict,
    ):
        return np.nan

    values = []

    for value in weights.values():

        x = pd.to_numeric(
            value,
            errors="coerce",
        )

        if pd.notna(
            x
        ):
            values.append(
                float(
                    x
                )
            )

    if not values:
        return np.nan

    return float(
        sum(
            values
        )
    )


def allocation_cash(
    allocation: dict[str, Any],
) -> float:

    for key in [
        "cash_weight",
        "cash",
        "cash_equivalent",
        "CASH_EQUIVALENT",
    ]:

        if key in allocation:

            value = pd.to_numeric(
                allocation.get(
                    key
                ),
                errors="coerce",
            )

            if pd.notna(
                value
            ):
                return float(
                    value
                )

    return np.nan


# ============================================================
# Existing daily_positions schema adapter
# ============================================================

def prepare_existing_parity_frame(
    existing: pd.DataFrame,
) -> pd.DataFrame:

    out = (
        existing.copy()
    )

    # --------------------------------------------------------
    # Date
    # --------------------------------------------------------

    date_col = find_column(
        out,
        [
            "signal_date",
            "date",
        ],
    )

    if date_col is None:

        raise ValueError(
            "daily_positions.csv에서 날짜 컬럼을 찾지 못했습니다.\n"
            f"Available columns:\n{out.columns.tolist()}"
        )

    out[
        "signal_date"
    ] = pd.to_datetime(
        out[
            date_col
        ],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Filter13
    # --------------------------------------------------------

    rb13_col = find_column(
        out,
        [
            "risk_budget_13",
            "risk_budget",
            "RISK_BUDGET",
        ],
    )

    if rb13_col is None:

        raise ValueError(
            "Filter13 Risk Budget 컬럼을 찾지 못했습니다.\n"
            f"Available columns:\n{out.columns.tolist()}"
        )

    out[
        "_existing_risk_budget_13"
    ] = pd.to_numeric(
        out[
            rb13_col
        ],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Filter15
    # --------------------------------------------------------

    exp15_col = find_column(
        out,
        [
            "exposure_15",
            "recommended_exposure",
            "RECOMMENDED_EXPOSURE",
        ],
    )

    if exp15_col is None:

        raise ValueError(
            "Filter15 Exposure 컬럼을 찾지 못했습니다.\n"
            f"Available columns:\n{out.columns.tolist()}"
        )

    out[
        "_existing_exposure_15"
    ] = pd.to_numeric(
        out[
            exp15_col
        ],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Filter18
    # --------------------------------------------------------

    allocated_col = find_column(
        out,
        [
            "allocated_equity_18",
            "allocated_equity",
            "allocated_exposure",
            "total_allocated_equity",
        ],
    )

    if allocated_col is not None:

        out[
            "_existing_allocated_equity_18"
        ] = pd.to_numeric(
            out[
                allocated_col
            ],
            errors="coerce",
        )

    else:

        weight_cols = [
            col
            for col in out.columns
            if col.startswith(
                "weight__"
            )
        ]

        if not weight_cols:

            raise ValueError(
                "Filter18 allocated equity 컬럼도 없고 "
                "weight__* 컬럼도 없습니다.\n"
                f"Available columns:\n{out.columns.tolist()}"
            )

        weights = (
            out[
                weight_cols
            ]
            .apply(
                pd.to_numeric,
                errors="coerce",
            )
        )

        out[
            "_existing_allocated_equity_18"
        ] = weights.sum(
            axis=1,
            min_count=1,
        )

        print(
            "[PARITY] Filter18 allocated equity reconstructed "
            f"from {len(weight_cols)} weight columns."
        )

    return out[
        [
            "signal_date",
            "_existing_risk_budget_13",
            "_existing_exposure_15",
            "_existing_allocated_equity_18",
        ]
    ].copy()


# ============================================================
# Scenario runner
# ============================================================

def run_scenario(
    panel: pd.DataFrame,
    attr_lookup: dict,
    limit: float | None,
    scenario_name: str,
) -> pd.DataFrame:

    mask = (
        panel[
            "execution_date"
        ].notna()
        &
        pd.to_numeric(
            panel[
                "SPY"
            ],
            errors="coerce",
        ).notna()
    )

    indices = (
        panel.index[
            mask
        ].tolist()
    )

    rows = []

    previous_exposure = 50.0

    flow_memory: dict[
        str,
        Any,
    ] = {
        "flow_state": "N/A",
        "flow_score": 0,
        "persistence_days": 0,
    }

    for count, idx in enumerate(
        indices,
        start=1,
    ):

        signal_date = pd.to_datetime(
            panel.iloc[
                idx
            ][
                "signal_date"
            ]
        )

        market_data = (
            rb.build_market_data(
                panel=panel,
                row_index=idx,
                previous_exposure=(
                    previous_exposure
                ),
            )
        )

        flow_memory = (
            rb.prepare_filter13_execution_state(
                market_data=market_data,
                panel=panel,
                row_index=idx,
                previous_flow_memory=(
                    flow_memory
                ),
            )
        )

        candidate_budget = None

        attr_row = (
            attr_lookup.get(
                signal_date.normalize()
            )
        )

        if (
            limit is not None
            and attr_row is not None
        ):

            candidate_budget = (
                calc_candidate_budget(
                    attr_row,
                    limit,
                )
            )

        result = (
            run_engine_candidate(
                market_data=market_data,
                previous_exposure=(
                    previous_exposure
                ),
                candidate_budget=(
                    candidate_budget
                ),
            )
        )

        allocation = (
            result[
                "allocation"
            ]
        )

        weights = (
            allocation.get(
                "weights",
                {},
            )
            or {}
        )

        allocated_equity = (
            allocation_equity(
                allocation
            )
        )

        cash_weight = (
            allocation_cash(
                allocation
            )
        )

        row = {
            "scenario":
                scenario_name,

            "signal_date":
                signal_date,

            "execution_date":
                panel.iloc[
                    idx
                ][
                    "execution_date"
                ],

            "production_budget_13":
                result[
                    "production_budget"
                ],

            "risk_budget_13":
                result[
                    "risk_budget"
                ],

            "candidate_requested_budget":
                candidate_budget,

            "exposure_15":
                result[
                    "exposure_15"
                ],

            "allocated_equity_18":
                allocated_equity,

            "cash_weight_18":
                cash_weight,

            "deadman_reason":
                result[
                    "deadman_reason"
                ],

            "brake_drivers":
                result[
                    "brake_drivers"
                ],
        }

        if isinstance(
            weights,
            dict,
        ):

            for sector, weight in (
                weights.items()
            ):

                row[
                    f"weight__{sector}"
                ] = weight

        rows.append(
            row
        )

        exposure = (
            result.get(
                "exposure_15"
            )
        )

        if (
            exposure is not None
            and pd.notna(
                exposure
            )
        ):

            previous_exposure = float(
                exposure
            )

        if (
            count % 500
            == 0
        ):

            print(
                f"[{scenario_name}] "
                f"{count:,}/{len(indices):,}"
            )

    return pd.DataFrame(
        rows
    )


# ============================================================
# Portfolio return from Filter18 weights
# ============================================================

def attach_portfolio_returns(
    scenario_df: pd.DataFrame,
    panel: pd.DataFrame,
) -> pd.DataFrame:

    x = (
        scenario_df.copy()
    )

    panel_market = (
        panel
        .sort_values(
            "signal_date"
        )
        .copy()
    )

    weight_cols = [
        col
        for col in x.columns
        if col.startswith(
            "weight__"
        )
    ]

    tickers = [
        col.replace(
            "weight__",
            "",
            1,
        )
        for col in weight_cols
    ]

    available = []

    for ticker in tickers:

        if ticker not in (
            panel_market.columns
        ):
            continue

        panel_market[
            f"_ret__{ticker}"
        ] = (
            pd.to_numeric(
                panel_market[
                    ticker
                ],
                errors="coerce",
            )
            .pct_change()
            .shift(-1)
        )

        available.append(
            ticker
        )

    return_cols = [
        "signal_date"
    ] + [
        f"_ret__{ticker}"
        for ticker in available
    ]

    x = x.merge(
        panel_market[
            return_cols
        ],
        on="signal_date",
        how="left",
    )

    portfolio_returns = []

    for _, row in (
        x.iterrows()
    ):

        total = 0.0
        valid_weight = 0.0

        for ticker in (
            available
        ):

            weight = pd.to_numeric(
                row.get(
                    f"weight__{ticker}"
                ),
                errors="coerce",
            )

            ret = pd.to_numeric(
                row.get(
                    f"_ret__{ticker}"
                ),
                errors="coerce",
            )

            if (
                pd.isna(
                    weight
                )
                or pd.isna(
                    ret
                )
            ):
                continue

            # ------------------------------------------------
            # Support 0.25 and 25.0 weight conventions
            # ------------------------------------------------

            if abs(
                float(
                    weight
                )
            ) > 1.5:

                w = (
                    float(
                        weight
                    )
                    / 100.0
                )

            else:

                w = float(
                    weight
                )

            total += (
                w
                * float(
                    ret
                )
            )

            valid_weight += abs(
                w
            )

        if valid_weight == 0:

            portfolio_returns.append(
                np.nan
            )

        else:

            portfolio_returns.append(
                total
            )

    x[
        "portfolio_return_gross"
    ] = portfolio_returns

    return x


# ============================================================
# Main
# ============================================================

def main() -> None:

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    panel = pd.read_csv(
        PANEL_PATH,
        parse_dates=[
            "date",
            "signal_date",
            "execution_date",
        ],
    )

    attr = pd.read_csv(
        ATTR_PATH
    )

    attr[
        "signal_date"
    ] = pd.to_datetime(
        attr[
            "date"
        ],
        errors="coerce",
    )

    attr = (
        attr
        .dropna(
            subset=[
                "signal_date"
            ]
        )
        .sort_values(
            "signal_date"
        )
        .drop_duplicates(
            "signal_date",
            keep="last",
        )
    )

    attr_lookup = {
        pd.Timestamp(
            row[
                "signal_date"
            ]
        ).normalize():
        row

        for _, row
        in attr.iterrows()
    }

    # ========================================================
    # BASELINE
    # ========================================================

    print()
    print(
        "Running BASELINE full pipeline..."
    )

    baseline = (
        run_scenario(
            panel=panel,
            attr_lookup=attr_lookup,
            limit=None,
            scenario_name="BASELINE",
        )
    )

    # ========================================================
    # Existing daily_positions parity
    # ========================================================

    if not EXISTING_POSITIONS_PATH.exists():

        raise FileNotFoundError(
            EXISTING_POSITIONS_PATH
        )

    existing_raw = pd.read_csv(
        EXISTING_POSITIONS_PATH
    )

    existing = (
        prepare_existing_parity_frame(
            existing_raw
        )
    )

    parity = baseline.merge(
        existing,
        on="signal_date",
        how="inner",
    )

    if parity.empty:

        raise RuntimeError(
            "Baseline과 daily_positions.csv 사이에 "
            "겹치는 signal_date가 없습니다."
        )

    # --------------------------------------------------------
    # Filter13 error
    # --------------------------------------------------------

    parity[
        "err_13"
    ] = (
        pd.to_numeric(
            parity[
                "risk_budget_13"
            ],
            errors="coerce",
        )
        -
        pd.to_numeric(
            parity[
                "_existing_risk_budget_13"
            ],
            errors="coerce",
        )
    )

    # --------------------------------------------------------
    # Filter15 error
    # --------------------------------------------------------

    parity[
        "err_15"
    ] = (
        pd.to_numeric(
            parity[
                "exposure_15"
            ],
            errors="coerce",
        )
        -
        pd.to_numeric(
            parity[
                "_existing_exposure_15"
            ],
            errors="coerce",
        )
    )

    # --------------------------------------------------------
    # Filter18 error
    # --------------------------------------------------------

    parity[
        "err_18"
    ] = (
        pd.to_numeric(
            parity[
                "allocated_equity_18"
            ],
            errors="coerce",
        )
        -
        pd.to_numeric(
            parity[
                "_existing_allocated_equity_18"
            ],
            errors="coerce",
        )
    )

    parity_fail_13 = int(
        (
            parity[
                "err_13"
            ].abs()
            > 1e-9
        ).sum()
    )

    parity_fail_15 = int(
        (
            parity[
                "err_15"
            ].abs()
            > 1e-9
        ).sum()
    )

    parity_fail_18 = int(
        (
            parity[
                "err_18"
            ].abs()
            > 1e-9
        ).sum()
    )

    print()
    print(
        "=" * 80
    )

    print(
        "FULL PIPELINE BASELINE PARITY"
    )

    print(
        "=" * 80
    )

    print(
        f"Overlap Days  : "
        f"{len(parity):,}"
    )

    print(
        f"Filter13 Fail : "
        f"{parity_fail_13:,}"
    )

    print(
        f"Filter15 Fail : "
        f"{parity_fail_15:,}"
    )

    print(
        f"Filter18 Fail : "
        f"{parity_fail_18:,}"
    )

    if (
        parity_fail_13 > 0
        or parity_fail_15 > 0
        or parity_fail_18 > 0
    ):

        print()
        print(
            "STOP — Baseline full-pipeline parity failed."
        )

        print(
            "Candidate results must NOT be interpreted."
        )

        print()

        print(
            "First Filter13 mismatches:"
        )

        print(
            parity.loc[
                parity[
                    "err_13"
                ].abs()
                > 1e-9,
                [
                    "signal_date",
                    "risk_budget_13",
                    "_existing_risk_budget_13",
                    "err_13",
                ],
            ]
            .head(
                10
            )
            .to_string(
                index=False
            )
        )

        print()

        print(
            "First Filter15 mismatches:"
        )

        print(
            parity.loc[
                parity[
                    "err_15"
                ].abs()
                > 1e-9,
                [
                    "signal_date",
                    "exposure_15",
                    "_existing_exposure_15",
                    "err_15",
                ],
            ]
            .head(
                10
            )
            .to_string(
                index=False
            )
        )

        print()

        print(
            "First Filter18 mismatches:"
        )

        print(
            parity.loc[
                parity[
                    "err_18"
                ].abs()
                > 1e-9,
                [
                    "signal_date",
                    "allocated_equity_18",
                    "_existing_allocated_equity_18",
                    "err_18",
                ],
            ]
            .head(
                10
            )
            .to_string(
                index=False
            )
        )

        return

    # ========================================================
    # Candidate scenarios
    # ========================================================

    scenario_frames = [
        baseline
    ]

    for limit in LIMITS:

        name = (
            f"LIMIT_{int(limit)}"
        )

        print()
        print(
            f"Running {name}..."
        )

        candidate = (
            run_scenario(
                panel=panel,
                attr_lookup=attr_lookup,
                limit=limit,
                scenario_name=name,
            )
        )

        scenario_frames.append(
            candidate
        )

    # ========================================================
    # Portfolio returns
    # ========================================================

    processed = []

    for frame in (
        scenario_frames
    ):

        processed.append(
            attach_portfolio_returns(
                scenario_df=frame,
                panel=panel,
            )
        )

    all_detail = pd.concat(
        processed,
        ignore_index=True,
        sort=False,
    )

    # ========================================================
    # Summary
    # ========================================================

    rows = []

    for scenario_name, group in (
        all_detail.groupby(
            "scenario"
        )
    ):

        scenario_metrics = (
            portfolio_metrics(
                group[
                    "portfolio_return_gross"
                ]
            )
        )

        rows.append(
            {
                "scenario":
                    scenario_name,

                "days":
                    len(
                        group
                    ),

                "avg_risk_budget_13":
                    pd.to_numeric(
                        group[
                            "risk_budget_13"
                        ],
                        errors="coerce",
                    ).mean(),

                "avg_exposure_15":
                    pd.to_numeric(
                        group[
                            "exposure_15"
                        ],
                        errors="coerce",
                    ).mean(),

                "avg_allocated_equity_18":
                    pd.to_numeric(
                        group[
                            "allocated_equity_18"
                        ],
                        errors="coerce",
                    ).mean(),

                "avg_cash_18":
                    pd.to_numeric(
                        group[
                            "cash_weight_18"
                        ],
                        errors="coerce",
                    ).mean(),

                **scenario_metrics,
            }
        )

    summary = pd.DataFrame(
        rows
    )

    order = [
        "BASELINE",
        "LIMIT_15",
        "LIMIT_20",
        "LIMIT_25",
        "LIMIT_30",
    ]

    order_map = {
        name: i
        for i, name
        in enumerate(
            order
        )
    }

    summary[
        "_order"
    ] = (
        summary[
            "scenario"
        ]
        .map(
            order_map
        )
    )

    summary = (
        summary
        .sort_values(
            "_order"
        )
        .drop(
            columns=[
                "_order"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # Delta vs baseline
    # ========================================================

    baseline_row = (
        summary.loc[
            summary[
                "scenario"
            ]
            == "BASELINE"
        ]
        .iloc[0]
    )

    for metric in [
        "avg_risk_budget_13",
        "avg_exposure_15",
        "avg_allocated_equity_18",
        "cagr",
        "mdd",
        "sharpe",
    ]:

        summary[
            f"{metric}_delta"
        ] = (
            summary[
                metric
            ]
            -
            baseline_row[
                metric
            ]
        )

    # ========================================================
    # Save
    # ========================================================

    RESULT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(
        SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    all_detail.to_csv(
        DETAIL_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    # ========================================================
    # Report
    # ========================================================

    lines = []

    lines.append(
        "=" * 100
    )

    lines.append(
        "FILTER13 CANDIDATE → FILTER15 → "
        "FILTER18 FULL PIPELINE AUDIT"
    )

    lines.append(
        "=" * 100
    )

    lines.append("")

    lines.append(
        "BASELINE FULL PIPELINE PARITY: PASS"
    )

    lines.append(
        f"Overlap Days  : "
        f"{len(parity):,}"
    )

    lines.append(
        f"Filter13 Fail : "
        f"{parity_fail_13}"
    )

    lines.append(
        f"Filter15 Fail : "
        f"{parity_fail_15}"
    )

    lines.append(
        f"Filter18 Fail : "
        f"{parity_fail_18}"
    )

    lines.append("")

    lines.append(
        summary.to_string(
            index=False
        )
    )

    lines.append("")

    lines.append(
        "Decision Rules:"
    )

    lines.append(
        "1. 13→15→18 baseline parity must PASS."
    )

    lines.append(
        "2. Restored Filter13 budget must survive Filter15."
    )

    lines.append(
        "3. Restored exposure must survive Filter18."
    )

    lines.append(
        "4. CAGR/Sharpe improvement must remain after Filter18."
    )

    lines.append(
        "5. MDD deterioration must remain acceptable."
    )

    lines.append(
        "6. This P&L is gross/pre-cost."
    )

    report = "\n".join(
        lines
    )

    TEXT_PATH.write_text(
        report,
        encoding="utf-8",
    )

    print()
    print(
        report
    )

    print()
    print(
        "Saved:"
    )

    print(
        SUMMARY_PATH
    )

    print(
        DETAIL_PATH
    )

    print(
        TEXT_PATH
    )


if __name__ == "__main__":
    main()