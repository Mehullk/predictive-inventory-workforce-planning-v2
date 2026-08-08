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

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_REPORT = OUTPUT_DIR / "Workforce_Decision_Report.csv"
OUTPUT_KPI = OUTPUT_DIR / "Workforce_Decision_KPIs.csv"
OUTPUT_ASSUMPTIONS = OUTPUT_DIR / "Workforce_Decision_Assumptions.csv"


# ==========================================================
# LOAD DATA
# ==========================================================

df = pd.read_csv(INPUT_FILE)

df["Date"] = pd.to_datetime(df["Date"])

df = (
    df.sort_values("Date")
    .reset_index(drop=True)
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
    "GapFrequency",
    "PendingWorkers",
    "HiringCost7",
    "OvertimeCost7",
    "HybridCost7",
    "RecommendedStrategy",
    "AlternativeStrategy",
    "ImplementationTime",
    "DecisionReason",
    "EstimatedSaving",
    "WorkersToHire",
    "HiringRequired",
    "FirstGapDate7",
    "RecommendedHireDate",
    "DaysBeforeGap",
    "GapWorkers",
    "DecisionCost",
    "AlternativeCost",
    "CostDifference",
]

numeric_columns = [
    "CurrentStaff",
    "CurrentGap",
    "GapDays7",
    "TotalGap7",
    "MaximumGap7",
    "AverageGap7",
    "GapFrequency",
    "PendingWorkers",
    "HiringCost7",
    "OvertimeCost7",
    "HybridCost7",
    "EstimatedSaving",
    "WorkersToHire",
    "HiringRequired",
    "DaysBeforeGap",
    "GapWorkers",
    "DecisionCost",
    "AlternativeCost",
    "CostDifference",
]

text_columns = [
    "RecommendedStrategy",
    "AlternativeStrategy",
    "ImplementationTime",
    "DecisionReason",
    "FirstGapDate7",
    "RecommendedHireDate",
]

for column in numeric_columns:
    decision[column] = np.nan

for column in text_columns:
    decision[column] = ""


# ==========================================================
# INITIALIZE ENGINE
# ==========================================================

default_staff = int(df["CurrentStaff"].iloc[0])

current_staff = default_staff
current_month = None
pending_hires = deque()

decision_kpis = None
decision_assumptions = None

print("=" * 70)
print("Predictive Workforce Decision Engine V2")
print("=" * 70)
print()


# ==========================================================
# MODULE 1 : BASIC HELPERS
# ==========================================================

def get_future_required_workers(dataframe, index):
    return int(dataframe.at[index, "RequiredWorkers"])


def get_future_date(dataframe, index):
    return pd.to_datetime(dataframe.at[index, "Date"])


def get_month_key(date):
    return date.year, date.month


def calculate_gap(required_workers, available_workers):
    return max(
        int(required_workers) - int(available_workers),
        0,
    )


def get_pending_workers(pending_hires):
    return int(
        sum(
            hire["workers"]
            for hire in pending_hires
        )
    )


def clone_pending_hires(pending_hires):
    cloned = deque()

    for hire in pending_hires:
        cloned.append(
            {
                "workers": hire["workers"],
                "joining_date": hire["joining_date"],
            }
        )

    return cloned


def apply_joining_workers(
    current_staff,
    pending_hires,
    current_date,
):
    joined_today = 0

    while (
        pending_hires
        and pending_hires[0]["joining_date"] <= current_date
    ):
        hire = pending_hires.popleft()

        current_staff += hire["workers"]
        joined_today += hire["workers"]

    return current_staff, joined_today


def calculate_daily_worker_cost(
    projected_labor_cost,
    current_staff,
):
    return (
        float(projected_labor_cost)
        / max(int(current_staff), 1)
    )


def calculate_hourly_rate(daily_worker_cost):
    return (
        float(daily_worker_cost)
        / WORKING_HOURS_PER_DAY
    )


def queue_hiring_request(
    pending_hires,
    workers,
    current_date,
):
    workers = int(workers)

    if workers <= 0:
        return

    pending_hires.append(
        {
            "workers": workers,
            "joining_date": (
                current_date
                + pd.Timedelta(days=HIRING_LEAD_TIME)
            ),
        }
    )


# ==========================================================
# MODULE 2 : LOOKAHEAD ANALYSIS
# ==========================================================

