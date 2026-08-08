import os
import warnings
from collections import deque

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INPUT_FILE = os.path.join(
    BASE_DIR,
    "Inventory & workforce planning csv",
    "outputs",
    "Workforce_Planning_Report.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "Inventory & workforce planning csv",
    "outputs"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_REPORT = os.path.join(
    OUTPUT_DIR,
    "Workforce_Decision_Report.csv"
)

OUTPUT_KPIS = os.path.join(
    OUTPUT_DIR,
    "Workforce_Decision_KPIs.csv"
)

OUTPUT_ASSUMPTIONS = os.path.join(
    OUTPUT_DIR,
    "Workforce_Decision_Assumptions.csv"
)


required_columns = [
    "Date",
    "CurrentStaff",
    "RequiredWorkers",
    "StaffGap",
    "ForecastDemand",
    "ProjectedLaborCost",
    "PlanningRisk",
    "WorkerUtilization(%)",
    "HiringRequired",
    "OvertimeRequired"
]

df = pd.read_csv(INPUT_FILE)

missing = [c for c in required_columns if c not in df.columns]

if missing:
    raise ValueError(
        f"Missing columns in Workforce_Planning_Report.csv:\n{missing}"
    )

df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date").reset_index(drop=True)

decision = pd.DataFrame()

decision["Date"] = df["Date"]
decision["ForecastDemand"] = df["ForecastDemand"]
decision["RequiredWorkers"] = df["RequiredWorkers"]
decision["ProjectedLaborCost"] = df["ProjectedLaborCost"]
decision["PlanningRisk"] = df["PlanningRisk"]
decision["WorkerUtilization(%)"] = df["WorkerUtilization(%)"]

default_staff = int(df["CurrentStaff"].iloc[0])

daily_worker_cost = (
    df["ProjectedLaborCost"] /
    df["CurrentStaff"]
).replace(
    [np.inf, -np.inf],
    0
).fillna(0)

hourly_rate = daily_worker_cost / 8

decision["CurrentStaff"] = 0
decision["StaffGap"] = 0
decision["GapStreak"] = 0
decision["PendingHires"] = 0

decision["HiringCostEstimate"] = 0.0
decision["OvertimeCostEstimate"] = 0.0
decision["HybridCostEstimate"] = 0.0

decision["RecommendedStrategy"] = ""
decision["AlternativeStrategy"] = ""
decision["ImplementationTime"] = ""
decision["DecisionReason"] = ""
decision["EstimatedSaving"] = 0.0

current_staff = default_staff

gap_streak = 0

current_month = None

pending_hires = deque()

######### module 2 ###########?????????????????????????????????????????????????????????????????????????????

current_staff = default_staff
current_month = None
gap_streak = 0

pending_hires = deque()

for i in range(len(df)):

    today = df.at[i, "Date"]

    month_key = (today.year, today.month)

    if current_month != month_key:

        current_month = month_key

        current_staff = default_staff

        pending_hires.clear()

    while pending_hires and pending_hires[0]["joining_date"] <= today:

        hire = pending_hires.popleft()

        current_staff += hire["workers"]

    required_workers = int(df.at[i, "RequiredWorkers"])

    pending_workers = sum(
        hire["workers"] for hire in pending_hires
    )

    effective_gap = max(
        required_workers -
        (current_staff + pending_workers),
        0
    )

    current_gap = max(
        required_workers -
        current_staff,
        0
    )

    if current_gap > 0:

        gap_streak += 1

    else:

        gap_streak = 0

    daily_worker_cost = (
        df.at[i, "ProjectedLaborCost"] /
        max(current_staff, 1)
    )

    hourly_rate = daily_worker_cost / 8

    hiring_cost = current_gap * daily_worker_cost

    overtime_hours = current_gap * 2

    overtime_cost = (
        overtime_hours *
        hourly_rate *
        1.5
    )

    hybrid_workers = int(
        np.ceil(current_gap / 2)
    )

    hybrid_hours = int(
        np.floor(current_gap / 2) * 2
    )

    hybrid_cost = (
        hybrid_workers *
        daily_worker_cost
    ) + (
        hybrid_hours *
        hourly_rate *
        1.5
    )

    strategy = ""

    alternative = ""

    implementation = ""

    reason = ""

    implementation_cost = 0

    if current_gap <= 0:

        strategy = "No Action"

        alternative = "-"

        implementation = "Immediate"

        reason = "Current workforce is sufficient."

        implementation_cost = 0

    else:

        if gap_streak >= 3:

            if effective_gap > 0:

                pending_hires.append(
                    {
                        "workers": effective_gap,
                        "joining_date": today + pd.Timedelta(days=7)
                    }
                )

                strategy = "Hiring"

                alternative = "Hybrid"

                implementation = "7 Days"

                reason = (
                    "Persistent workforce shortage "
                    "for 3 consecutive days."
                )

                implementation_cost = (
                    effective_gap *
                    daily_worker_cost
                )

            else:

                strategy = "Overtime"

                alternative = "Hybrid"

                implementation = "Immediate"

                reason = (
                    "Hiring already in progress."
                )

                implementation_cost = overtime_cost

        else:

            if current_gap <= 2:

                strategy = "Overtime"

                alternative = "Hybrid"

                implementation = "Immediate"

                reason = (
                    "Temporary workforce shortage."
                )

                implementation_cost = overtime_cost

            elif current_gap == 3:

                strategy = "Hybrid"

                alternative = "Hiring"

                implementation = "2 Days"

                reason = (
                    "Moderate workforce shortage."
                )

                implementation_cost = hybrid_cost

            else:

                if effective_gap > 0:

                    pending_hires.append(
                        {
                            "workers": effective_gap,
                            "joining_date": today + pd.Timedelta(days=7)
                        }
                    )

                strategy = "Hiring"

                alternative = "Hybrid"

                implementation = "7 Days"

                reason = (
                    "Large workforce shortage."
                )

                implementation_cost = (
                    effective_gap *
                    daily_worker_cost
                )

    decision.at[i, "CurrentStaff"] = current_staff

    decision.at[i, "RequiredWorkers"] = required_workers

    decision.at[i, "StaffGap"] = current_gap

    decision.at[i, "GapStreak"] = gap_streak

    decision.at[i, "PendingHires"] = sum(
        hire["workers"] for hire in pending_hires
    )

    decision.at[i, "HiringCostEstimate"] = round(
        hiring_cost,
        2
    )

    decision.at[i, "OvertimeCostEstimate"] = round(
        overtime_cost,
        2
    )

    decision.at[i, "HybridCostEstimate"] = round(
        hybrid_cost,
        2
    )

    decision.at[i, "RecommendedStrategy"] = strategy

    decision.at[i, "AlternativeStrategy"] = alternative

    decision.at[i, "ImplementationTime"] = implementation

    decision.at[i, "DecisionReason"] = reason

    decision.at[i, "EstimatedSaving"] = round(
        max(
            hiring_cost,
            overtime_cost,
            hybrid_cost
        ) - implementation_cost,
        2
    )


    ##################################### module 4 ##################################


decision_kpis = pd.DataFrame({

    "Metric": [

        "Planning Days",

        "Days With Workforce Gap",

        "No Action Recommendations",

        "Overtime Recommendations",

        "Hybrid Recommendations",

        "Hiring Recommendations",

        "Average Current Staff",

        "Average Required Workers",

        "Maximum Staff Gap",

        "Average Staff Gap",

        "Maximum Gap Streak",

        "Maximum Pending Hires",

        "Average Hiring Cost",

        "Average Overtime Cost",

        "Average Hybrid Cost",

        "Total Estimated Saving"

    ],

    "Value": [

        len(decision),

        int((decision["StaffGap"] > 0).sum()),

        int((decision["RecommendedStrategy"] == "No Action").sum()),

        int((decision["RecommendedStrategy"] == "Overtime").sum()),

        int((decision["RecommendedStrategy"] == "Hybrid").sum()),

        int((decision["RecommendedStrategy"] == "Hiring").sum()),

        round(decision["CurrentStaff"].mean(), 2),

        round(decision["RequiredWorkers"].mean(), 2),

        int(decision["StaffGap"].max()),

        round(decision["StaffGap"].mean(), 2),

        int(decision["GapStreak"].max()),

        int(decision["PendingHires"].max()),

        round(decision["HiringCostEstimate"].mean(), 2),

        round(decision["OvertimeCostEstimate"].mean(), 2),

        round(decision["HybridCostEstimate"].mean(), 2),

        round(decision["EstimatedSaving"].sum(), 2)

    ]

})




########################### module 5 ##################################


decision_assumptions = pd.DataFrame({

    "Assumption": [

        "Planning Horizon",

        "Monthly Workforce Reset",

        "Hiring Lead Time",

        "Persistent Shortage Threshold",

        "Overtime Rule",

        "Hybrid Rule",

        "Hiring Rule",

        "Hiring Quantity",

        "Pending Hire Queue",

        "Working Hours Per Day",

        "Overtime Hours Per Worker",

        "Overtime Pay Multiplier"

    ],

    "Value": [

        "90 Days",

        "Enabled",

        "7 Days",

        "3 Consecutive Days",

        "Gap <= 2",

        "Gap == 3",

        "Gap >= 4 or Persistent Shortage",

        "1 Worker",

        "FIFO",

        8,

        2,

        1.5

    ]

})

decision.to_csv(

    OUTPUT_REPORT,

    index=False

)

decision_kpis.to_csv(

    OUTPUT_KPIS,

    index=False

)

decision_assumptions.to_csv(

    OUTPUT_ASSUMPTIONS,

    index=False

)

print()

print("=" * 60)

print("Workforce Decision Engine Completed")

print("=" * 60)

print()

print("Decision Report")

print(decision.head())

print()

print("KPIs")

print(decision_kpis)

print()

print("Assumptions")

print(decision_assumptions)

print()

print("Saved Files")

print(OUTPUT_REPORT)

print(OUTPUT_KPIS)

print(OUTPUT_ASSUMPTIONS)