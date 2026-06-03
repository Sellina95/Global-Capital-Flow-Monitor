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
