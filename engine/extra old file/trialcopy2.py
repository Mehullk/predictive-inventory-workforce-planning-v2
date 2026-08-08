from collections import deque
from pathlib import Path

import numpy as np
import pandas as pd

# ==========================================================
# CONFIGURATION
# ==========================================================

PLANNING_HORIZON = 14

COST_EVALUATION_DAYS = 30

HIRING_LEAD_TIME = 7

WORKING_HOURS_PER_DAY = 8

MAX_OVERTIME_PER_WORKER = 2

OVERTIME_MULTIPLIER = 1.5

PERSISTENT_SHORTAGE_THRESHOLD = 3

DEFAULT_RECRUITMENT_COST = 0

# ==========================================================
# FILE PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "Inventory & workforce planning csv"
    / "outputs"
    / "Workforce_Planning_Report.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "Inventory & workforce planning csv"
    / "outputs"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_REPORT = (
    OUTPUT_DIR
    / "Workforce_Decision_Report.csv"
)

OUTPUT_KPI = (
    OUTPUT_DIR
    / "Workforce_Decision_KPIs.csv"
)

OUTPUT_ASSUMPTIONS = (
    OUTPUT_DIR
    / "Workforce_Decision_Assumptions.csv"
)

# ==========================================================
# LOAD DATA
# ==========================================================

df = pd.read_csv(INPUT_FILE)

df["Date"] = pd.to_datetime(df["Date"])

df = df.sort_values(
    "Date"
).reset_index(
    drop=True
)

# ==========================================================
# DECISION DATAFRAME
# ==========================================================

decision = df.copy()

new_columns = [

    "CurrentStaff",

    "CurrentGap",

    "GapDays7",

    "TotalGap7",

    "MaximumGap7",

    "AverageGap7",

    "PendingWorkers",

    "HiringCost7",

    "OvertimeCost7",

    "HybridCost7",

    "RecommendedStrategy",

    "AlternativeStrategy",

    "ImplementationTime",

    "DecisionReason",

    "EstimatedSaving",

    "FirstGapDate7",
    "RecommendedHireDate",
    "DaysBeforeGap",
    "GapWorkers",
    "DecisionCost",
    "AlternativeCost",
    "CostDifference"

]
numeric_columns = [

    "CurrentStaff",

    "CurrentGap",

    "GapDays7",

    "TotalGap7",

    "MaximumGap7",

    "AverageGap7",

    "PendingWorkers",

    "HiringCost7",

    "OvertimeCost7",

    "HybridCost7",

    "EstimatedSaving",

    "DaysBeforeGap",
    "GapWorkers",
    "DecisionCost",
    "AlternativeCost",
    "CostDifference"

]

text_columns = [

    "RecommendedStrategy",

    "AlternativeStrategy",

    "ImplementationTime",

    "DecisionReason",

    "FirstGapDate7",

    "RecommendedHireDate"

]

for column in numeric_columns:

    decision[column] = np.nan

for column in text_columns:

    decision[column] = ""

# ==========================================================
# INITIALIZE ENGINE
# ==========================================================

default_staff = int(
    df["CurrentStaff"].iloc[0]
)

current_staff = default_staff

current_month = None

pending_hires = deque()

decision_kpis = None

decision_assumptions = None

print("=" * 70)
print("Predictive Workforce Decision Engine V2")
print("=" * 70)
print()




def get_future_required_workers(
    dataframe,
    index
):

    return int(

        dataframe.at[
            index,
            "RequiredWorkers"
        ]

    )


def get_future_date(
    dataframe,
    index
):

    return pd.to_datetime(

        dataframe.at[
            index,
            "Date"
        ]

    )

###########################
#############module 2 
###########################
def get_month_key(date):

    return (
        date.year,
        date.month
    )


def calculate_gap(
    required_workers,
    available_workers
):

    return max(
        required_workers - available_workers,
        0
    )


def get_pending_workers(
    pending_hires
):

    return sum(
        hire["workers"]
        for hire in pending_hires
    )


def clone_pending_hires(
    pending_hires
):

    cloned = deque()

    for hire in pending_hires:

        cloned.append({

            "workers": hire["workers"],

            "joining_date": hire["joining_date"]

        })

    return cloned


