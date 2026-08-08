from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

forecast30 = pd.read_csv(ROOT / "outputs" / "forecast_30_days.csv")

forecast90 = pd.read_csv(ROOT / "outputs" / "forecast_next_90_days.csv")

metrics = pd.read_csv(ROOT / "models" / "model_metrics.csv")

inventory_kpis = pd.read_csv(
    ROOT / "Inventory & workforce planning csv" / "outputs" / "Inventory_KPIs.csv"
)

inventory_report = pd.read_csv(
    ROOT / "Inventory & workforce planning csv" / "outputs" / "Inventory_Planning_Report.csv"
)



workforce = pd.read_csv(
    ROOT / "Inventory & workforce planning csv" / "outputs" / "Workforce_Decision_Report.csv"
)


workforce_kpis = pd.read_csv(
    ROOT / "Inventory & workforce planning csv" / "outputs" / "Workforce_Decision_KPIs.csv"
)

workforce_assumptions = pd.read_csv(
    ROOT / "Inventory & workforce planning csv" / "outputs" / "Workforce_Decision_Assumptions.csv"
)

print("WORKFORCE COLUMNS:")
print(workforce.columns.tolist())