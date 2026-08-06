import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    mean_absolute_percentage_error,
    r2_score,
   
)


train = pd.read_csv("train_test/train_dataset.csv")
test = pd.read_csv("train_test/test_dataset.csv")


feature_columns = [
    "DayOfWeek",
    "Month",
    "Day",
    "Quarter",
    "WeekOfYear",
    "UnitPrice",
    "MarketingSpend_lag1",
    "CompetitorPriceIndex",
    "WebSearchInterest_lag2",
    "IsPromo",
    "IsHoliday",
    "UnitsSold_roll_mean_7",
    "UnitsSold_roll_std_7",
    "UnitsSold_roll_mean_30",
    "UnitsSold_roll_std_30"
]


X_train = train[feature_columns]
y_train = train["UnitsSold"]

X_test = test[feature_columns]
y_test = test["UnitsSold"]


model = LinearRegression()


model.fit(X_train, y_train)


predictions = model.predict(X_test)


mae = mean_absolute_error(y_test, predictions)
mse = mean_squared_error(y_test, predictions)
rmse = np.sqrt(mse)
mape = mean_absolute_percentage_error(y_test, predictions)
r2 = r2_score(y_test, predictions)


print("Linear Regression Results")
print(f"MAE  : {mae:.2f}")
print(f"MSE  : {mse:.2f}")
print(f"RMSE : {rmse:.2f}")
print(f"MAPE : {mape:.2%}")
print(f"R²   : {r2:.4f}")
print(f"adjusted R² : {1 - (1 - r2) * (len(y_test) - 1) / (len(y_test) - X_test.shape[1] - 1):.4f}")