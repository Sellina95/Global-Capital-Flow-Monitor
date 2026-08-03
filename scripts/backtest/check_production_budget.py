from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.generate_report import (
    load_macro_df,
    merge_sovereign_spreads_into_macro_df,
    build_market_data,
    attach_liquidity_layer,
    attach_credit_spread_layer,
    attach_fred_extras_layer,
    attach_sovereign_spread_layer,
    attach_breadth_layer,
    attach_sentiment_proxy_layer,
    attach_sector_momentum_layer,
    attach_drift_data_layer,
    attach_growth_sustainability_layer,
    attach_leadership_layer,
    attach_positioning_layer,
    attach_expectation_layer,
    attach_geopolitical_ew_layer,
    attach_country_risk_layer,
    attach_geo_similarity_layer,
)

from filters.strategist_filters import narrative_engine_filter


df = load_macro_df()
df = merge_sovereign_spreads_into_macro_df(df)

idx = df.index[df["date"] == "2008-12-02"][0]

market_data = build_market_data(df, idx)

market_data = attach_liquidity_layer(market_data) or market_data
market_data = attach_credit_spread_layer(market_data) or market_data
market_data = attach_fred_extras_layer(market_data) or market_data
market_data = attach_sovereign_spread_layer(market_data) or market_data
market_data = attach_breadth_layer(market_data, df, idx) or market_data
market_data = attach_sentiment_proxy_layer(market_data) or market_data
market_data = attach_sector_momentum_layer(market_data, df, idx) or market_data
market_data = attach_drift_data_layer(market_data) or market_data
market_data = attach_growth_sustainability_layer(market_data, df, idx) or market_data
market_data = attach_leadership_layer(market_data, df, idx) or market_data
market_data = attach_positioning_layer(market_data) or market_data
market_data = attach_expectation_layer(market_data) or market_data
market_data = attach_geopolitical_ew_layer(market_data, df, idx) or market_data
market_data = attach_country_risk_layer(market_data, df, idx) or market_data
market_data = attach_geo_similarity_layer(market_data) or market_data

narrative_engine_filter(market_data)

print("RISK_BUDGET =", market_data.get("RISK_BUDGET"))