def apply_joining_workers(
    current_staff,
    pending_hires,
    current_date
):

    joined_today = 0

    while (

        pending_hires

        and

        pending_hires[0]["joining_date"] <= current_date

    ):

        hire = pending_hires.popleft()

        current_staff += hire["workers"]

        joined_today += hire["workers"]

    return (

        current_staff,

        joined_today

    )


def calculate_daily_worker_cost(
    projected_labor_cost,
    current_staff
):

    return (

        projected_labor_cost /

        max(
            current_staff,
            1
        )

    )


def calculate_hourly_rate(
    daily_worker_cost
):

    return (

        daily_worker_cost /

        WORKING_HOURS_PER_DAY

    )


def queue_hiring_request(
    pending_hires,
    workers,
    current_date
):

    if workers <= 0:

        return

    pending_hires.append(

        {

            "workers": workers,

            "joining_date":

            current_date +

            pd.Timedelta(
                days=HIRING_LEAD_TIME
            )

        }

    )

#########################
######### module 3 
#########################


def analyse_lookahead(
    dataframe,
    current_index,
    current_staff,
    pending_hires
):

    simulated_staff = current_staff

    simulated_queue = clone_pending_hires(
        pending_hires
    )

    horizon_end = min(
        current_index + PLANNING_HORIZON,
        len(dataframe) - 1
    )

    gap_days = 0

    total_gap = 0

    maximum_gap = 0

    daily_gaps = []

    gap_dates = []

    first_shortage_day = None

    workers_needed_today = 0

    for index in range(

        current_index,

        horizon_end + 1

    ):

        current_date = get_future_date(

            dataframe,

            index

        )

        simulated_staff, _ = apply_joining_workers(

            simulated_staff,

            simulated_queue,

            current_date

        )

        required_workers = get_future_required_workers(

            dataframe,

            index

        )

        available_workers = simulated_staff

        gap = calculate_gap(

            required_workers,

            available_workers

        )

        daily_gaps.append(
            gap
        )

        if gap > 0:

            gap_days += 1

            total_gap += gap

            maximum_gap = max(

                maximum_gap,

                gap

            )
            gap_dates.append(current_date)
            days_ahead = index - current_index

            if (

                days_ahead <= HIRING_LEAD_TIME

                and

                workers_needed_today == 0

            ):

                first_shortage_day = index

                workers_needed_today = gap

                queue_hiring_request(

                    simulated_queue,

                    gap,

                    current_date

                )

    average_gap = 0

    if gap_days > 0:

        average_gap = round(

            total_gap /

            gap_days,

            2

        )

    return {

        "GapDays": gap_days,

        "TotalGap": total_gap,

        "MaximumGap": maximum_gap,

        "AverageGap": average_gap,

        "DailyGaps": daily_gaps,

        "GapDates": gap_dates,

        "FirstShortageDay": first_shortage_day,

        "WorkersNeededToday": workers_needed_today

    }

######################
###### module 4 
######################

def calculate_strategy_costs(
    lookahead,
    daily_worker_cost,
    hourly_rate
):

    total_gap = lookahead["TotalGap"]

    maximum_gap = lookahead["MaximumGap"]

    gap_days = lookahead["GapDays"]

    hiring_workers = max(
    lookahead["WorkersNeededToday"],
    0
    )

    # Monthly salary cost for newly hired workers
    hiring_cost = (

        hiring_workers *

        daily_worker_cost *

        COST_EVALUATION_DAYS

    )

    overtime_hours = (

    total_gap *

    MAX_OVERTIME_PER_WORKER 

    )

    overtime_cost = (

        overtime_hours *

        hourly_rate *

        OVERTIME_MULTIPLIER

    )

    hybrid_workers = int(

        np.ceil(

            hiring_workers / 2

        )

    )

    remaining_gap = max(

        total_gap -

        (

            hybrid_workers *

            gap_days

        ),

        0

    )

    hybrid_hours = (

    remaining_gap *

    MAX_OVERTIME_PER_WORKER *

    gap_days

    )

    hybrid_cost = (

        hybrid_workers *

        daily_worker_cost *

        COST_EVALUATION_DAYS

        +

        hybrid_hours *

        hourly_rate *

        OVERTIME_MULTIPLIER

    )

    return {

        "HiringCost": round(hiring_cost, 2),

        "OvertimeCost": round(overtime_cost, 2),

        "HybridCost": round(hybrid_cost, 2)

    }

