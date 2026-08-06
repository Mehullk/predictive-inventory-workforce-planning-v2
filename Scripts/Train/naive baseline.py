import pandas as pd
import numpy as np

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    mean_absolute_percentage_error,
    r2_score,
    adjusted_rand_score
)

df = pd.read_csv("data/sales_feature_engineered.csv")

split_index = int(len(df) * 0.92)

train = df.iloc[:split_index]
test = df.iloc[split_index:]

y_test = test["UnitsSold"]

predictions = []

for index in test.index:
    predictions.append(df.loc[index - 7, "UnitsSold"])

predictions = np.array(predictions)

mae = mean_absolute_error(y_test, predictions)
mse = mean_squared_error(y_test, predictions)
rmse = np.sqrt(mse)
mape = mean_absolute_percentage_error(y_test, predictions)
r2 = r2_score(y_test, predictions)

print("Naive Seasonal Baseline Results")
print(f"MAE  : {mae:.2f}")
print(f"MSE  : {mse:.2f}")
print(f"RMSE : {rmse:.2f}")
print(f"MAPE : {mape:.2%}")
print(f"R²   : {r2:.4f}")
print(f"Adjusted R² : {1 - (1 - r2) * (len(y_test) - 1) / (len(y_test) - test.shape[1] - 1):.4f}")