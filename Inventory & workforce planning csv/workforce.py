import os
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_DIR = os.path.join(BASE_DIR, "outputs")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

os.makedirs(OUTPUT_DIR, exist_ok=True)

INVENTORY_REPORT = os.path.join(
    INPUT_DIR,
    "Inventory_Planning_Report.csv"
)

WORKFORCE_HISTORY = os.path.join(
    BASE_DIR,
    "datasets used",
    "workforce_train.csv"
)

OUTPUT_REPORT = os.path.join(
    OUTPUT_DIR,
    "Workforce_Planning_Report.csv"
)

OUTPUT_KPI = os.path.join(
    OUTPUT_DIR,
    "Workforce_KPIs.csv"
)

OUTPUT_ASSUMPTIONS = os.path.join(
    OUTPUT_DIR,
    "Workforce_Assumptions.csv"
)


def load_inventory_report():

    if not os.path.exists(INVENTORY_REPORT):
        raise FileNotFoundError(
            f"Inventory report not found:\n{INVENTORY_REPORT}"
        )

    df = pd.read_csv(INVENTORY_REPORT)

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])

    required_columns = [
        "Date",
        "ForecastDemand",
        "ClosingStock",
        "InventoryPosition",
        "SafetyStock",
        "NeedReplenishment",
        "StockoutFlag"
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns in Inventory_Planning_Report.csv:\n{missing}"
        )

    return df


def load_workforce_history():

    if not os.path.exists(WORKFORCE_HISTORY):
        raise FileNotFoundError(
            f"workforce_train.csv not found:\n{WORKFORCE_HISTORY}"
        )

    df = pd.read_csv(WORKFORCE_HISTORY)

    required_columns = [
        "UnitsSold",
        "RequiredHeadcount",
        "StaffedHeadcount",
        "TotalLaborCost"
    ]

    missing = [
        col
        for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns in workforce_train.csv:\n{missing}"
        )

    productivity = (
        df["UnitsSold"] /
        df["RequiredHeadcount"]
    ).replace(
        [np.inf, -np.inf],
        np.nan
    ).median()

    productivity = round(productivity, 2)

    current_staff = int(
        df["StaffedHeadcount"].iloc[-1]
    )

    daily_cost = (
        df["TotalLaborCost"] /
        df["StaffedHeadcount"]
    ).replace(
        [np.inf, -np.inf],
        np.nan
    ).median()

    daily_cost = round(daily_cost, 2)

    return {
        "productivity": productivity,
        "current_staff": current_staff,
        "daily_cost": daily_cost
    }


def generate_workforce_plan(inventory_df, config):

    productivity = config["productivity"]
    current_staff = config["current_staff"]
    daily_cost = config["daily_cost"]

    df = inventory_df.copy()

    if productivity <= 0:
        raise ValueError(
            "Calculated workforce productivity is zero."
        )

    df["RequiredWorkers"] = np.ceil(
        df["ForecastDemand"] / productivity
    ).astype(int)

    df["CurrentStaff"] = current_staff

    df["StaffGap"] = (
        df["RequiredWorkers"] -
        df["CurrentStaff"]
    )

    df["HiringRequired"] = np.where(
        df["StaffGap"] > 0,
        df["StaffGap"],
        0
    )

    df["SurplusWorkers"] = np.where(
        df["StaffGap"] < 0,
        abs(df["StaffGap"]),
        0
    )

    df["WorkerUtilization(%)"] = (
        (
            df["RequiredWorkers"] /
            df["CurrentStaff"]
        ) * 100
    ).round(2)

    df["ProjectedLaborCost"] = (
        df["RequiredWorkers"] *
        daily_cost
    ).round(2)

    df["InventoryRisk"] = np.select(
        [
            df["StockoutFlag"] == 1,
            df["NeedReplenishment"] == "YES"
        ],
        [
            "High",
            "Medium"
        ],
        default="Low"
    )

    df["RecommendedShift"] = np.select(
        [
            df["WorkerUtilization(%)"] >= 120,
            df["WorkerUtilization(%)"] >= 100,
            df["WorkerUtilization(%)"] >= 80
        ],
        [
            "Three Shift",
            "Two Shift",
            "Single Shift"
        ],
        default="Reduced Shift"
    )

    df["HiringPriority"] = np.select(
        [
            (df["InventoryRisk"] == "Low") &
            (df["StaffGap"] > 0),

            (df["InventoryRisk"] == "Medium") &
            (df["StaffGap"] > 0),

            (df["InventoryRisk"] == "High") &
            (df["StaffGap"] > 0)
        ],
        [
            "Normal",
            "High",
            "Delay Hiring Until Inventory Stabilizes"
        ],
        default="None"
    )

    return df