def analyse_lookahead(
    dataframe,
    current_index,
    current_staff,
    pending_hires,
):
    """
    Simulates only already-scheduled hires.

    IMPORTANT:
    This function does NOT insert new hires while calculating
    the forecast. That keeps the shortage signal honest.

    The result therefore answers:
        "When would the workforce become insufficient if we
         keep the currently scheduled staffing plan?"
    """

    simulated_staff = int(current_staff)

    simulated_queue = clone_pending_hires(
        pending_hires
    )

    horizon_end = min(
        current_index + PLANNING_HORIZON - 1,
        len(dataframe) - 1,
    )

    gap_days = 0
    total_gap = 0
    maximum_gap = 0

    daily_gaps = []
    gap_dates = []

    first_shortage_day = None
    first_shortage_gap = 0

    for index in range(
        current_index,
        horizon_end + 1,
    ):
        current_date = get_future_date(
            dataframe,
            index,
        )

        simulated_staff, _ = apply_joining_workers(
            simulated_staff,
            simulated_queue,
            current_date,
        )

        required_workers = get_future_required_workers(
            dataframe,
            index,
        )

        gap = calculate_gap(
            required_workers,
            simulated_staff,
        )

        daily_gaps.append(gap)

        if gap > 0:
            gap_days += 1
            total_gap += gap
            maximum_gap = max(
                maximum_gap,
                gap,
            )

            gap_dates.append(current_date)

            if first_shortage_day is None:
                first_shortage_day = index
                first_shortage_gap = gap

    average_gap = 0

    if gap_days > 0:
        average_gap = round(
            total_gap / gap_days,
            2,
        )

    # Future shortage after the hiring lead time.
    # This is used to decide whether current shortages need
    # both temporary coverage and permanent hiring.
    future_hire_index = min(
        current_index + HIRING_LEAD_TIME,
        horizon_end,
    )

    future_gap_after_lead = 0
    future_max_gap_after_lead = 0
    future_gap_days_after_lead = 0

    for index in range(
        future_hire_index,
        horizon_end + 1,
    ):
        current_date = get_future_date(
            dataframe,
            index,
        )

        future_staff = int(current_staff)

        future_queue = clone_pending_hires(
            pending_hires
        )

        for queue_index in range(
            current_index,
            index + 1,
        ):
            queue_date = get_future_date(
                dataframe,
                queue_index,
            )

            future_staff, _ = apply_joining_workers(
                future_staff,
                future_queue,
                queue_date,
            )

        required_workers = get_future_required_workers(
            dataframe,
            index,
        )

        gap = calculate_gap(
            required_workers,
            future_staff,
        )

        if gap > 0:
            future_gap_days_after_lead += 1
            future_gap_after_lead = max(
                future_gap_after_lead,
                gap,
            )
            future_max_gap_after_lead = max(
                future_max_gap_after_lead,
                gap,
            )

    return {
        "GapDays": gap_days,
        "TotalGap": total_gap,
        "MaximumGap": maximum_gap,
        "AverageGap": average_gap,
        "DailyGaps": daily_gaps,
        "GapDates": gap_dates,
        "FirstShortageDay": first_shortage_day,
        "FirstShortageGap": first_shortage_gap,
        "WorkersNeededToday": (
            first_shortage_gap
            if (
                first_shortage_day is not None
                and first_shortage_day
                <= current_index + HIRING_LEAD_TIME
            )
            else 0
        ),
        "FutureGapAfterLead": future_gap_after_lead,
        "FutureMaxGapAfterLead": future_max_gap_after_lead,
        "FutureGapDaysAfterLead": future_gap_days_after_lead,
    }


# ==========================================================
# MODULE 3 : STRATEGY COSTS
# ==========================================================

