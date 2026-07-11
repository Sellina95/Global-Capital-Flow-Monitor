from pathlib import Path
import pandas as pd

DATA = Path("data/backtest")
OUT = DATA / "master_panel.csv"

FILES = {
    "macro": "macro_data.csv",
    "positioning": "positioning_data.csv",
    "sentiment": "sentiment_proxy.csv",
    "country_etf": "country_etf_data_combined.csv",
    "sovereign_yields": "sovereign_yields.csv",
    "sovereign_spreads": "sovereign_spreads.csv",
    "credit": "credit_spread_data.csv",
    "liquidity": "liquidity_data.csv",
    "fred_sector": "fred_macro_sctorallo.csv",
    "fred_extras": "fred_macro_extras.csv",
}

def load_csv(name: str, filename: str) -> pd.DataFrame:
    path = DATA / filename
    if not path.exists():
        raise FileNotFoundError(f"{name}: {path}")

    df = pd.read_csv(path)

    date_col = next(
        (c for c in df.columns if c.lower() in {"date", "datetime"}),
        None,
    )
    if date_col is None:
        raise ValueError(f"{name}: date column not found")

    df = df.rename(columns={date_col: "date"})
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = (
        df.dropna(subset=["date"])
        .sort_values("date")
        .drop_duplicates("date", keep="last")
    )

    # 같은 이름의 컬럼 충돌 방지
    if name != "macro":
        rename = {
            c: f"{name}__{c}"
            for c in df.columns
            if c != "date"
        }
        df = df.rename(columns=rename)

    return df


panel = load_csv("macro", FILES["macro"])

for name, filename in FILES.items():
    if name == "macro":
        continue

    right = load_csv(name, filename)
    panel = panel.merge(right, on="date", how="left")

panel = panel.sort_values("date").reset_index(drop=True)

# 주말·공휴일 및 저빈도 데이터는 과거 값만 전달.
# 미래 데이터 누수를 막기 위해 bfill은 절대 사용하지 않음.
non_price_prefixes = (
    "positioning__",
    "sentiment__",
    "sovereign_yields__",
    "sovereign_spreads__",
    "credit__",
    "liquidity__",
    "fred_sector__",
    "fred_extras__",
)

ffill_cols = [
    c for c in panel.columns
    if c.startswith(non_price_prefixes)
]
panel[ffill_cols] = panel[ffill_cols].ffill()

panel["signal_date"] = panel["date"]
panel["execution_date"] = panel["date"].shift(-1)

panel.to_csv(OUT, index=False, encoding="utf-8-sig")

print(f"Saved: {OUT}")
print(f"Period: {panel['date'].min().date()} ~ {panel['date'].max().date()}")
print(f"Rows: {len(panel):,}")
print(f"Columns: {len(panel.columns):,}")
print(f"Duplicate dates: {panel['date'].duplicated().sum()}")
print("\nT-1 mapping:")
print(panel[["signal_date", "execution_date"]].head(5).to_string(index=False))