def calculate_estimated_saving(
    cost_table,
    selected_strategy
):

    if selected_strategy == "No Action":

        return 0

    highest_cost = max(

        cost_table.values()

    )

    selected_cost = cost_table.get(

        selected_strategy,

        highest_cost

    )

    return round(

        highest_cost -

        selected_cost,

        2

    )


################
##### module 5 
#############3##


def generate_decision(
    dataframe,
    current_index,
    current_staff,
    pending_hires
):

    lookahead = analyse_lookahead(

        dataframe,

        current_index,

        current_staff,

        pending_hires

    )

    projected_labor_cost = dataframe.at[
        current_index,
        "ProjectedLaborCost"
    ]

    daily_worker_cost = calculate_daily_worker_cost(

        projected_labor_cost,

        max(current_staff, 1)

    )

    hourly_rate = calculate_hourly_rate(

        daily_worker_cost

    )

    costs = calculate_strategy_costs(

        lookahead,

        daily_worker_cost,

        hourly_rate

    )

    workers_to_hire = lookahead["WorkersNeededToday"]

    current_gap = calculate_gap(

        dataframe.at[
            current_index,
            "RequiredWorkers"
        ],

        current_staff

    )

    pending_workers = get_pending_workers(
    pending_hires
    )

    additional_workers_needed = max(
        workers_to_hire - pending_workers,
        0
    )

    if additional_workers_needed > 0:

        recommended_strategy = "Hiring"

        implementation_time = "Today"

        workers_to_hire = additional_workers_needed

        if lookahead["FirstShortageDay"] is not None:

            first_gap_date = dataframe.at[
                lookahead["FirstShortageDay"],
                "Date"
            ]

            decision_reason = (
                f"Projected shortage of "
                f"{workers_to_hire} worker(s) on "
                f"{first_gap_date.strftime('%d %b %Y')}. "
                f"Hiring now provides the required "
                f"{HIRING_LEAD_TIME}-day lead time."
            )

        else:

            decision_reason = (
                "Additional workforce required beyond "
                "already scheduled hires."
            )

    elif current_gap > 0:

        if costs["OvertimeCost"] <= costs["HybridCost"]:

            recommended_strategy = "Overtime"

            decision_reason = (
                f"Current shortage requires temporary coverage. "
                f"Overtime is preferred because its projected cost "
                f"of ₹{costs['OvertimeCost']:,.0f} is lower than the "
                f"hybrid alternative of "
                f"₹{costs['HybridCost']:,.0f}."
            )

        else:

            recommended_strategy = "Hybrid"

            decision_reason = (
                f"Current shortage requires temporary coverage. "
                f"Hybrid coverage is preferred because its projected "
                f"cost of ₹{costs['HybridCost']:,.0f} is lower than "
                f"overtime at ₹{costs['OvertimeCost']:,.0f}."
            )

        workers_to_hire = 0

        implementation_time = "Immediate"

    else:

        recommended_strategy = "No Action"

        workers_to_hire = 0

        implementation_time = "Immediate"

        decision_reason = (
            "Current workforce is sufficient and no immediate "
            "intervention is required."
        )

   
    #if recommended_strategy == "No Action":

     #   costs["HiringCost"] = 0

      #  costs["OvertimeCost"] = 0

       # costs["HybridCost"] = 0

    strategy_costs = {

        "Hiring": costs["HiringCost"],

        "Overtime": costs["OvertimeCost"],

        "Hybrid": costs["HybridCost"]

    }

    ranked = sorted(

        strategy_costs.items(),

        key=lambda x: x[1]

    )

    alternative_strategy = ranked[0][0]

    if alternative_strategy == recommended_strategy:

        if len(ranked) > 1:

            alternative_strategy = ranked[1][0]

    estimated_saving = calculate_estimated_saving(

        strategy_costs,

        recommended_strategy

    )

    first_gap_date = None

    if lookahead["FirstShortageDay"] is not None:

        first_gap_date = dataframe.at[
            lookahead["FirstShortageDay"],
            "Date"
        ]

    recommended_hire_date = None

    days_before_gap = 0

    if first_gap_date is not None:

        recommended_hire_date = (
            first_gap_date -
            pd.Timedelta(
                days=HIRING_LEAD_TIME
            )
        )

        days_before_gap = max(
            (
                first_gap_date -
                dataframe.at[
                    current_index,
                    "Date"
                ]
            ).days,
            0
        )

    if recommended_strategy == "Hiring":

        decision_cost = costs["HiringCost"]

    elif recommended_strategy == "Overtime":

        decision_cost = costs["OvertimeCost"]

    elif recommended_strategy == "Hybrid":

        decision_cost = costs["HybridCost"]

    else:

        decision_cost = 0

    if alternative_strategy == "Hiring":

        alternative_cost = costs["HiringCost"]

    elif alternative_strategy == "Overtime":

        alternative_cost = costs["OvertimeCost"]

    elif alternative_strategy == "Hybrid":

        alternative_cost = costs["HybridCost"]

    else:

        alternative_cost = 0

    cost_difference = abs(
        decision_cost -
        alternative_cost
    )

    return {

        "CurrentGap":

        current_gap,

        "GapDays7":

        lookahead["GapDays"],

        "TotalGap7":

        lookahead["TotalGap"],

        "MaximumGap7":

        lookahead["MaximumGap"],

        "AverageGap7":

        lookahead["AverageGap"],

        "GapFrequency":

        round(

            lookahead["GapDays"] /

            max(

                len(

                    lookahead["DailyGaps"]

                ),

                1

            ),

            2

        ),

        "HiringCost7": 0 if recommended_strategy == "No Action" else costs["HiringCost"],

        "OvertimeCost7": 0 if recommended_strategy == "No Action" else costs["OvertimeCost"],

        "HybridCost7": 0 if recommended_strategy == "No Action" else costs["HybridCost"],

        "RecommendedStrategy":

        recommended_strategy,

        "AlternativeStrategy":

        alternative_strategy,

        "ImplementationTime":

        implementation_time,

        "DecisionReason":

        decision_reason,

        "EstimatedSaving":

        estimated_saving,

        "WorkersToHire":

        workers_to_hire,

        "FirstGapDate7":

        "" if first_gap_date is None
        else first_gap_date.strftime("%Y-%m-%d"),

        "RecommendedHireDate":

        "" if recommended_hire_date is None
        else recommended_hire_date.strftime("%Y-%m-%d"),

        "DaysBeforeGap":

        days_before_gap,

        "GapWorkers":

        lookahead["WorkersNeededToday"],

        "DecisionCost":

        round(
            decision_cost,
            2
        ),

        "AlternativeCost":

        round(
            alternative_cost,
            2
        ),

        "CostDifference":

        round(
            cost_difference,
            2
        )

    }