def calculate_strategy_costs(
    lookahead,
    daily_worker_cost,
    hourly_rate,
    current_gap,
    hiring_workers,
):
    total_gap = int(lookahead["TotalGap"])
    gap_days = int(lookahead["GapDays"])

    hiring_workers = max(
        int(hiring_workers),
        0,
    )

    # Hiring cost:
    # one month of salary for newly hired workers.
    hiring_cost = (
        hiring_workers
        * daily_worker_cost
        * COST_EVALUATION_DAYS
    )

    # Overtime cost:
    # every worker-day of shortage receives the configured
    # overtime allowance.
    overtime_hours = (
        total_gap
        * MAX_OVERTIME_PER_WORKER
    )

    overtime_cost = (
        overtime_hours
        * hourly_rate
        * OVERTIME_MULTIPLIER
    )

    # Hybrid:
    # permanent hires cover part of persistent/future demand;
    # overtime remains for the uncovered worker-days.
    covered_worker_days = (
        hiring_workers
        * gap_days
    )

    remaining_gap = max(
        total_gap - covered_worker_days,
        0,
    )

    # At minimum, an immediate current gap still needs
    # temporary coverage until new hires arrive.
    immediate_overtime_gap = (
        max(int(current_gap), 0)
        * min(
            HIRING_LEAD_TIME,
            max(gap_days, 1),
        )
    )

    hybrid_overtime_worker_days = max(
        remaining_gap,
        immediate_overtime_gap,
    )

    hybrid_hours = (
        hybrid_overtime_worker_days
        * MAX_OVERTIME_PER_WORKER
    )

    hybrid_cost = (
        hiring_workers
        * daily_worker_cost
        * COST_EVALUATION_DAYS
        + hybrid_hours
        * hourly_rate
        * OVERTIME_MULTIPLIER
    )

    return {
        "HiringCost": round(hiring_cost, 2),
        "OvertimeCost": round(overtime_cost, 2),
        "HybridCost": round(hybrid_cost, 2),
    }


def get_strategy_cost(costs, strategy):
    if strategy == "Hiring":
        return float(costs["HiringCost"])

    if strategy == "Overtime":
        return float(costs["OvertimeCost"])

    if strategy == "Hybrid":
        return float(costs["HybridCost"])

    return 0.0


# ==========================================================
# MODULE 4 : DECISION ENGINE
# ==========================================================

