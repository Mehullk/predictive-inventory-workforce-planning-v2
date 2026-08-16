from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent

SOURCE_FORECAST = (
    BASE_DIR
    / "outputs"
    / "forecast_90_days_direct.csv"
)

OUTPUT_FORECAST = (
    BASE_DIR
    / "outputs"
    / "forecast_30_days.csv"
)

forecast_90 = pd.read_csv(
    SOURCE_FORECAST,
    parse_dates=["Date"]
)

forecast_90 = (
    forecast_90
    .sort_values("Date")
    .reset_index(drop=True)
)

if len(forecast_90) != 90:
    raise ValueError(
        f"Expected exactly 90 forecast rows, found {len(forecast_90)}"
    )

forecast_30 = forecast_90.iloc[:30].copy()

forecast_30.to_csv(
    OUTPUT_FORECAST,
    index=False
)

print("=" * 60)
print("30-DAY FORECAST GENERATED FROM 90-DAY FORECAST")
print("=" * 60)
print(
    f"Forecast start : {forecast_30['Date'].min().date()}"
)
print(
    f"Forecast end   : {forecast_30['Date'].max().date()}"
)
print(
    f"Forecast days  : {len(forecast_30)}"
)
print(
    f"30-day demand  : {forecast_30['Forecast'].sum():.2f}"
)
print(
    f"90-day demand  : {forecast_90['Forecast'].sum():.2f}"
)
print(
    f"Saved to       : {OUTPUT_FORECAST}"
)
print("=" * 60)