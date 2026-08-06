import pandas as pd
import matplotlib.pyplot as plt

direct = pd.read_csv(
    "/Users/mehul/Downloads/PIP/Outputs/forecast_90_days_direct.csv"
)

recursive = pd.read_csv(
    "/Users/mehul/Downloads/PIP/Outputs/forecast_90_days_recursive.csv"
)

direct["Date"] = pd.to_datetime(direct["Date"])
recursive["Date"] = pd.to_datetime(recursive["Date"])

direct = direct.iloc[30:].reset_index(drop=True)

comparison = direct.merge(
    recursive,
    on="Date",
    suffixes=("_Direct", "_Recursive")
)

comparison["Difference"] = (
    comparison["Forecast_Recursive"]
    - comparison["Forecast_Direct"]
)

comparison["DifferencePercent"] = (
    comparison["Difference"]
    / comparison["Forecast_Direct"]
) * 100

comparison["ConfidenceDifference"] = (
    comparison["DerivedConfidence_Recursive"]
    - comparison["DerivedConfidence_Direct"]
)

comparison.to_csv(
    "/Users/mehul/Downloads/PIP/Outputs/forecast_comparison.csv",
    index=False
)

print("=" * 60)
print("Average Direct Forecast        :", round(comparison["Forecast_Direct"].mean(),2))
print("Average Recursive Forecast     :", round(comparison["Forecast_Recursive"].mean(),2))
print("Average Difference             :", round(comparison["Difference"].mean(),2))
print("Average % Difference           :", round(comparison["DifferencePercent"].mean(),2))
print()

print("Average Direct Confidence      :", round(comparison["DerivedConfidence_Direct"].mean(),2))
print("Average Recursive Confidence   :", round(comparison["DerivedConfidence_Recursive"].mean(),2))
print("Average Confidence Difference  :", round(comparison["ConfidenceDifference"].mean(),2))
print("=" * 60)

print()

print("Total Direct Forecast    :", round(comparison["Forecast_Direct"].sum(),2))
print("Total Recursive Forecast :", round(comparison["Forecast_Recursive"].sum(),2))

plt.figure(figsize=(14,6))

plt.plot(
    comparison["Date"],
    comparison["Forecast_Direct"],
    label="Direct Forecast"
)

plt.plot(
    comparison["Date"],
    comparison["Forecast_Recursive"],
    label="Recursive Forecast"
)

plt.legend()

plt.title("Direct vs Recursive 90-Day Forecast")

plt.xlabel("Date")

plt.ylabel("Forecasted Sales")

plt.grid(True)

plt.tight_layout()

plt.savefig(
    "/Users/mehul/Downloads/PIP/Outputs/direct_vs_recursive.png",
    dpi=300
)

plt.figure(figsize=(14,6))

plt.plot(
    comparison["Date"],
    comparison["DerivedConfidence_Direct"],
    label="Direct Confidence"
)

plt.plot(
    comparison["Date"],
    comparison["DerivedConfidence_Recursive"],
    label="Recursive Confidence"
)

plt.legend()

plt.title("Prediction Confidence Comparison")

plt.xlabel("Date")

plt.ylabel("Derived Confidence (%)")

plt.grid(True)

plt.tight_layout()

plt.savefig(
    "/Users/mehul/Downloads/PIP/Outputs/confidence_comparison.png",
    dpi=300
)

plt.show()

print()
print("Saved:")
print("/Users/mehul/Downloads/PIP/Outputs/forecast_comparison.csv")
print("/Users/mehul/Downloads/PIP/Outputs/direct_vs_recursive.png")
print("/Users/mehul/Downloads/PIP/Outputs/confidence_comparison.png")