def generate_decision(
    dataframe,
    current_index,
    current_staff,
    pending_hires,
):
    lookahead = analyse_lookahead(
        dataframe,
        current_index,
        current_staff,
        pending_hires,
    )

    projected_labor_cost = float(
        dataframe.at[
            current_index,
            "ProjectedLaborCost",
        ]
    )

    daily_worker_cost = calculate_daily_worker_cost(
        projected_labor_cost,
        max(current_staff, 1),
    )

    hourly_rate = calculate_hourly_rate(
        daily_worker_cost,
    )

    current_gap = calculate_gap(
        dataframe.at[
            current_index,
            "RequiredWorkers",
        ],
        current_staff,
    )

    pending_workers = get_pending_workers(
        pending_hires
    )

    # ------------------------------------------------------
    # Identify the permanent workforce requirement.
    # ------------------------------------------------------

    future_hiring_need = max(
        lookahead["WorkersNeededToday"],
        lookahead["FutureMaxGapAfterLead"],
        0,
    )

    workers_to_hire = max(
        future_hiring_need - pending_workers,
        0,
    )

    # If there is an immediate shortage, do not pretend that
    # hiring solves today's problem. Temporary coverage is
    # required immediately.
    if current_gap > 0:

        if workers_to_hire > 0:
            recommended_strategy = "Hybrid"
            implementation_time = "Immediate + Hiring"

        else:
            recommended_strategy = "Overtime"
            implementation_time = "Immediate"

    # No current shortage, but a shortage is approaching within
    # the hiring lead time.
    elif (
        lookahead["FirstShortageDay"] is not None
        and (
            lookahead["FirstShortageDay"]
            <= current_index + HIRING_LEAD_TIME
        )
        and workers_to_hire > 0
    ):
        recommended_strategy = "Hiring"
        implementation_time = "Today"

    # A shortage exists further out, but there is still enough
    # time before the hiring lead-time window. Do not tell
    # management to hire too early.
    elif (
        lookahead["FirstShortageDay"] is not None
        and workers_to_hire > 0
    ):
        recommended_strategy = "No Action"
        implementation_time = "Monitor"

    else:
        recommended_strategy = "No Action"
        implementation_time = "Immediate"
        workers_to_hire = 0

    # ------------------------------------------------------
    # Costs are calculated AFTER the actual decision quantity
    # has been established.
    # ------------------------------------------------------

    costs = calculate_strategy_costs(
        lookahead,
        daily_worker_cost,
        hourly_rate,
        current_gap,
        workers_to_hire,
    )

    # No Action means no recommended intervention cost.
    if recommended_strategy == "No Action":
        decision_cost = 0.0
    else:
        decision_cost = get_strategy_cost(
            costs,
            recommended_strategy,
        )

    # ------------------------------------------------------
    # Dates
    # ------------------------------------------------------

    first_gap_date = None

    if lookahead["FirstShortageDay"] is not None:
        first_gap_date = pd.to_datetime(
            dataframe.at[
                lookahead["FirstShortageDay"],
                "Date",
            ]
        )

    recommended_hire_date = None
    days_before_gap = 0

    if (
        first_gap_date is not None
        and workers_to_hire > 0
    ):
        recommended_hire_date = (
            first_gap_date
            - pd.Timedelta(
                days=HIRING_LEAD_TIME
            )
        )

        days_before_gap = max(
            (
                first_gap_date
                - dataframe.at[
                    current_index,
                    "Date",
                ]
            ).days,
            0,
        )

    # ------------------------------------------------------
    # Human-readable explanation
    # ------------------------------------------------------

    if recommended_strategy == "Hiring":

        decision_reason = (
            f"Projected shortage of "
            f"{workers_to_hire} worker(s) on "
            f"{first_gap_date.strftime('%d %b %Y')}. "
            f"Hiring now provides the required "
            f"{HIRING_LEAD_TIME}-day lead time."
        )

    elif recommended_strategy == "Overtime":

        decision_reason = (
            f"Current shortage of "
            f"{current_gap} worker(s) requires immediate "
            f"temporary coverage. Overtime is recommended "
            f"because no additional permanent workforce is "
            f"required within the current decision window."
        )

    elif recommended_strategy == "Hybrid":

        decision_reason = (
            f"Current shortage of "
            f"{current_gap} worker(s) requires immediate "
            f"temporary coverage, while an additional "
            f"{workers_to_hire} worker(s) are required for "
            f"future demand. Hybrid coverage combines "
            f"overtime now with hiring for the upcoming gap."
        )

    elif implementation_time == "Monitor":

        decision_reason = (
            f"A projected workforce gap occurs on "
            f"{first_gap_date.strftime('%d %b %Y')}, but it "
            f"is outside the immediate {HIRING_LEAD_TIME}-day "
            f"hiring window. No action is required today; "
            f"the situation should be reviewed closer to the "
            f"recommended hire date."
        )

    else:

        decision_reason = (
            "Current workforce is sufficient and no immediate "
            "intervention is required."
        )

    # ------------------------------------------------------
    # Alternative strategy
    # ------------------------------------------------------

    if recommended_strategy == "No Action":
        alternative_strategy = "None"
        alternative_cost = 0.0
    else:
        alternatives = [
            strategy
            for strategy in (
                "Hiring",
                "Overtime",
                "Hybrid",
            )
            if strategy != recommended_strategy
        ]

        alternative_strategy = min(
            alternatives,
            key=lambda strategy: get_strategy_cost(
                costs,
                strategy,
            ),
        )

        alternative_cost = get_strategy_cost(
            costs,
            alternative_strategy,
        )

    cost_difference = abs(
        decision_cost - alternative_cost
    )

    estimated_saving = max(
        alternative_cost - decision_cost,
        0.0,
    )

    # For an immediate shortage, GapWorkers should describe
    # today's actual shortage. For a future hiring decision,
    # it describes the workforce quantity that must be added.
    if current_gap > 0:
        gap_workers = current_gap
    else:
        gap_workers = workers_to_hire

    return {
        "CurrentGap": current_gap,

        "GapDays7": lookahead["GapDays"],

        "TotalGap7": lookahead["TotalGap"],

        "MaximumGap7": lookahead["MaximumGap"],

        "AverageGap7": lookahead["AverageGap"],

        "GapFrequency": round(
            lookahead["GapDays"]
            / max(
                len(lookahead["DailyGaps"]),
                1,
            ),
            2,
        ),

        "HiringCost7": (
            costs["HiringCost"]
            if recommended_strategy != "No Action"
            else 0.0
        ),

        "OvertimeCost7": (
            costs["OvertimeCost"]
            if recommended_strategy != "No Action"
            else 0.0
        ),

        "HybridCost7": (
            costs["HybridCost"]
            if recommended_strategy != "No Action"
            else 0.0
        ),

        "RecommendedStrategy":
            recommended_strategy,

        "AlternativeStrategy":
            alternative_strategy,

        "ImplementationTime":
            implementation_time,

        "DecisionReason":
            decision_reason,

        "EstimatedSaving":
            round(estimated_saving, 2),

        "WorkersToHire":
            int(workers_to_hire),

        # Dashboard compatibility alias.
        "HiringRequired":
            int(workers_to_hire),

        "FirstGapDate7":
            (
                ""
                if first_gap_date is None
                else first_gap_date.strftime("%Y-%m-%d")
            ),

        "RecommendedHireDate":
            (
                ""
                if recommended_hire_date is None
                else recommended_hire_date.strftime("%Y-%m-%d")
            ),

        "DaysBeforeGap":
            int(days_before_gap),

        "GapWorkers":
            int(gap_workers),

        "DecisionCost":
            round(decision_cost, 2),

        "AlternativeCost":
            round(alternative_cost, 2),

        "CostDifference":
            round(cost_difference, 2),
    }


