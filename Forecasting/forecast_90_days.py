import pandas as pd
import joblib
from prophet import Prophet

df = pd.read_csv("/Users/mehul/Downloads/PIP/Data/processed/sales_feature_engineered.csv")

df = df.rename(columns={
    "Date": "ds",
    "UnitsSold": "y"
})

df["ds"] = pd.to_datetime(df["ds"])

split = int(len(df) * 0.92)

train = df.iloc[:split].copy()

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

model.fit(train[["ds", "y"] + features])

future = pd.read_csv(
    "/Users/mehul/Downloads/PIP/Outputs/future_regressors_90_days.csv"
)

future = future.rename(columns={"Date": "ds"})
future["ds"] = pd.to_datetime(future["ds"])

forecast = model.predict(future)

metrics = pd.read_csv(
    "/Users/mehul/Downloads/PIP/Models/model_metrics.csv"
)

historical_accuracy = float(metrics.loc[0, "ForecastAccuracy"])

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

result = result.drop(columns=["RelativeUncertainty"])

result.to_csv(
    "/Users/mehul/Downloads/PIP/Outputs/forecast_90_days_direct.csv",
    index=False
)

joblib.dump(
    model,
    "/Users/mehul/Downloads/PIP/Models/prophet_model.pkl"
)

print(result.head())
print()
print(result.tail())
print()
print("Saved:")
print("/Users/mehul/Downloads/PIP/Outputs/forecast_90_days_direct.csv")