def enrich_workforce_plan(df):

    df = df.copy()

    df["OvertimeRequired"] = np.where(
        df["WorkerUtilization(%)"] > 100,
        "Yes",
        "No"
    )

    df["WorkforceStatus"] = np.select(
        [
            df["StaffGap"] > 0,
            df["StaffGap"] < 0
        ],
        [
            "Understaffed",
            "Overstaffed"
        ],
        default="Balanced"
    )

    high_gap = max(
        5,
        int(np.ceil(df["CurrentStaff"].iloc[0] * 0.10))
    )

    df["HiringRecommendation"] = np.select(
        [
            df["StaffGap"] >= high_gap,
            df["StaffGap"] > 0,
            df["StaffGap"] <= -high_gap,
            df["StaffGap"] < 0
        ],
        [
            "Immediate Hiring Required",
            "Hire Temporary Workers",
            "Reallocate Workforce",
            "No Hiring Required"
        ],
        default="Optimal Staffing"
    )

    df["ManagementRecommendation"] = np.select(
        [
            (df["StockoutFlag"] == 1) &
            (df["StaffGap"] > 0),

            (df["NeedReplenishment"] == "YES") &
            (df["StaffGap"] > 0),

            df["StaffGap"] > 0,

            df["StaffGap"] < 0
        ],
        [
            "Delay Hiring Until Inventory Arrives",
            "Recruit Gradually",
            "Increase Workforce",
            "Reassign Existing Workforce"
        ],
        default="Maintain Current Workforce"
    )

    df["PlanningRisk"] = np.select(
        [
            (df["InventoryRisk"] == "High") &
            (df["WorkerUtilization(%)"] > 100),

            (df["InventoryRisk"] == "Medium") |
            (df["WorkerUtilization(%)"] > 90)
        ],
        [
            "High",
            "Medium"
        ],
        default="Low"
    )

    return df


def generate_workforce_kpis(df):

    kpis = {

        "PlanningDays":
            len(df),

        "AverageForecastDemand":
            round(df["ForecastDemand"].mean(), 2),

        "TotalForecastDemand":
            round(df["ForecastDemand"].sum(), 2),

        "AverageRequiredWorkers":
            round(df["RequiredWorkers"].mean(), 2),

        "MaximumRequiredWorkers":
            int(df["RequiredWorkers"].max()),

        "MinimumRequiredWorkers":
            int(df["RequiredWorkers"].min()),

        "CurrentStaff":
            int(df["CurrentStaff"].iloc[0]),

        "MaximumStaffGap":
            int(df["StaffGap"].max()),

        "MinimumStaffGap":
            int(df["StaffGap"].min()),

        "HiringDays":
            int((df["StaffGap"] > 0).sum()),

        "SurplusDays":
            int((df["StaffGap"] < 0).sum()),

        "BalancedDays":
            int((df["StaffGap"] == 0).sum()),

        "AverageWorkerUtilization":
            round(df["WorkerUtilization(%)"].mean(), 2),

        "PeakWorkerUtilization":
            round(df["WorkerUtilization(%)"].max(), 2),

        "AverageDailyLaborCost":
            round(df["ProjectedLaborCost"].mean(), 2),

        "TotalProjectedLaborCost":
            round(df["ProjectedLaborCost"].sum(), 2),

        "InventoryRiskDays":
            int((df["InventoryRisk"] == "High").sum()),

        "OvertimeDays":
            int((df["OvertimeRequired"] == "Yes").sum()),

        "HighPlanningRiskDays":
            int((df["PlanningRisk"] == "High").sum())

    }

    return pd.DataFrame(
        list(kpis.items()),
        columns=[
            "Metric",
            "Value"
        ]
    )

def save_outputs(plan_df):

    plan_df.to_csv(
        OUTPUT_REPORT,
        index=False
    )

    generate_workforce_kpis(
        plan_df
    ).to_csv(
        OUTPUT_KPI,
        index=False
    )

    total_workers = max(
        int(plan_df["RequiredWorkers"].sum()),
        1
    )

    assumptions = pd.DataFrame({

        "Parameter": [

            "Current Staff",

            "Average Units Per Worker",

            "Average Daily Labor Cost",

            "Planning Horizon (Days)",

            "Average Daily Forecast Demand"

        ],

        "Value": [

            int(
                plan_df["CurrentStaff"].iloc[0]
            ),

            round(
                plan_df["ForecastDemand"].sum() /
                total_workers,
                2
            ),

            round(
                plan_df["ProjectedLaborCost"].sum() /
                total_workers,
                2
            ),

            len(plan_df),

            round(
                plan_df["ForecastDemand"].mean(),
                2
            )

        ]

    })

    assumptions.to_csv(
        OUTPUT_ASSUMPTIONS,
        index=False
    )


def main():

    print("\nLoading inventory report...")

    inventory_df = load_inventory_report()

    print("Loading workforce history...")

    config = load_workforce_history()

    print("Generating workforce plan...")

    workforce_df = generate_workforce_plan(
        inventory_df,
        config
    )

    workforce_df = enrich_workforce_plan(
        workforce_df
    )

    print("Saving reports...")

    save_outputs(
        workforce_df
    )

    print("\n===================================")
    print(" Workforce Planning Completed")
    print("===================================")
    print(f"Report       : {OUTPUT_REPORT}")
    print(f"KPIs         : {OUTPUT_KPI}")
    print(f"Assumptions  : {OUTPUT_ASSUMPTIONS}")
    print("===================================\n")


if __name__ == "__main__":
    main()