# ==========================================================
# MODULE 5 : RUN ENGINE
# ==========================================================

current_staff = default_staff
current_month = None
pending_hires = deque()

for index in range(len(df)):

    current_date = df.at[
        index,
        "Date",
    ]

    month_key = get_month_key(
        current_date
    )

    # Preserve the original monthly workforce reset behavior.
    if current_month != month_key:
        current_month = month_key
        current_staff = default_staff
        pending_hires.clear()

    # Apply previously scheduled hires that have reached
    # their joining date.
    current_staff, joined_today = apply_joining_workers(
        current_staff,
        pending_hires,
        current_date,
    )

    decision_data = generate_decision(
        df,
        index,
        current_staff,
        pending_hires,
    )

    # Queue only the actual permanent hiring recommendation.
    if decision_data["WorkersToHire"] > 0:

        already_scheduled = get_pending_workers(
            pending_hires
        )

        additional_workers = max(
            decision_data["WorkersToHire"]
            - already_scheduled,
            0,
        )

        if additional_workers > 0:
            queue_hiring_request(
                pending_hires,
                additional_workers,
                current_date,
            )

    # ------------------------------------------------------
    # Persist ALL decision-engine outputs.
    # This is the critical fix for the dashboard.
    # ------------------------------------------------------

    decision.at[
        index,
        "CurrentStaff",
    ] = current_staff

    decision.at[
        index,
        "CurrentGap",
    ] = decision_data["CurrentGap"]

    decision.at[
        index,
        "GapDays7",
    ] = decision_data["GapDays7"]

    decision.at[
        index,
        "TotalGap7",
    ] = decision_data["TotalGap7"]

    decision.at[
        index,
        "MaximumGap7",
    ] = decision_data["MaximumGap7"]

    decision.at[
        index,
        "AverageGap7",
    ] = decision_data["AverageGap7"]

    decision.at[
        index,
        "GapFrequency",
    ] = decision_data["GapFrequency"]

    # Record the queue AFTER today's hiring request has been
    # added, so the report shows what is now scheduled.
    decision.at[
        index,
        "PendingWorkers",
    ] = get_pending_workers(
        pending_hires
    )

    decision.at[
        index,
        "HiringCost7",
    ] = decision_data["HiringCost7"]

    decision.at[
        index,
        "OvertimeCost7",
    ] = decision_data["OvertimeCost7"]

    decision.at[
        index,
        "HybridCost7",
    ] = decision_data["HybridCost7"]

    decision.at[
        index,
        "RecommendedStrategy",
    ] = decision_data["RecommendedStrategy"]

    decision.at[
        index,
        "AlternativeStrategy",
    ] = decision_data["AlternativeStrategy"]

    decision.at[
        index,
        "ImplementationTime",
    ] = decision_data["ImplementationTime"]

    decision.at[
        index,
        "DecisionReason",
    ] = decision_data["DecisionReason"]

    decision.at[
        index,
        "EstimatedSaving",
    ] = decision_data["EstimatedSaving"]

    decision.at[
        index,
        "WorkersToHire",
    ] = decision_data["WorkersToHire"]

    decision.at[
        index,
        "HiringRequired",
    ] = decision_data["HiringRequired"]

    decision.at[
        index,
        "FirstGapDate7",
    ] = decision_data["FirstGapDate7"]

    decision.at[
        index,
        "RecommendedHireDate",
    ] = decision_data["RecommendedHireDate"]

    decision.at[
        index,
        "DaysBeforeGap",
    ] = decision_data["DaysBeforeGap"]

    decision.at[
        index,
        "GapWorkers",
    ] = decision_data["GapWorkers"]

    decision.at[
        index,
        "DecisionCost",
    ] = decision_data["DecisionCost"]

    decision.at[
        index,
        "AlternativeCost",
    ] = decision_data["AlternativeCost"]

    decision.at[
        index,
        "CostDifference",
    ] = decision_data["CostDifference"]


# ==========================================================
# MODULE 6 : VALIDATION
# ==========================================================

# These checks make sure the report cannot silently contain
# the contradictions seen in the dashboard.

