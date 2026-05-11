# filters/growth_sustainability.py

def growth_sustainability_filter(market_data, final_state):
    us10y = market_data.get("US10Y", 0)
    real = market_data.get("DFII10", 0)
    curve = market_data.get("T10Y2Y", 0)
    oil = market_data.get("WTI", 0)
    dxy = market_data.get("DXY", 0)
    liq_dir = final_state.get("liquidity_dir", "→")
    credit_calm = final_state.get("credit_calm", True)

    demand = 0
    financing = 0
    energy = 0
    policy = 0

    # Demand proxy (drift + DXY)
    if final_state.get("drift_label") in ["DISINFLATION_RISK_ON", "EARLY_RISK_ON"]:
        demand += 2
    if dxy < 103:
        demand += 1
    elif dxy > 106:
        demand -= 1

    # Financing
    if us10y < 4.5:
        financing += 1
    else:
        financing -= 1

    if real < 2.0:
        financing += 1
    else:
        financing -= 1

    if credit_calm:
        financing += 2
    else:
        financing -= 2

    # Energy burden
    if oil < 85:
        energy += 2
    elif oil > 95:
        energy -= 2

    # Policy capacity
    if liq_dir == "UP":
        policy += 2
    elif liq_dir == "DOWN":
        policy -= 2

    if curve > 0:
        policy += 1
    else:
        policy -= 1

    total = demand + financing + energy + policy

    if total >= 5:
        label = "DURABLE_GROWTH"
    elif total >= 1:
        label = "FRAGILE_EXPANSION"
    elif total >= -2:
        label = "LATE_CYCLE_STRAIN"
    else:
        label = "STRUCTURAL_STRESS"

    report = f"""
### 12.5) Growth Sustainability Filter [SHADOW]
- Score: {total}
- Label: {label}
- Demand: {demand}
- Financing: {financing}
- Energy: {energy}
- Policy: {policy}
"""

    return {
        "report": report,
        "state": {
            "_shadow_gsi_score": total,
            "_shadow_gsi_label": label
        }
    }