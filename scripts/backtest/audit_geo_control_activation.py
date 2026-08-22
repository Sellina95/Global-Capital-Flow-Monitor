from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import filters.strategist_filters as sf
from scripts.backtest.market_data_builder import build_market_data

DATA = ROOT / "data" / "backtest"

PANELS = {
    "CONTROL_OLD_DATA": (
        DATA / "pit_safe" / "master_panel_geo_control_old_data.csv"
    ),
    "PIT_SAFE_DATA": (
        DATA / "pit_safe" / "master_panel_pit_safe_with_sovereign.csv"
    ),
}

OUT = (
    DATA
    / "results"
    / "geo_control_activation_audit.csv"
)

rows = []

for panel_name, path in PANELS.items():

    if not path.exists():
        raise FileNotFoundError(path)

    panel = pd.read_csv(
        path,
        parse_dates=["date", "signal_date", "execution_date"],
    )

    mask = (
        panel["signal_date"].ge(pd.Timestamp("2008-12-01"))
        & panel["execution_date"].notna()
        & pd.to_numeric(panel["SPY"], errors="coerce").notna()
    )

    indices = panel.index[mask].tolist()

    # Fast activation check only — full-period scan unnecessary here.
    if len(indices) > 100:
        step = max(1, len(indices) // 100)
        indices = indices[::step][:100]

    level_counts = {}
    score_non_null = 0
    sovereign_component_days = 0

    for idx in indices:

        md = build_market_data(
            panel=panel,
            row_index=idx,
            previous_exposure=50.0,
        )

        md = (
            sf.attach_geopolitical_ew_layer(
                md,
                panel,
                idx,
            )
            or md
        )

        geo = md.get("GEO_EW", {}) or {}

        level = str(
            geo.get("level", "N/A")
        ).upper()

        level_counts[level] = (
            level_counts.get(level, 0) + 1
        )

        if geo.get("score") is not None:
            score_non_null += 1

        components = geo.get(
            "components",
            [],
        ) or []

        keys = {
            str(x.get("key"))
            for x in components
            if isinstance(x, dict)
        }

        if keys.intersection({
            "KR10Y_SPREAD",
            "JP10Y_SPREAD",
            "DE10Y_SPREAD",
            "IL10Y_SPREAD",
        }):
            sovereign_component_days += 1

    total = len(indices)

    rows.append({
        "panel": panel_name,
        "rows": total,
        "geo_score_non_null": score_non_null,
        "geo_score_non_null_pct":
            score_non_null / total * 100 if total else 0,
        "sovereign_component_days":
            sovereign_component_days,
        "sovereign_component_pct":
            sovereign_component_days / total * 100 if total else 0,
        "NORMAL": level_counts.get("NORMAL", 0),
        "ELEVATED": level_counts.get("ELEVATED", 0),
        "HIGH": level_counts.get("HIGH", 0),
        "CONFLICT": level_counts.get("CONFLICT", 0),
        "NA": (
            level_counts.get("N/A", 0)
            + level_counts.get("NONE", 0)
        ),
    })

df = pd.DataFrame(rows)

df.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig",
)

print("=" * 90)
print("GEO CONTROL ACTIVATION AUDIT")
print("=" * 90)

print(
    df.to_string(index=False)
)

print()
print("INTERPRETATION")
print("- If geo_score_non_null > 0: GEO actually ran.")
print("- If sovereign_component_days > 0: sovereign spreads actually entered GEO.")
print("- ELEVATED/HIGH/CONFLICT > 0 means GEO overlay had opportunities to cut risk.")
print()
print("[OUTPUT]")
print(OUT)