#############
### module 6 
#############


current_staff = default_staff

current_month = None

pending_hires = deque()

for index in range(len(df)):

    current_date = df.at[
        index,
        "Date"
    ]

    month_key = get_month_key(
        current_date
    )

    if current_month != month_key:

        current_month = month_key

        current_staff = default_staff

        pending_hires.clear()

    current_staff, joined_today = apply_joining_workers(

        current_staff,

        pending_hires,

        current_date

    )

    decision_data = generate_decision(

        df,

        index,

        current_staff,

        pending_hires

    )

    if decision_data["WorkersToHire"] > 0:

        already_scheduled = get_pending_workers(

            pending_hires

        )

        additional_workers = max(

            decision_data["WorkersToHire"] -

            already_scheduled,

            0

        )

        if additional_workers > 0:

            queue_hiring_request(

                pending_hires,

                additional_workers,

                current_date

            )

    decision.at[
        index,
        "CurrentStaff"
    ] = current_staff

    decision.at[
        index,
        "CurrentGap"
    ] = decision_data[
        "CurrentGap"
    ]

    decision.at[
        index,
        "GapDays7"
    ] = decision_data[
        "GapDays7"
    ]

    decision.at[
        index,
        "TotalGap7"
    ] = decision_data[
        "TotalGap7"
    ]

    decision.at[
        index,
        "MaximumGap7"
    ] = decision_data[
        "MaximumGap7"
    ]

    decision.at[
        index,
        "AverageGap7"
    ] = decision_data[
        "AverageGap7"
    ]

    decision.at[
        index,
        "PendingWorkers"
    ] = get_pending_workers(
        pending_hires
    )

    decision.at[
        index,
        "HiringCost7"
    ] = decision_data[
        "HiringCost7"
    ]

    decision.at[
        index,
        "OvertimeCost7"
    ] = decision_data[
        "OvertimeCost7"
    ]

    decision.at[
        index,
        "HybridCost7"
    ] = decision_data[
        "HybridCost7"
    ]

    decision.at[
        index,
        "RecommendedStrategy"
    ] = decision_data[
        "RecommendedStrategy"
    ]

    decision.at[
        index,
        "AlternativeStrategy"
    ] = decision_data[
        "AlternativeStrategy"
    ]

    decision.at[
        index,
        "ImplementationTime"
    ] = decision_data[
        "ImplementationTime"
    ]

    decision.at[
        index,
        "DecisionReason"
    ] = decision_data[
        "DecisionReason"
    ]

    decision.at[
        index,
        "EstimatedSaving"
    ] = decision_data[
        "EstimatedSaving"
    ]



