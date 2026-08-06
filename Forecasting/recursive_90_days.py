import pandas as pd
import joblib
from prophet import Prophet

history = pd.read_csv("/Users/mehul/Downloads/PIP/Data/processed/sales_feature_engineered.csv")
history["Date"] = pd.to_datetime(history["Date"])

forecast30 = pd.read_csv("/Users/mehul/Downloads/PIP/Outputs/forecast_30_days.csv")
forecast30["Date"] = pd.to_datetime(forecast30["Date"])

future30 = pd.read_csv("/Users/mehul/Downloads/PIP/Outputs/future_regressors_30_days.csv")
future30["Date"] = pd.to_datetime(future30["Date"])

forecast30 = forecast30.merge(future30, on="Date", how="left")

forecast30 = forecast30.rename(columns={
    "Date": "ds",
    "Forecast": "y"
})

history = history.rename(columns={
    "Date": "ds",
    "UnitsSold": "y"
})

combined = pd.concat([
    history[[
        "ds",
        "y",
        "MarketingSpend_lag1",
        "WebSearchInterest_lag2",
        "IsPromo",
        "IsHoliday"
    ]],
    forecast30[[
        "ds",
        "y",
        "MarketingSpend_lag1",
        "WebSearchInterest_lag2",
        "IsPromo",
        "IsHoliday"
    ]]
], ignore_index=True)

features = [
    "MarketingSpend_lag1",
    "WebSearchInterest_lag2",
    "IsPromo",
    "IsHoliday"
]

model = Prophet(
    growth="linear",
    seasonality_mode="multiplicative",
    changepoint_prior_scale=0.03,
    seasonality_prior_scale=10,
    holidays_prior_scale=10,
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False,
    interval_width=0.95
)

model.add_seasonality(
    name="monthly",
    period=30.5,
    fourier_order=5
)

model.add_seasonality(
    name="quarterly",
    period=91.25,
    fourier_order=5
)

for feature in features:
    model.add_regressor(feature)

model.fit(combined[["ds", "y"] + features])

future90 = pd.read_csv("/Users/mehul/Downloads/PIP/Outputs/future_regressors_90_days.csv")
future90["Date"] = pd.to_datetime(future90["Date"])

future90 = future90.iloc[30:].copy()

future90 = future90.rename(columns={
    "Date": "ds"
})

forecast = model.predict(future90)

metrics = pd.read_csv(
    "/Users/mehul/Downloads/PIP/Models/model_metrics.csv"
)

historical_accuracy = float(
    metrics.loc[0, "ForecastAccuracy"]
)

result = forecast[
    [
        "ds",
        "yhat",
        "yhat_lower",
        "yhat_upper"
    ]
].copy()

result.columns = [
    "Date",
    "Forecast",
    "Lower95CI",
    "Upper95CI"
]

result["CI_Width"] = (
    result["Upper95CI"] -
    result["Lower95CI"]
)

result["RelativeUncertainty"] = (
    result["CI_Width"] /
    (2 * result["Forecast"].abs())
)

result["DerivedConfidence"] = (
    historical_accuracy *
    (
        1 -
        result["RelativeUncertainty"]
    )
)

result["DerivedConfidence"] = (
    result["DerivedConfidence"]
    .clip(lower=0, upper=100)
    .round(2)
)

result.drop(
    columns=["RelativeUncertainty"],
    inplace=True
)

result.to_csv(
    "/Users/mehul/Downloads/PIP/Outputs/forecast_90_days_recursive.csv",
    index=False
)

joblib.dump(
    model,
    "/Users/mehul/Downloads/PIP/Models/recursive_prophet_model.pkl"
)

print(result.head())
print()
print(result.tail())
print()
print("Saved:")
print("/Users/mehul/Downloads/PIP/Outputs/forecast_90_days_recursive.csv")