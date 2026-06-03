mode_policy = {
    "NORMAL_EXPANSION": {
        "allow_broad_participation": True,
        "allow_cyclical_expansion": True,
        "high_beta_cap": 1.00,
        "small_cap_cap": 1.00,
        "cyclical_cap": 1.00,
        "flow_weak_penalty": False,
        "cash_return_required": False,
    },
    "SELECTIVE_EXPANSION": {
        "allow_broad_participation": True,
        "allow_cyclical_expansion": True,
        "high_beta_cap": 0.40,
        "small_cap_cap": 0.20,
        "cyclical_cap": 0.35,
        "flow_weak_penalty": False,
        "cash_return_required": False,
    },
    "BALANCED": {
        "allow_broad_participation": False,
        "allow_cyclical_expansion": True,
        "high_beta_cap": 0.30,
        "small_cap_cap": 0.15,
        "cyclical_cap": 0.25,
        "flow_weak_penalty": False,
        "cash_return_required": False,
    },
    "SELECTIVE_ONLY": {
        "allow_broad_participation": False,
        "allow_cyclical_expansion": False,
        "high_beta_cap": 0.20,
        "small_cap_cap": 0.10,
        "cyclical_cap": 0.15,
        "flow_weak_penalty": False,
        "cash_return_required": True,
    },
    "DEFENSIVE_SELECTIVE": {
        "allow_broad_participation": False,
        "allow_cyclical_expansion": False,
        "high_beta_cap": 0.10,
        "small_cap_cap": 0.05,
        "cyclical_cap": 0.10,
        "flow_weak_penalty": False,
        "cash_return_required": True,
    },
    "CAP_RESTRICTED": {
        "allow_broad_participation": False,
        "allow_cyclical_expansion": False,
        "high_beta_cap": 0.05,
        "small_cap_cap": 0.00,
        "cyclical_cap": 0.05,
        "flow_weak_penalty": True,
        "cash_return_required": True,
    },
    "FAILED_BREADTH_MODE": {
        "allow_broad_participation": False,
        "allow_cyclical_expansion": False,
        "high_beta_cap": 0.00,
        "small_cap_cap": 0.00,
        "cyclical_cap": 0.00,
        "flow_weak_penalty": True,
        "cash_return_required": True,
    },
    "COMPRESSED_SQUEEZE": {
        "allow_broad_participation": False,
        "allow_cyclical_expansion": False,
        "high_beta_cap": 0.25,
        "small_cap_cap": 0.00,
        "cyclical_cap": 0.05,
        "flow_weak_penalty": True,
        "cash_return_required": True,
    },
    "VOL_STRUCTURE_DEFENSE": {
        "allow_broad_participation": True,
        "allow_cyclical_expansion": False,
        "high_beta_cap": 0.15,
        "small_cap_cap": 0.05,
        "cyclical_cap": 0.10,
        "flow_weak_penalty": False,
        "cash_return_required": True,
    },
}

def classify_participation_quality(context):
    leadership_state = context["leadership_state"]
    breadth_score = context["breadth_score"]
    positioning_state = context["positioning_state"]
    positioning_score = context["positioning_score"]

    quality_score = breadth_score + positioning_score

    if leadership_state == "FAILED_BREADTH":
        return {
            "participation_quality": "COMPRESSED_OR_FAILED",
            "participation_quality_score": quality_score,
            "participation_mode": "FAILED_BREADTH_MODE"
        }

    if (
        leadership_state in ["NARROW", "MEGACAP_ONLY"]
        and positioning_state == "SQUEEZE_RISK"
    ):
        return {
            "participation_quality": "COMPRESSED_OR_FAILED",
            "participation_quality_score": quality_score,
            "participation_mode": "COMPRESSED_SQUEEZE"
        }

    if (
        leadership_state == "BROAD"
        and positioning_state in ["STRESSED", "SQUEEZE_RISK"]
    ):
        return {
            "participation_quality": "FRAGILE_PARTICIPATION",
            "participation_quality_score": quality_score,
            "participation_mode": "VOL_STRUCTURE_DEFENSE"
        }

    if quality_score >= 2:
        quality = "BROAD_HEALTHY"
        mode = "NORMAL_EXPANSION"
    elif quality_score == 1:
        quality = "BROAD_BUT_WATCH"
        mode = "SELECTIVE_EXPANSION"
    elif quality_score == 0:
        quality = "NEUTRAL_PARTICIPATION"
        mode = "BALANCED"
    elif quality_score == -1:
        quality = "NARROW_PARTICIPATION"
        mode = "SELECTIVE_ONLY"
    elif quality_score == -2:
        quality = "FRAGILE_PARTICIPATION"
        mode = "DEFENSIVE_SELECTIVE"
    else:
        quality = "COMPRESSED_OR_FAILED"
        mode = "CAP_RESTRICTED"

    return {
        "participation_quality": quality,
        "participation_quality_score": quality_score,
        "participation_mode": mode
    }

test_context = {
    "leadership_state": "MEGACAP_ONLY",
    "breadth_score": -1,
    "leader_type": "MEGACAP_TECH",
    "participation_signal": "WEAK",
    "positioning_state": "SQUEEZE_RISK",
    "positioning_score": -3,
    "squeeze_risk": "HIGH",
    "gamma_signal": "SHORT_GAMMA",
    "vol_structure": "DISLOCATION",
}

print(classify_participation_quality(test_context))
