def generate_pm_final_brief(market_data):
    """
    Daily PM View — presentation / observability layer only.

    Contract:
    - Does NOT create market states, portfolio rules, or trading signals.
    - Does NOT modify F13 / F15 / F18 / FINAL_STATE / FINAL_DECISION.
    - Canonical engine outputs are rendered as-is.
    - Market observations may be calculated for display only.
    - Missing != Neutral.
    - Stale != Current.
    """

    lines = []

    # ==================================================
    # Canonical contracts
    # ==================================================

    final_state = market_data.get("FINAL_STATE", {}) or {}
    final_decision = market_data.get("FINAL_DECISION", {}) or {}
    final_action = market_data.get("FINAL_ACTION", {}) or {}

    phase = final_state.get("phase", "N/A")
    structure = final_state.get("structure_tag", "N/A")
    flow_state = final_state.get("flow_state", "N/A")
    drift_state = final_state.get("drift_state", "N/A")
    liquidity_dir = final_state.get("liquidity_dir", "N/A")
    macro_narrative = final_state.get("macro_narrative", "N/A")

    pos_z = final_state.get("pos_z")
    credit_calm = final_state.get("credit_calm")

    action = final_decision.get("action", "N/A")
    exposure = final_decision.get("exposure", "N/A")

    tactical_action = final_action.get("action", "N/A")
    tactical_size = final_action.get("size", "N/A")
    tactical_confidence = final_action.get("confidence", "N/A")
    tactical_reasons = final_action.get("reason", []) or []

    geo_level = (
        market_data.get("WARNING_SIGNALS", {}) or {}
    ).get("geo_level", "N/A")

    cross_asset = final_state.get("cross_asset_tape", {}) or {}

    us10y_dir = cross_asset.get("US10Y_DIR")
    dxy_dir = cross_asset.get("DXY_DIR")
    vix_dir = cross_asset.get("VIX_DIR")
    wti_dir = cross_asset.get("WTI_DIR")

    hy_oas_status = cross_asset.get("HY_OAS_STATUS")
    if hy_oas_status is None:
        hy_oas_status = "N/A"
    else:
        hy_oas_status = str(hy_oas_status).upper()

    # ==================================================
    # Helpers — rendering only
    # ==================================================

    def fmt_value(value, decimals=2):
        if value is None:
            return "N/A"
        try:
            return f"{float(value):.{decimals}f}"
        except (TypeError, ValueError):
            return str(value)

    def fmt_pct(value):
        if value is None:
            return "N/A"
        try:
            return f"{float(value):+.2%}"
        except (TypeError, ValueError):
            return "N/A"

    def render_direction(value, up_text, down_text):
        if value == 1:
            return f"↑ {up_text}"
        if value == -1:
            return f"↓ {down_text}"
        return "⚪ No canonical signal"

    def render_liquidity(value):
        if value == "UP":
            return "↑ Improving"
        if value == "DOWN":
            return "↓ Tightening"
        return "⚪ No canonical signal"

    def render_credit(value):
        if value is True:
            return "Calm"
        if value is False:
            return "Not calm"
        return "⚪ No canonical signal"

    def safe_relative(today_a, prev_a, today_b, prev_b):
        values = (today_a, prev_a, today_b, prev_b)

        if any(v is None for v in values):
            return None

        try:
            today_a = float(today_a)
            prev_a = float(prev_a)
            today_b = float(today_b)
            prev_b = float(prev_b)

            if prev_a == 0 or prev_b == 0:
                return None

            return (
                (today_a / prev_a - 1.0)
                - (today_b / prev_b - 1.0)
            )
        except (TypeError, ValueError, ZeroDivisionError):
            return None

    def append_rotation_observation(
        label,
        today_a,
        prev_a,
        prev2_a,
        today_b,
        prev_b,
        prev2_b,
    ):
        today_rel = safe_relative(
            today_a, prev_a, today_b, prev_b
        )

        previous_rel = safe_relative(
            prev_a, prev2_a, prev_b, prev2_b
        )

        if today_rel is None:
            lines.append(f"{label:<18} N/A")
            return

        if previous_rel is None:
            lines.append(
                f"{label:<18} Today {fmt_pct(today_rel)} | Change N/A"
            )
            return

        change = today_rel - previous_rel

        lines.append(
            f"{label:<18} "
            f"Today {fmt_pct(today_rel)} | "
            f"Prev {fmt_pct(previous_rel)} | "
            f"Δ {fmt_pct(change)}"
        )

    # ==================================================
    # Header
    # ==================================================

    lines.append("GLOBAL CAPITAL FLOW MONITOR")
    lines.append("DAILY PM VIEW")
    lines.append("")

    # ==================================================
    # Portfolio stance
    # ==================================================

    lines.append("PORTFOLIO STANCE")
    lines.append(f"{action} · {exposure}%")
    lines.append("")

    lines.append("REGIME")
    lines.append(str(phase))
    lines.append("")

    lines.append("CONVICTION")
    lines.append(str(tactical_confidence))
    lines.append("")

    # ==================================================
    # Executive View
    # ==================================================

    lines.append("1. EXECUTIVE VIEW")

    liquidity_text = render_liquidity(liquidity_dir)
    credit_text = render_credit(credit_calm)

    lines.append(
        f"The current strategic phase is {phase}. "
        f"Liquidity is {liquidity_text}, while flow is {flow_state}. "
        f"Positioning Z is {fmt_value(pos_z)} and credit is {credit_text}. "
        f"The canonical portfolio decision is {action} with an "
        f"{exposure}% exposure ceiling."
    )
    lines.append(
        f"Macro Narrative      {macro_narrative}"
    )
    lines.append(
        f"Tactical Signal      {tactical_action} / {tactical_size}"
    )
    lines.append("")

    # ==================================================
    # Market State
    # ==================================================

    lines.append("2. MARKET STATE")
    lines.append(f"Liquidity            {render_liquidity(liquidity_dir)}")
    lines.append(f"Flow                 {flow_state}")
    lines.append(f"Structure            {structure}")
    lines.append(f"Drift                {drift_state}")
    lines.append(f"Positioning Z        {fmt_value(pos_z)}")
    lines.append(f"Credit               {render_credit(credit_calm)}")
    lines.append("")

    # ==================================================
    # What Matters Today
    #
    # No renderer-generated thesis.
    # This is a compact display of existing state.
    # ==================================================

    # ==================================================
    # Cross-Asset Tape
    # ==================================================

    lines.append("3. CROSS-ASSET CONFIRMATION")

    # --------------------------------------------------
    # Factual market observations for PM display.
    #
    # Display bands below are PRESENTATION-ONLY.
    # They do NOT feed F13 / F15 / F18 or alter any
    # canonical engine state.
    # --------------------------------------------------

    def _obs(name):
        obj = market_data.get(name, {}) or {}
        if not isinstance(obj, dict):
            return None, None
        return obj.get("today"), obj.get("pct_change")

    def _float_or_none(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _pct_display(value):
        value = _float_or_none(value)
        if value is None:
            return "N/A"
        return f"{value:+.2f}%"

    def _us10y_band(value):
        value = _float_or_none(value)
        if value is None:
            return "⚪"
        if value > 4.5:
            return "🔴"
        if value >= 4.0:
            return "🟡"
        return "🟢"

    def _dxy_band(value):
        value = _float_or_none(value)
        if value is None:
            return "⚪"
        if value > 105:
            return "🔴"
        if value >= 100:
            return "🟡"
        return "🟢"

    def _vix_band(value):
        value = _float_or_none(value)
        if value is None:
            return "⚪"
        if value > 25:
            return "🔴"
        if value >= 20:
            return "🟡"
        return "🟢"

    def _hy_band(value):
        value = _float_or_none(value)
        if value is None:
            return "⚪"
        if value > 5.0:
            return "🔴"
        if value >= 4.0:
            return "🟡"
        return "🟢"

    us10y_today, us10y_change = _obs("US10Y")
    dxy_today, dxy_change = _obs("DXY")
    wti_today, wti_change = _obs("WTI")
    vix_today, vix_change = _obs("VIX")
    hy_today, hy_change = _obs("HY_OAS")

    us10y_value = _float_or_none(us10y_today)
    dxy_value = _float_or_none(dxy_today)
    wti_value = _float_or_none(wti_today)
    vix_value = _float_or_none(vix_today)
    hy_value = _float_or_none(hy_today)

    lines.append("Equities             ⚪ No canonical PM state")

    if us10y_value is not None:
        lines.append(
            f"US10Y Yield          "
            f"{_us10y_band(us10y_value)} {us10y_value:.2f}% · "
            f"{render_direction(us10y_dir, 'Rising', 'Falling')} "
            f"({_pct_display(us10y_change)})"
        )
    else:
        lines.append(
            f"US10Y Yield          ⚪ N/A · "
            f"{render_direction(us10y_dir, 'Rising', 'Falling')}"
        )

    if dxy_value is not None:
        lines.append(
            f"USD                  "
            f"{_dxy_band(dxy_value)} {dxy_value:.2f} · "
            f"{render_direction(dxy_dir, 'Stronger', 'Weaker')} "
            f"({_pct_display(dxy_change)})"
        )
    else:
        lines.append(
            f"USD                  ⚪ N/A · "
            f"{render_direction(dxy_dir, 'Stronger', 'Weaker')}"
        )

    if wti_value is not None:
        lines.append(
            f"Oil                  "
            f"${wti_value:.2f} · "
            f"{render_direction(wti_dir, 'Rising', 'Falling')} "
            f"({_pct_display(wti_change)})"
        )
    else:
        lines.append(
            f"Oil                  N/A · "
            f"{render_direction(wti_dir, 'Rising', 'Falling')}"
        )

    if vix_value is not None:
        lines.append(
            f"Volatility           "
            f"{_vix_band(vix_value)} {vix_value:.2f} · "
            f"{render_direction(vix_dir, 'Rising', 'Falling')} "
            f"({_pct_display(vix_change)})"
        )
    else:
        lines.append(
            f"Volatility           ⚪ N/A · "
            f"{render_direction(vix_dir, 'Rising', 'Falling')}"
        )

    if hy_value is not None:
        lines.append(
            f"HY OAS               "
            f"{_hy_band(hy_value)} {hy_value:.2f}% · "
            f"{hy_oas_status} ({_pct_display(hy_change)})"
        )
    else:
        lines.append(f"HY OAS               ⚪ N/A · {hy_oas_status}")

    lines.append("")

    # ==================================================
    # Leadership & Rotation
    # ==================================================

    lines.append("4. LEADERSHIP & PARTICIPATION")
    lines.append("")

    # --------------------------------------------------
    # Today's Sector Leaders
    #
    # PM_SECTOR_SNAPSHOT is factual observability only:
    # 1D sector return and 1D relative return vs SPY.
    #
    # Missing sectors are NOT treated as neutral.
    # --------------------------------------------------

    lines.append("Today's Sector Leaders")

    sector_snapshot = market_data.get("PM_SECTOR_SNAPSHOT", []) or []

    sector_names = {
        "XLK": "Technology",
        "XLF": "Financials",
        "XLE": "Energy",
        "XLI": "Industrials",
        "XLB": "Materials",
        "XLY": "Consumer Discretionary",
        "XLP": "Consumer Staples",
        "XLV": "Health Care",
        "XLU": "Utilities",
        "XLRE": "Real Estate",
        "XLC": "Communication Services",
    }

    expected_sector_count = len(sector_names)
    observed_sector_count = len(sector_snapshot)

    lines.append(
        f"Coverage             "
        f"{observed_sector_count}/{expected_sector_count} "
        f"· same-date observations only"
    )

    if not sector_snapshot:
        lines.append("⚪ No same-date sector observations available")

    else:
        lines.append(
            "Rank  Sector                     "
            "1D Return   vs SPY     Momentum"
        )

        for row in sector_snapshot:
            ticker = row.get("ticker", "N/A")
            rank = row.get("rank", "-")

            sector_return = row.get(
                "sector_return_1d",
                row.get("return_1d"),
            )

            relative_return = row.get(
                "relative_return_1d",
                row.get("relative_1d"),
            )

            momentum = row.get(
                "momentum_score",
                row.get("momentum"),
            )

            name = sector_names.get(ticker, ticker)

            momentum_display = (
                "N/A"
                if momentum is None
                else str(momentum)
            )

            lines.append(
                f"{str(rank):>4}  "
                f"{name:<25} "
                f"{fmt_pct(sector_return):>9}   "
                f"{fmt_pct(relative_return):>9}   "
                f"{momentum_display:>8}"
            )

    lines.append("")

    # --------------------------------------------------
    # Breadth & Leadership
    # Raw relative-performance observations only.
    # No BUY/SELL or rally-quality classification.
    # --------------------------------------------------

    lines.append("Breadth & Leadership")

    rsp = market_data.get("BREADTH_RSP")
    rsp_prev = market_data.get("BREADTH_RSP_PREV")
    rsp_prev2 = market_data.get("BREADTH_RSP_PREV2")

    spy = market_data.get("BREADTH_SPY")
    spy_prev = market_data.get("BREADTH_SPY_PREV")
    spy_prev2 = market_data.get("BREADTH_SPY_PREV2")

    qqqe = market_data.get("BREADTH_QQQE")
    qqqe_prev = market_data.get("BREADTH_QQQE_PREV")
    qqqe_prev2 = market_data.get("BREADTH_QQQE_PREV2")

    qqq = market_data.get("BREADTH_QQQ")
    qqq_prev = market_data.get("BREADTH_QQQ_PREV")
    qqq_prev2 = market_data.get("BREADTH_QQQ_PREV2")

    smh = market_data.get("LEAD_SMH")
    smh_prev = market_data.get("LEAD_SMH_PREV")
    smh_prev2 = market_data.get("LEAD_SMH_PREV2")

    iwm = market_data.get("LEAD_IWM")
    iwm_prev = market_data.get("LEAD_IWM_PREV")
    iwm_prev2 = market_data.get("LEAD_IWM_PREV2")

    append_rotation_observation(
        "RSP vs SPY",
        rsp, rsp_prev, rsp_prev2,
        spy, spy_prev, spy_prev2,
    )

    append_rotation_observation(
        "QQQE vs QQQ",
        qqqe, qqqe_prev, qqqe_prev2,
        qqq, qqq_prev, qqq_prev2,
    )

    append_rotation_observation(
        "SMH vs SPY",
        smh, smh_prev, smh_prev2,
        spy, spy_prev, spy_prev2,
    )

    append_rotation_observation(
        "IWM vs SPY",
        iwm, iwm_prev, iwm_prev2,
        spy, spy_prev, spy_prev2,
    )

    lines.append("")

    # ==================================================
    # Portfolio Implication
    #
    # Only existing FINAL_DECISION / FINAL_ACTION.
    # --------------------------------------------------
    # PORTFOLIO ALLOCATION
    # Canonical execution-facing F18 allocation only.
    # No presentation-generated allocation advice.
    # --------------------------------------------------
    pm_allocation = market_data.get("PM_FINAL_ALLOCATION", {}) or {}

    lines.append("")
    lines.append("5. PORTFOLIO ALLOCATION")

    if pm_allocation:
        exposure_ceiling = pm_allocation.get("exposure_ceiling", "N/A")
        allocated_equity = pm_allocation.get("allocated_equity", "N/A")
        tactical_reserve = pm_allocation.get("tactical_reserve", "N/A")
        cash_weight = pm_allocation.get("cash_weight", "N/A")
        sector_weights = pm_allocation.get("sector_weights", {}) or {}

        lines.append(f"Exposure Ceiling      {exposure_ceiling}%")
        lines.append(f"Allocated Equity      {allocated_equity}%")
        lines.append(f"Tactical Reserve      {tactical_reserve}%")
        lines.append(f"Cash                  {cash_weight}%")
        lines.append("")
        lines.append("Sector Allocation")

        positive_weights = []
        for sector, weight in sector_weights.items():
            try:
                w = float(weight)
            except (TypeError, ValueError):
                continue
            if w > 0:
                positive_weights.append((sector, w))

        positive_weights.sort(key=lambda x: x[1], reverse=True)

        if positive_weights:
            for sector, weight in positive_weights:
                lines.append(f"{sector:<24} {weight:.1f}%")
        else:
            lines.append("No positive sector allocation")

        lines.append("")
        lines.append(
            "Note: Tactical Reserve is undeployed capacity within the "
            "Exposure Ceiling and is included in Cash."
        )
    else:
        lines.append("No canonical F18 allocation available.")

    lines.append("")

    # ==================================================
    # Risk & Constraints
    #
    # Presentation of existing canonical / observed state.
    # No renderer-generated risk thresholds.
    # ==================================================

    lines.append("6. RISK & CONSTRAINTS")
    lines.append("Inflation            ⚪ No canonical PM risk state")
    lines.append(f"Liquidity            {render_liquidity(liquidity_dir)}")
    lines.append(f"Positioning Z        {fmt_value(pos_z)}")
    lines.append(f"Credit               {render_credit(credit_calm)}")
    lines.append(f"Geopolitical         {geo_level}")
    lines.append("")

    # ==================================================
    # Decision Rationale
    #
    # FINAL_DECISION / FINAL_ACTION only.
    # ==================================================

    lines.append("7. DECISION RATIONALE")
    lines.append(f"Decision             {action}")
    lines.append(f"Exposure Ceiling     {exposure}%")
    lines.append(f"Tactical Signal      {tactical_action} / {tactical_size}")
    lines.append(f"Conviction           {tactical_confidence}")

    if tactical_reasons:
        lines.append("Rationale")
        for reason in tactical_reasons:
            lines.append(f"- {reason}")
    else:
        lines.append("Rationale")
        lines.append("- No canonical tactical rationale available")

    lines.append("")

    return "\n".join(lines)
