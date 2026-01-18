# scripts/fetch_liquidity_data.py
from __future__ import annotations
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUT_CSV = DATA_DIR / "liquidity_data.csv"

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id="

SERIES = {
    "TGA": "WTREGEN",     # Treasury General Account
    "RRP": "RRPONTSYD",   # Reverse Repo
    "WALCL": "WALCL",     # Fed Total Assets
}

def fetch_fred(series_id: str) -> pd.DataFrame:
    df = pd.read_csv(f"{FRED_CSV}{series_id}")
    df.columns = ["date", series_id]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df[series_id] = pd.to_numeric(df[series_id], errors="coerce")
    return df.dropna().sort_values("date").reset_index(drop=True)

def main():
    DATA_DIR.mkdir(exist_ok=True)

    tga = fetch_fred(SERIES["TGA"])
    rrp = fetch_fred(SERIES["RRP"])
    walcl = fetch_fred(SERIES["WALCL"])

    as_of = min(tga.iloc[-1]["date"], rrp.iloc[-1]["date"])

    def last(df, col):
        return float(df[df["date"] <= as_of].iloc[-1][col])

    tga_v = last(tga, SERIES["TGA"])
    rrp_v = last(rrp, SERIES["RRP"])
    walcl_v = last(walcl, SERIES["WALCL"])

    net_liq = walcl_v - tga_v - rrp_v

    new = pd.DataFrame([{
        "date": as_of.strftime("%Y-%m-%d"),
        "TGA": tga_v,
        "RRP": rrp_v,
        "WALCL": walcl_v,
        "NET_LIQ": net_liq,
    }])

    if OUT_CSV.exists():
        old = pd.read_csv(OUT_CSV)
        df = pd.concat([old, new]).drop_duplicates("date", keep="last")
    else:
        df = new

    df.to_csv(OUT_CSV, index=False)
    print("[OK] liquidity_data.csv updated")

if __name__ == "__main__":
    main()

