from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

BASE_PANEL = (
    ROOT
    / "data/backtest/pit_safe/"
    / "master_panel_pit_safe_with_sovereign.csv"
)

ALFRED = ROOT / "data/backtest/alfred_vintage_82"

OUT_PANEL = (
    ROOT
    / "data/backtest/pit_safe/"
    / "master_panel_fred_initial_release_counterfactual.csv"
)

OUT_AUDIT = (
    ROOT
    / "data/backtest/results/"
    / "fred_initial_release_counterfactual_panel_audit.txt"
)


# ============================================================
# Helpers
# ============================================================

def load_initial(series_id: str) -> pd.DataFrame:
    path = ALFRED / f"{series_id}_initial_release.json"

    if not path.exists():
        raise FileNotFoundError(path)

    with path.open() as f:
        payload = json.load(f)

    if "error_code" in payload:
        raise RuntimeError(
            f"{series_id}: invalid ALFRED evidence: {payload}"
        )

    obs = payload.get("observations", [])

    rows = []

    for x in obs:
        value = x.get("value")

        if value in (None, "", "."):
            value = np.nan
        else:
            value = float(value)

        rows.append(
            {
                "observation_date": pd.to_datetime(
                    x["date"]
                ).normalize(),
                "available_date": pd.to_datetime(
                    x["realtime_start"]
                ).normalize(),
                "value": value,
            }
        )

    df = pd.DataFrame(rows)

    if df.empty:
        raise RuntimeError(
            f"{series_id}: no initial-release observations"
        )

    df = (
        df.dropna(subset=["value"])
        .sort_values(
            ["available_date", "observation_date"]
        )
        .drop_duplicates(
            subset=["observation_date"],
            keep="first",
        )
        .reset_index(drop=True)
    )

    return df


