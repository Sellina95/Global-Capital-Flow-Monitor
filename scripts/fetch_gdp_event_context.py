from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd


SOURCE = "https://tradingeconomics.com/united-states/gdp-growth"


def _clean_value(value: Any) -> Optional[str]:
    if pd.isna(value):
        return None

    text = str(value).strip()

    if not text or text.lower() == "nan":
        return None

    return text


def fetch_gdp_event_context() -> Dict[str, Any]:
    """
    Presentation-only US GDP event context.

    V0 contract:
    - Does not feed F13 / F15 / F18.
    - Failure returns available=False instead of raising.
    - TEForecast is never used as market consensus.
    """

    result: Dict[str, Any] = {
        "available": False,
        "event": "US GDP Growth",
        "source": "Trading Economics",
        "gdp_qoq": None,
    }

    try:
        tables = pd.read_html(SOURCE, flavor="lxml")

        calendar_table = None

        for table in tables:
            columns = {str(col) for col in table.columns}

            if {
                "Calendar",
                "GMT",
                "Actual",
                "Previous",
                "Consensus",
                "TEForecast",
            }.issubset(columns):
                calendar_table = table
                break

        if calendar_table is None or calendar_table.empty:
            raise ValueError("Economic calendar table not found")

        latest_event = calendar_table.iloc[-1]

        result["gdp_qoq"] = {
            "release_date": _clean_value(latest_event.get("Calendar")),
            "release_time_gmt": _clean_value(latest_event.get("GMT")),
            "reference": _clean_value(latest_event.get("Reference.1")),
            "actual": _clean_value(latest_event.get("Actual")),
            "consensus": _clean_value(latest_event.get("Consensus")),
            "previous": _clean_value(latest_event.get("Previous")),
        }

        result["available"] = True
        return result

    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result


if __name__ == "__main__":
    print(fetch_gdp_event_context())