print()

print(
    decision[
        [
            "Date",
            "RequiredWorkers",
            "CurrentStaff",
            "CurrentGap",
            "GapDays7",
            "TotalGap7",
            "MaximumGap7",
            "PendingWorkers",
            "RecommendedStrategy",
            "HiringCost7",
            "OvertimeCost7",
            "HybridCost7"
        ]
    ].head(30)
)

print()

print(
    decision[
        [
            "Date",
            "RequiredWorkers",
            "CurrentStaff",
            "CurrentGap",
            "GapDays7",
            "TotalGap7",
            "MaximumGap7",
            "PendingWorkers",
            "RecommendedStrategy",
            "HiringCost7",
            "OvertimeCost7",
            "HybridCost7"
        ]
    ].tail(30)
)



# ============================================================
# MODULE 7 : KPI REPORT
# ============================================================

decision_kpis = pd.DataFrame({

    "Metric": [

        "Planning Days",

        "Hiring Decisions",

        "Overtime Decisions",

        "Hybrid Decisions",

        "No Action Decisions",

        "Average Current Staff",

        "Average Required Workers",

        "Maximum Current Staff",

        "Maximum Required Workers",

        "Maximum Workforce Gap",

        "Average Workforce Gap",

        "Maximum Pending Workers",

        "Average Hiring Cost",

        "Average Overtime Cost",

        "Average Hybrid Cost"

    ],

    "Value": [

        len(decision),

        int((decision["RecommendedStrategy"] == "Hiring").sum()),

        int((decision["RecommendedStrategy"] == "Overtime").sum()),

        int((decision["RecommendedStrategy"] == "Hybrid").sum()),

        int((decision["RecommendedStrategy"] == "No Action").sum()),

        round(decision["CurrentStaff"].mean(), 2),

        round(decision["RequiredWorkers"].mean(), 2),

        int(decision["CurrentStaff"].max()),

        int(decision["RequiredWorkers"].max()),

        int(decision["CurrentGap"].max()),

        round(decision["CurrentGap"].mean(), 2),

        int(decision["PendingWorkers"].max()),

        round(decision["HiringCost7"].mean(), 2),

        round(decision["OvertimeCost7"].mean(), 2),

        round(decision["HybridCost7"].mean(), 2)

    ]

})


# ============================================================
# MODULE 8 : MODEL ASSUMPTIONS
# ============================================================

decision_assumptions = pd.DataFrame({

    "Assumption": [

        "Planning Horizon",

        "Lookahead Window",

        "Monthly Workforce Reset",

        "Hiring Lead Time",

        "Hiring Decision",

        "Pending Hire Queue",

        "Overtime Rule",

        "Hybrid Rule",

        "Working Hours Per Day",

        "Overtime Hours Per Worker",

        "Overtime Pay Multiplier",

        "Hiring Cost",

        "Cost Basis"

    ],

    "Value": [

        "14 Days",

        f"{PLANNING_HORIZON} Days",

        "Enabled",

        "7 Days",

        "Predictive Lookahead",

        "FIFO Queue",

        "Temporary Shortage",

        "Mixed Hiring + Overtime",

        8,

        2,

        1.5,

        "One Month Salary",

        "Monthly Salary Only"

    ]

})




# ============================================================
# MODULE 9 : SAVE REPORTS
# ============================================================

decision.to_csv(

    OUTPUT_REPORT,

    index=False

)

decision_kpis.to_csv(

    OUTPUT_KPI,

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

print(

    decision.head()

)

print()

print("KPI Report")

print(

    decision_kpis

)

print()

print("Model Assumptions")

print(

    decision_assumptions

)

print()

print("Saved Files")

print(OUTPUT_REPORT)

print(OUTPUT_KPI)

print(OUTPUT_ASSUMPTIONS)

print("\nStrategy Distribution")
print(
    decision["RecommendedStrategy"]
    .value_counts()
)