def build_asof_series(
    calendar: pd.DataFrame,
    source: pd.DataFrame,
    output_name: str,
) -> pd.DataFrame:

    x = source[
        ["available_date", "observation_date", "value"]
    ].copy()

    # If more than one observation becomes available on one day,
    # retain the newest observation known on that day.
    x = (
        x.sort_values(
            ["available_date", "observation_date"]
        )
        .drop_duplicates(
            subset=["available_date"],
            keep="last",
        )
    )

    x = x.rename(
        columns={
            "available_date": "date",
            "value": output_name,
        }
    )

    out = calendar.merge(
        x[["date", output_name]],
        on="date",
        how="left",
    )

    # Only carry information forward AFTER its actual
    # first-available date.
    out[output_name] = (
        pd.to_numeric(
            out[output_name],
            errors="coerce",
        )
        .ffill()
    )

    return out


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 80)
    print("FRED INITIAL-RELEASE COUNTERFACTUAL PANEL")
    print("=" * 80)
    print()
    print(
        "INPUT-ONLY COUNTERFACTUAL — "
        "Production / Backtest decision logic unchanged."
    )
    print()

    panel = pd.read_csv(BASE_PANEL)

    if "date" in panel.columns:
        date_col = "date"
    elif "signal_date" in panel.columns:
        date_col = "signal_date"
    else:
        raise RuntimeError(
            "No date/signal_date column in baseline panel."
        )

    panel[date_col] = pd.to_datetime(
        panel[date_col]
    ).dt.normalize()

    # Work internally with `date`.
    if date_col != "date":
        panel = panel.rename(
            columns={date_col: "date"}
        )

    panel = panel.sort_values("date").reset_index(drop=True)

    calendar = panel[["date"]].drop_duplicates().copy()

    print("Baseline rows:", len(panel))
    print(
        "Window:",
        panel["date"].min().date(),
        "->",
        panel["date"].max().date(),
    )

    # --------------------------------------------------------
    # 1. NFCI
    # --------------------------------------------------------

    nfci_raw = load_initial("NFCI")

    nfci = build_asof_series(
        calendar,
        nfci_raw,
        "FCI_PIT",
    )

    panel = panel.merge(
        nfci,
        on="date",
        how="left",
    )

    for col in [
        "fred_extras__FCI",
        "fred_sector__FCI",
    ]:
        if col not in panel.columns:
            raise RuntimeError(
                f"Missing frozen FCI contract: {col}"
            )

        panel[col] = panel["FCI_PIT"].combine_first(
            pd.to_numeric(
                panel[col],
                errors="coerce",
            )
        )

    panel = panel.drop(columns=["FCI_PIT"])

    # --------------------------------------------------------
    # 2. WTREGEN -> TGA
    # --------------------------------------------------------

    tga_raw = load_initial("WTREGEN")

    tga = build_asof_series(
        calendar,
        tga_raw,
        "TGA_PIT",
    )

    panel = panel.merge(
        tga,
        on="date",
        how="left",
    )

    if "liquidity__TGA" not in panel.columns:
        raise RuntimeError(
            "Missing frozen liquidity__TGA contract."
        )

    panel["liquidity__TGA"] = (
        panel["TGA_PIT"].combine_first(
            pd.to_numeric(
                panel["liquidity__TGA"],
                errors="coerce",
            )
        )
    )

    panel = panel.drop(columns=["TGA_PIT"])

    # --------------------------------------------------------
    # 3. WALCL
    # --------------------------------------------------------

    walcl_raw = load_initial("WALCL")

    walcl = build_asof_series(
        calendar,
        walcl_raw,
        "WALCL_PIT",
    )

    panel = panel.merge(
        walcl,
        on="date",
        how="left",
    )

    if "liquidity__WALCL" not in panel.columns:
        raise RuntimeError(
            "Missing frozen liquidity__WALCL contract."
        )

    panel["liquidity__WALCL"] = (
        panel["WALCL_PIT"].combine_first(
            pd.to_numeric(
                panel["liquidity__WALCL"],
                errors="coerce",
            )
        )
    )

    panel = panel.drop(columns=["WALCL_PIT"])

    # --------------------------------------------------------
    # 4. RRP
    #
    # RRPONTSYD has no ALFRED vintage history.
    # Preserve frozen PIT panel RRP.
    # --------------------------------------------------------

    required_liq = [
        "liquidity__TGA",
        "liquidity__RRP",
        "liquidity__WALCL",
        "liquidity__NET_LIQ",
    ]

    missing = [
        c for c in required_liq
        if c not in panel.columns
    ]

    if missing:
        raise RuntimeError(
            f"Missing liquidity contracts: {missing}"
        )

    for col in required_liq:
        panel[col] = pd.to_numeric(
            panel[col],
            errors="coerce",
        )

    # --------------------------------------------------------
    # 5. Recompute NET_LIQ using frozen production formula
    #
    # NET_LIQ = WALCL - TGA - RRP
    # only when all three parents exist.
    # --------------------------------------------------------

    old_net_liq = panel["liquidity__NET_LIQ"].copy()

    new_net_liq = pd.Series(
        np.nan,
        index=panel.index,
        dtype=float,
    )

    mask = (
        panel["liquidity__TGA"].notna()
        & panel["liquidity__RRP"].notna()
        & panel["liquidity__WALCL"].notna()
    )

    new_net_liq.loc[mask] = (
        panel.loc[mask, "liquidity__WALCL"]
        - panel.loc[mask, "liquidity__TGA"]
        - panel.loc[mask, "liquidity__RRP"]
    )

    panel["liquidity__NET_LIQ"] = new_net_liq

    # --------------------------------------------------------
    # Audit statistics
    # --------------------------------------------------------

    def changed(a, b, tol=1e-12):
        a = pd.to_numeric(a, errors="coerce")
        b = pd.to_numeric(b, errors="coerce")

        both_nan = a.isna() & b.isna()

        same = (
            np.isclose(
                a.fillna(0.0),
                b.fillna(0.0),
                atol=tol,
                rtol=0.0,
            )
            & (a.isna() == b.isna())
        )

        return ~(both_nan | same)

    original = pd.read_csv(BASE_PANEL)

    original_date_col = (
        "date"
        if "date" in original.columns
        else "signal_date"
    )

    original[original_date_col] = pd.to_datetime(
        original[original_date_col]
    ).dt.normalize()

    if original_date_col != "date":
        original = original.rename(
            columns={original_date_col: "date"}
        )

    original = original.sort_values("date").reset_index(drop=True)

    if len(original) != len(panel):
        raise RuntimeError(
            "Counterfactual panel row count changed."
        )

    audit_rows = []

    for col in [
        "fred_extras__FCI",
        "fred_sector__FCI",
        "liquidity__TGA",
        "liquidity__WALCL",
    ]:
        n = int(
            changed(
                original[col],
                panel[col],
            ).sum()
        )

        audit_rows.append(
            f"{col} changed rows: {n}"
        )

    net_changed = int(
        changed(
            old_net_liq,
            panel["liquidity__NET_LIQ"],
        ).sum()
    )

    audit_rows.append(
        f"liquidity__NET_LIQ changed rows: {net_changed}"
    )

    # --------------------------------------------------------
    # Save separate counterfactual panel
    # --------------------------------------------------------

    OUT_PANEL.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUT_AUDIT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    panel.to_csv(
        OUT_PANEL,
        index=False,
    )

    lines = [
        "FRED INITIAL-RELEASE COUNTERFACTUAL PANEL",
        "=" * 80,
        "",
        "Purpose:",
        (
            "Replace confirmed material revised FRED inputs "
            "with values actually available at the time."
        ),
        "",
        "Decision logic modified: NO",
        "Baseline panel overwritten: NO",
        "",
        "Counterfactual sources:",
        "NFCI -> fred_extras__FCI / fred_sector__FCI",
        "WTREGEN -> liquidity__TGA",
        "WALCL -> liquidity__WALCL",
        "RRPONTSYD -> unchanged (no ALFRED vintage history)",
        "",
        "Derived formula:",
        "NET_LIQ = WALCL - TGA - RRP",
        "",
        *audit_rows,
        "",
        f"Rows: {len(panel)}",
        (
            f"Window: {panel['date'].min().date()} "
            f"-> {panel['date'].max().date()}"
        ),
        "",
        f"Output: {OUT_PANEL}",
    ]

    OUT_AUDIT.write_text(
        "\n".join(lines) + "\n"
    )

    print()
    print("=" * 80)
    print("COUNTERFACTUAL PANEL BUILT")
    print("=" * 80)

    for x in audit_rows:
        print(x)

    print()
    print("Saved:", OUT_PANEL)
    print("Audit:", OUT_AUDIT)


if __name__ == "__main__":
    main()
