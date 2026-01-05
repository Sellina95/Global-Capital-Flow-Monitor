def generate_daily_report():
    market_data = load_market_data_for_today()
    macro_section = build_macro_signals_section(market_data)
    strategist_section = build_strategist_commentary(market_data)
    
    regime_change = market_regime_filter(market_data)  # Regime 변화 감지
    regime_change_section = f"### Regime Change Detected: {regime_change}"  # 변화 감지 섹션 추가
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    report_text = f"""# 🌍 Global Capital Flow – Daily Brief
**Date:** {today_str}

{macro_section}

---

{strategist_section}

---

{regime_change_section}
"""  
