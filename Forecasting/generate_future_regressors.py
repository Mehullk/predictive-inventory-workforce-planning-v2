import pandas as pd
import numpy as np

df = pd.read_csv("/Users/mehul/Downloads/PIP/Data/processed/sales_feature_engineered.csv")

df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date").reset_index(drop=True)

history = df.tail(90).copy()

weekday_stats = (
    history.groupby(history["Date"].dt.dayofweek)
    .agg({
        "MarketingSpend_lag1": "mean",
        "WebSearchInterest_lag2": "mean",
        "IsPromo": "mean"
    })
)

future_dates = pd.date_range(
    start=df["Date"].max() + pd.Timedelta(days=1),
    periods=90,
    freq="D"
)

future = pd.DataFrame({
    "Date": future_dates
})

future["Weekday"] = future["Date"].dt.dayofweek

future["MarketingSpend_lag1"] = future["Weekday"].map(
    weekday_stats["MarketingSpend_lag1"]
)

future["WebSearchInterest_lag2"] = future["Weekday"].map(
    weekday_stats["WebSearchInterest_lag2"]
)

np.random.seed(42)

promo_prob = weekday_stats["IsPromo"]

future["IsPromo"] = future["Weekday"].apply(
    lambda x: np.random.binomial(1, promo_prob.loc[x])
)

future["IsHoliday"] = 0

future.drop(columns="Weekday", inplace=True)

future.iloc[:30].to_csv(
    "/Users/mehul/Downloads/PIP/Outputs/future_regressors_30_days.csv",
    index=False
)

future.to_csv(
    "/Users/mehul/Downloads/PIP/Outputs/future_regressors_90_days.csv",
    index=False
)

print("=" * 60)
print("Future regressors generated successfully.")
print("=" * 60)
print(future.head())
print("=" * 60)
print("30-day file saved:")
print("/Users/mehul/Downloads/PIP/Outputs/future_regressors_30_days.csv")
print()
print("90-day file saved:")
print("/Users/mehul/Downloads/PIP/Outputs/future_regressors_90_days.csv")