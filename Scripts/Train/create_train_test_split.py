import pandas as pd

df = pd.read_csv("/Users/mehul/Downloads/PIP/Data/processed/sales_feature_engineered.csv")

df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date").reset_index(drop=True)

split_index = int(len(df) * 0.92)

train = df.iloc[:split_index].copy()
test = df.iloc[split_index:].copy()

train.to_csv("/Users/mehul/Downloads/PIP/Data/processed/sales_train.csv", index=False)
test.to_csv("/Users/mehul/Downloads/PIP/Data/processed/sales_test.csv", index=False)

print("=" * 40)
print("Train Shape :", train.shape)
print("Test Shape  :", test.shape)
print("=" * 40)
print("Train Period :", train["Date"].min(), "to", train["Date"].max())
print("Test Period  :", test["Date"].min(), "to", test["Date"].max())