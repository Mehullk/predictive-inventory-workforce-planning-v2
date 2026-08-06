import os
import joblib
import numpy as np
import pandas as pd

from prophet import Prophet

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    mean_absolute_percentage_error,
    r2_score
)

os.makedirs("/Users/mehul/Downloads/PIP/Outputs", exist_ok=True)
os.makedirs("/Users/mehul/Downloads/PIP/Models", exist_ok=True)

train = pd.read_csv("/Users/mehul/Downloads/PIP/Data/processed/sales_train.csv")
test = pd.read_csv("/Users/mehul/Downloads/PIP/Data/processed/sales_test.csv")

train = train.rename(columns={
    "Date": "ds",
    "UnitsSold": "y"
})

test = test.rename(columns={
    "Date": "ds",
    "UnitsSold": "y"
})

train["ds"] = pd.to_datetime(train["ds"])
test["ds"] = pd.to_datetime(test["ds"])

features = [
    "MarketingSpend_lag1",
    "WebSearchInterest_lag2",
    "IsPromo",
    "IsHoliday"
]

model = Prophet(
    growth="linear",
    seasonality_mode="multiplicative",
    changepoint_prior_scale=0.05,
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
    fourier_order=10
)

model.add_seasonality(
    name="quarterly",
    period=91.25,
    fourier_order=3
)

for feature in features:
    model.add_regressor(feature)

model.fit(train[["ds", "y"] + features])

forecast = model.predict(test[["ds"] + features])

predictions = forecast["yhat"].reset_index(drop=True)
actual = test["y"].reset_index(drop=True)

mae = mean_absolute_error(actual, predictions)
mse = mean_squared_error(actual, predictions)
rmse = np.sqrt(mse)
mape = mean_absolute_percentage_error(actual, predictions)
r2 = r2_score(actual, predictions)

adj_r2 = 1 - (1 - r2) * (len(actual) - 1) / (len(actual) - len(features) - 1)

forecast_accuracy = (1 - mape) * 100

print("\n========== Prophet Results ==========")
print(f"MAE          : {mae:.2f}")
print(f"MSE          : {mse:.2f}")
print(f"RMSE         : {rmse:.2f}")
print(f"MAPE         : {mape:.2%}")
print(f"Forecast Accuracy : {forecast_accuracy:.2f}%")
print(f"R²           : {r2:.4f}")
print(f"Adjusted R²  : {adj_r2:.4f}")

historical_predictions = pd.DataFrame({
    "Date": test["ds"],
    "Actual": actual,
    "Predicted": predictions,
    "Lower95CI": forecast["yhat_lower"].values,
    "Upper95CI": forecast["yhat_upper"].values
})

historical_predictions.to_csv(
    "/Users/mehul/Downloads/PIP/Outputs/Historical_Predictions.csv",
    index=False
)

metrics = pd.DataFrame({
    "MAE": [mae],
    "MSE": [mse],
    "RMSE": [rmse],
    "MAPE": [mape],
    "ForecastAccuracy": [forecast_accuracy],
    "R2": [r2],
    "AdjustedR2": [adj_r2]
})

metrics.to_csv(
    "/Users/mehul/Downloads/PIP/Models/model_metrics.csv",
    index=False
)

joblib.dump(
    model,
    "/Users/mehul/Downloads/PIP/Models/prophet_model.pkl"
)

print("\nSaved:")
print("/Users/mehul/Downloads/PIP/Outputs/Historical_Predictions.csv")
print("/Users/mehul/Downloads/PIP/Models/model_metrics.csv")
print("/Users/mehul/Downloads/PIP/Models/prophet_model.pkl")