invalid_hiring = decision[
    (
        decision["RecommendedStrategy"] == "Hiring"
    )
    & (
        decision["WorkersToHire"] <= 0
    )
]

invalid_overtime = decision[
    (
        decision["RecommendedStrategy"] == "Overtime"
    )
    & (
        decision["CurrentGap"] <= 0
    )
]

invalid_hybrid = decision[
    (
        decision["RecommendedStrategy"] == "Hybrid"
    )
    & (
        decision["CurrentGap"] <= 0
    )
    & (
        decision["WorkersToHire"] <= 0
    )
]

if len(invalid_hiring) > 0:
    print(
        f"WARNING: {len(invalid_hiring)} invalid Hiring "
        f"decision(s) detected."
    )

if len(invalid_overtime) > 0:
    print(
        f"WARNING: {len(invalid_overtime)} invalid Overtime "
        f"decision(s) detected."
    )

if len(invalid_hybrid) > 0:
    print(
        f"WARNING: {len(invalid_hybrid)} invalid Hybrid "
        f"decision(s) detected."
    )


# ==========================================================
# MODULE 7 : CONSOLE REPORT
# ==========================================================

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
            "WorkersToHire",
            "FirstGapDate7",
            "RecommendedHireDate",
            "DecisionCost",
            "AlternativeStrategy",
            "AlternativeCost",
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
            "WorkersToHire",
            "FirstGapDate7",
            "RecommendedHireDate",
            "DecisionCost",
            "AlternativeStrategy",
            "AlternativeCost",
        ]
    ].tail(30)
)


# ==========================================================
# MODULE 8 : KPI REPORT
# ==========================================================

decision_kpis = pd.DataFrame(
    {
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
            "Total Workers Recommended For Hiring",
            "Total Recommended Decision Cost",
            "Average Hiring Cost",
            "Average Overtime Cost",
            "Average Hybrid Cost",
        ],
        "Value": [
            len(decision),

            int(
                (
                    decision["RecommendedStrategy"]
                    == "Hiring"
                ).sum()
            ),

            int(
                (
                    decision["RecommendedStrategy"]
                    == "Overtime"
                ).sum()
            ),

            int(
                (
                    decision["RecommendedStrategy"]
                    == "Hybrid"
                ).sum()
            ),

            int(
                (
                    decision["RecommendedStrategy"]
                    == "No Action"
                ).sum()
            ),

            round(
                decision["CurrentStaff"].mean(),
                2,
            ),

            round(
                decision["RequiredWorkers"].mean(),
                2,
            ),

            int(
                decision["CurrentStaff"].max()
            ),

            int(
                decision["RequiredWorkers"].max()
            ),

            int(
                decision["CurrentGap"].max()
            ),

            round(
                decision["CurrentGap"].mean(),
                2,
            ),

            int(
                decision["PendingWorkers"].max()
            ),

            int(
                decision["WorkersToHire"].sum()
            ),

            round(
                decision["DecisionCost"].sum(),
                2,
            ),

            round(
                decision["HiringCost7"].mean(),
                2,
            ),

            round(
                decision["OvertimeCost7"].mean(),
                2,
            ),

            round(
                decision["HybridCost7"].mean(),
                2,
            ),
        ],
    }
)


# ==========================================================
# MODULE 9 : MODEL ASSUMPTIONS
# ==========================================================

decision_assumptions = pd.DataFrame(
    {
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
            "Cost Basis",
        ],
        "Value": [
            "90-day dashboard / daily decision rows",
            f"{PLANNING_HORIZON} Days",
            "Enabled",
            f"{HIRING_LEAD_TIME} Days",
            "Predictive Lookahead",
            "FIFO Queue",
            "Temporary Shortage",
            "Mixed Hiring + Overtime",
            WORKING_HOURS_PER_DAY,
            MAX_OVERTIME_PER_WORKER,
            OVERTIME_MULTIPLIER,
            "One Month Salary",
            "Monthly Salary Only",
        ],
    }
)


# ==========================================================
# MODULE 10 : SAVE REPORTS
# ==========================================================

decision.to_csv(
    OUTPUT_REPORT,
    index=False,
)

decision_kpis.to_csv(
    OUTPUT_KPI,
    index=False,
)

decision_assumptions.to_csv(
    OUTPUT_ASSUMPTIONS,
    index=False,
)


# ==========================================================
# FINAL OUTPUT
# ==========================================================

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

print()
print("Strategy Distribution")
print(
    decision["RecommendedStrategy"]
    .value_counts()
)