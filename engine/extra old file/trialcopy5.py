from collections import deque
from pathlib import Path

import numpy as np
import pandas as pd


# ==========================================================
# CONFIGURATION
# ==========================================================

PLANNING_HORIZON = 14                 # check today + next 14 days
HIRING_LEAD_TIME = 7                  # worker joins 7 days after hiring decision
WORKING_HOURS_PER_DAY = 8
MAX_OVERTIME_PER_WORKER = 2           # overtime hours used for a same-day shortage
OVERTIME_MULTIPLIER = 1.5

# Hiring triggers:
#   1) Gap >= 1 for 2 or more consecutive days
#   2) gap >= 3 for 2 or more consecutive days
#
# A single isolated gap > 2 is intentionally NOT a hiring trigger.
# It is handled as Hybrid on the shortage day.
PERSISTENT_GAP_DAYS = 2
SEVERE_GAP_THRESHOLD = 3
SEVERE_GAP_DAYS = 2

COST_EVALUATION_DAYS = 30            # days used to convert daily salary to monthly salary


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
df = df.sort_values("Date").reset_index(drop=True)

required_columns = {
    "Date",
    "RequiredWorkers",
    "CurrentStaff",
    "ProjectedLaborCost",
}

missing = required_columns - set(df.columns)
if missing:
    raise ValueError(
        "Workforce_Planning_Report.csv is missing required column(s): "
        + ", ".join(sorted(missing))
    )


# ==========================================================
# BASIC HELPERS
# ==========================================================

def calculate_gap(required_workers, available_workers):
    """Positive workforce shortage only."""
    return max(int(required_workers) - int(available_workers), 0)


def get_pending_workers(pending_hires):
    return sum(int(item["workers"]) for item in pending_hires)


def clone_pending_hires(pending_hires):
    cloned = deque()
    for item in pending_hires:
        cloned.append(
            {
                "workers": int(item["workers"]),
                "joining_date": pd.to_datetime(item["joining_date"]),
            }
        )
    return cloned


def apply_joining_workers(current_staff, pending_hires, current_date):
    """Move all hires whose joining date has arrived into current staff."""
    joined_today = 0

    while pending_hires and pending_hires[0]["joining_date"] <= current_date:
        hire = pending_hires.popleft()
        workers = int(hire["workers"])
        current_staff += workers
        joined_today += workers

    return int(current_staff), int(joined_today)


def queue_hiring_request(pending_hires, workers, current_date):
    """Schedule workers to join exactly HIRING_LEAD_TIME days later."""
    workers = int(max(workers, 0))
    if workers <= 0:
        return

    joining_date = pd.to_datetime(current_date) + pd.Timedelta(
        days=HIRING_LEAD_TIME
    )

    pending_hires.append(
        {
            "workers": workers,
            "joining_date": joining_date,
        }
    )

    ordered = sorted(pending_hires, key=lambda x: x["joining_date"])
    pending_hires.clear()
    pending_hires.extend(ordered)


def pending_workers_by_date(pending_hires, target_date):
    """Workers already scheduled to join on or before target_date."""
    target_date = pd.to_datetime(target_date)
    return sum(
        int(item["workers"])
        for item in pending_hires
        if pd.to_datetime(item["joining_date"]) <= target_date
    )


# ==========================================================
# COST MODEL
# ==========================================================

def daily_salary_per_worker(projected_labor_cost, required_workers):
    """
    ProjectedLaborCost is the projected DAILY labour cost for the
    required workforce.

    Therefore:
        daily salary / worker = projected daily labour cost
                                 / required workers
    """
    return float(projected_labor_cost) / max(int(required_workers), 1)


def monthly_salary_per_worker(projected_labor_cost, required_workers):
    """
    Convert the daily worker salary into a monthly salary.

        monthly salary = daily salary × 30
    """
    daily_salary = daily_salary_per_worker(
        projected_labor_cost,
        required_workers,
    )

    return daily_salary * COST_EVALUATION_DAYS


def hourly_salary_rate(projected_labor_cost, required_workers):
    """
    Convert the daily worker salary into an hourly salary.

        hourly salary = daily salary / 8 working hours
    """
    daily_salary = daily_salary_per_worker(
        projected_labor_cost,
        required_workers,
    )

    return daily_salary / WORKING_HOURS_PER_DAY


def hiring_cost(workers, projected_labor_cost, required_workers):
    """Hiring cost = one full month salary for each newly hired worker."""
    workers = int(max(workers, 0))

    return round(
        workers
        * monthly_salary_per_worker(
            projected_labor_cost,
            required_workers,
        ),
        2,
    )


def overtime_cost(gap, projected_labor_cost, required_workers):
    """
    Same-day overtime cost.

    Each missing worker is assumed to require a full normal
    working day of overtime coverage:
        gap × 8 hours × hourly salary × 1.5
    """
    gap = int(max(gap, 0))

    if gap <= 0:
        return 0.0

    hourly_rate = hourly_salary_rate(
        projected_labor_cost,
        required_workers,
    )

    overtime_hours = (
        gap
        * WORKING_HOURS_PER_DAY
    )

    return round(
        overtime_hours
        * hourly_rate
        * OVERTIME_MULTIPLIER,
        2,
    )


def hybrid_cost(gap, projected_labor_cost, required_workers):
    """
    Hybrid is for an isolated severe shortage (gap > 2) that does not
    qualify for advance hiring.

    The hybrid response uses:
      - overtime for up to 2 missing workers
      - temporary same-day coverage for the remaining workers

    The temporary component uses the normal hourly labour rate because
    no separate temporary-worker rate exists in the input data.
    """
    gap = int(max(gap, 0))

    if gap <= 0:
        return 0.0

    hourly_rate = hourly_salary_rate(
        projected_labor_cost,
        required_workers,
    )

    overtime_workers = min(gap, 2)
    temporary_workers = max(gap - 2, 0)

    overtime_component = (
        overtime_workers
        * MAX_OVERTIME_PER_WORKER
        * hourly_rate
        * OVERTIME_MULTIPLIER
    )

    temporary_component = (
        temporary_workers
        * MAX_OVERTIME_PER_WORKER
        * hourly_rate
    )

    return round(
        overtime_component + temporary_component,
        2,
    )


# ==========================================================
# GAP-RUN DETECTION
# ==========================================================

def find_positive_gap_runs(gaps):
    """
    Return consecutive positive-gap runs.

    Each result contains:
        start offset
        end offset
        run length
        maximum gap
    """
    runs = []
    start = None

    for offset, gap in enumerate(gaps):
        if gap >= 1 and start is None:
            start = offset

        if start is not None:
            is_last = offset == len(gaps) - 1
            gap_ended = gap == 0

            if gap_ended or is_last:
                end = offset - 1 if gap_ended else offset

                run = gaps[start : end + 1]

                runs.append(
                    {
                        "start": start,
                        "end": end,
                        "length": end - start + 1,
                        "maximum_gap": int(max(run)),
                    }
                )

                start = None

    return runs


def find_severe_gap_runs(gaps):
    """
    Return consecutive runs where gap >= SEVERE_GAP_THRESHOLD.

    This is deliberately separate from normal positive-gap runs because:
      - gap 1 for 3+ days -> Hiring
      - gap 3+ for 2+ days -> Hiring
      - isolated gap 3+ -> Hybrid
    """
    runs = []
    start = None

    for offset, gap in enumerate(gaps):
        if gap >= SEVERE_GAP_THRESHOLD and start is None:
            start = offset

        if start is not None:
            is_last = offset == len(gaps) - 1
            run_ended = gap < SEVERE_GAP_THRESHOLD

            if run_ended or is_last:
                end = offset - 1 if run_ended else offset

                run = gaps[start : end + 1]

                runs.append(
                    {
                        "start": start,
                        "end": end,
                        "length": end - start + 1,
                        "maximum_gap": int(max(run)),
                    }
                )

                start = None

    return runs


# ==========================================================
# 14-DAY LOOKAHEAD
# ==========================================================

def analyse_lookahead(
    dataframe,
    current_index,
    current_staff,
    pending_hires
):
    """
    Analyse the next PLANNING_HORIZON days while respecting the same
    monthly-reset rule used by the actual workforce simulation.

    Important:
        A future month boundary resets simulated staff to the default
        baseline and clears pending hires. This prevents the lookahead
        from incorrectly carrying a high-demand month's workforce into
        the following month.
    """

    start_date = pd.to_datetime(
        dataframe.at[current_index, "Date"]
    )

    default_staff = int(
        dataframe["CurrentStaff"].iloc[0]
    )

    future = dataframe.iloc[
        current_index:
        min(
            current_index + PLANNING_HORIZON,
            len(dataframe)
        )
    ].copy()

    future["Date"] = pd.to_datetime(
        future["Date"]
    )

    # Simulated state for the lookahead.
    simulated_staff = int(current_staff)

    # Copy pending hires so lookahead never mutates the real queue.
    simulated_pending = deque(
        list(pending_hires)
    )

    current_month = start_date.to_period("M")

    daily_gaps = []
    daily_required = []
    daily_staff = []

    gap_days = 0
    total_gap = 0
    maximum_gap = 0

    for row_index, row in future.iterrows():

        date = pd.to_datetime(
            row["Date"]
        )

        month_key = date.to_period("M")

        # ----------------------------------------------------------
        # FUTURE MONTHLY RESET
        # ----------------------------------------------------------
        # This mirrors the actual simulation exactly:
        # at the start of a new month, workforce returns to the
        # default baseline and pending hires are cleared.
        # ----------------------------------------------------------
        if month_key != current_month:

            current_month = month_key

            simulated_staff = default_staff

            simulated_pending.clear()

        # Apply hires whose lead time has completed.
        simulated_staff, _ = apply_joining_workers(
            simulated_staff,
            simulated_pending,
            date,
        )

        required = int(
            row["RequiredWorkers"]
        )

        gap = calculate_gap(
            required,
            simulated_staff,
        )

        daily_required.append(required)
        daily_staff.append(simulated_staff)
        daily_gaps.append(gap)

        if gap > 0:

            gap_days += 1

            total_gap += gap

            maximum_gap = max(
                maximum_gap,
                gap,
            )

        # ----------------------------------------------------------
        # Do NOT automatically create a hiring decision here.
        # analyse_lookahead() is analysis only. Actual hiring is
        # decided later by generate_decision().
        # ----------------------------------------------------------

    first_shortage_index = None

    for row_index, gap in zip(
        future.index,
        daily_gaps,
    ):

        if gap > 0:

            first_shortage_index = row_index

            break

    # Convert the simulated gap series into the run structures
    # consumed by the hiring-decision layer.
    positive_runs = find_positive_gap_runs(
        daily_gaps
    )

    severe_runs = find_severe_gap_runs(
        daily_gaps
    )

    dates = [
        pd.to_datetime(date)
        for date in future["Date"].tolist()
    ]

    return {
        "Dates": dates,

        "DailyGaps": daily_gaps,

        "DailyRequired": daily_required,

        "DailyStaff": daily_staff,

        "PositiveRuns": positive_runs,

        "SevereRuns": severe_runs,

        "GapDays": gap_days,

        "TotalGap": total_gap,

        "MaximumGap": maximum_gap,

        "AverageGap": round(
            total_gap /
            max(len(daily_gaps), 1),
            2,
        ),

        "FirstShortageDay":
            first_shortage_index,

        "WorkersNeededToday":
            (
                daily_gaps[0]
                if daily_gaps
                else 0
            ),
    }

def choose_hiring_candidate(lookahead):
    """
    Select the earliest future run that qualifies for advance hiring.

    Rule A:
        gap >= 1 for at least 2 consecutive days.

    Rule B:
        gap >= 3 for at least 2 consecutive days.

    An isolated severe gap is NOT a hiring candidate.
    """
    candidates = []

    # Rule A: persistent shortage.
    for run in lookahead["PositiveRuns"]:
        if run["length"] >= PERSISTENT_GAP_DAYS:
            candidates.append(
                {
                    "kind": "Persistent",
                    "start": run["start"],
                    "end": run["end"],
                    "length": run["length"],
                    "maximum_gap": run["maximum_gap"],
                }
            )

    # Rule B: severe shortage lasting at least 2 days.
    for run in lookahead["SevereRuns"]:
        if run["length"] >= SEVERE_GAP_DAYS:
            candidates.append(
                {
                    "kind": "Severe Persistent",
                    "start": run["start"],
                    "end": run["end"],
                    "length": run["length"],
                    "maximum_gap": run["maximum_gap"],
                }
            )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            item["start"],
            -item["maximum_gap"],
        )
    )

    return candidates[0]


# ==========================================================
# DECISION ENGINE
# ==========================================================

def generate_decision(
    dataframe,
    current_index,
    current_staff,
    pending_hires,
):
    current_date = pd.to_datetime(
        dataframe.at[current_index, "Date"]
    )

    required_today = int(
        dataframe.at[current_index, "RequiredWorkers"]
    )

    projected_labor_cost = float(
        dataframe.at[current_index, "ProjectedLaborCost"]
    )

    current_gap = calculate_gap(
        required_today,
        current_staff,
    )

    lookahead = analyse_lookahead(
        dataframe,
        current_index,
        current_staff,
        pending_hires,
    )

    hiring_candidate = choose_hiring_candidate(
        lookahead
    )

    pending_workers = get_pending_workers(
        pending_hires
    )

    recommended_strategy = "No Action"
    alternative_strategy = "None"
    implementation_time = "No immediate action"
    decision_reason = (
        "Current workforce is sufficient and no hiring trigger "
        "is due today."
    )

    workers_to_hire = 0
    first_gap_date = None
    recommended_hire_date = None
    days_before_gap = 0

    hiring_decision_cost = 0.0
    overtime_decision_cost = 0.0
    hybrid_decision_cost = 0.0
    decision_cost = 0.0
    alternative_cost = 0.0

    # ------------------------------------------------------
    # ADVANCE HIRING
    # ------------------------------------------------------

    if hiring_candidate is not None:
        first_offset = hiring_candidate["start"]
        last_offset = hiring_candidate["end"]

        first_gap_date = lookahead["Dates"][first_offset]
        last_gap_date = lookahead["Dates"][last_offset]

        recommended_hire_date = (
            first_gap_date
            - pd.Timedelta(days=HIRING_LEAD_TIME)
        )

        days_before_gap = int(
            (first_gap_date - current_date).days
        )

        # We can only make an advance-hiring decision before
        # the shortage begins. If the hire date has passed,
        # the immediate shortage rules take over.
        hire_window_open = (
            current_date >= recommended_hire_date
            and current_date < first_gap_date
        )

        if hire_window_open:
            # Maximum shortage in the qualifying run.
            target_workers = int(
                hiring_candidate["maximum_gap"]
            )

            # Existing hires that will already be present by
            # the first shortage date reduce the new hiring need.
            already_arriving = pending_workers_by_date(
                pending_hires,
                first_gap_date,
            )

            workers_to_hire = max(
                target_workers - already_arriving,
                0,
            )

            if workers_to_hire > 0:
                recommended_strategy = "Hiring"
                implementation_time = "Hire today"

                hiring_decision_cost = hiring_cost(
                    workers_to_hire,
                    projected_labor_cost,
                    required_today,
                )

                decision_cost = hiring_decision_cost

                # Comparison against covering the maximum future
                # gap temporarily.
                future_max_gap = target_workers

                if future_max_gap <= 2:
                    alternative_strategy = "Overtime"
                    alternative_cost = overtime_cost(
                        future_max_gap,
                        projected_labor_cost,
                        required_today,
                    )
                else:
                    alternative_strategy = "Hybrid"
                    alternative_cost = hybrid_cost(
                        future_max_gap,
                        projected_labor_cost,
                        required_today,
                    )

                if hiring_candidate["kind"] == "Persistent":
                    decision_reason = (
                        f"Forecast shows a workforce gap of at least "
                        f"1 worker for {hiring_candidate['length']} "
                        f"consecutive days from "
                        f"{first_gap_date:%d %b %Y} to "
                        f"{last_gap_date:%d %b %Y}. "
                        f"Hiring {workers_to_hire} worker(s) now "
                        f"provides the required workforce before the "
                        f"shortage begins."
                    )
                else:
                    decision_reason = (
                        f"Forecast shows a severe gap of at least "
                        f"{SEVERE_GAP_THRESHOLD} workers for "
                        f"{hiring_candidate['length']} consecutive "
                        f"days from {first_gap_date:%d %b %Y} to "
                        f"{last_gap_date:%d %b %Y}. "
                        f"Hiring {workers_to_hire} worker(s) now "
                        f"provides the required workforce before the "
                        f"shortage begins."
                    )

    # ------------------------------------------------------
    # SAME-DAY OVERTIME
    # ------------------------------------------------------

    if (
        recommended_strategy == "No Action"
        and current_gap > 0
    ):
        if current_gap <= 2:
            recommended_strategy = "Overtime"
            alternative_strategy = "Hiring"
            implementation_time = "Immediate / same day"

            overtime_decision_cost = overtime_cost(
                current_gap,
                projected_labor_cost,
                required_today,
            )

            alternative_cost = hiring_cost(
                current_gap,
                projected_labor_cost,
                required_today,
            )

            decision_cost = overtime_decision_cost

            decision_reason = (
                f"Current workforce shortage is {current_gap} "
                f"worker(s). The gap is <= 2, so same-day "
                f"overtime is recommended instead of immediate hiring."
            )

        # --------------------------------------------------
        # SAME-DAY HYBRID
        # --------------------------------------------------

        else:
            recommended_strategy = "Hybrid"
            alternative_strategy = "Hiring"
            implementation_time = "Immediate / same day"

            hybrid_decision_cost = hybrid_cost(
                current_gap,
                projected_labor_cost,
                required_today,
            )

            alternative_cost = hiring_cost(
                current_gap,
                projected_labor_cost,
                required_today,
            )

            decision_cost = hybrid_decision_cost

            decision_reason = (
                f"Current workforce shortage is {current_gap} "
                f"worker(s). The gap is > 2 but does not qualify "
                f"for advance hiring at this point, so a hybrid "
                f"temporary coverage strategy is recommended."
            )

    # ------------------------------------------------------
    # FUTURE QUALIFYING SHORTAGE, BUT NOT YET HIRING DAY
    # ------------------------------------------------------

    if (
        recommended_strategy == "No Action"
        and hiring_candidate is not None
    ):
        first_gap_date = lookahead["Dates"][
            hiring_candidate["start"]
        ]
        last_gap_date = lookahead["Dates"][
            hiring_candidate["end"]
        ]

        recommended_hire_date = (
            first_gap_date
            - pd.Timedelta(days=HIRING_LEAD_TIME)
        )

        days_before_gap = int(
            (first_gap_date - current_date).days
        )

        if current_date < recommended_hire_date:
            decision_reason = (
                f"A qualifying workforce shortage is forecast "
                f"from {first_gap_date:%d %b %Y} to "
                f"{last_gap_date:%d %b %Y}. "
                f"The hiring decision is scheduled for "
                f"{recommended_hire_date:%d %b %Y}; no action "
                f"is required yet."
            )

        elif (
            current_date >= first_gap_date
            and pending_workers > 0
        ):
            decision_reason = (
                f"Workers are already scheduled to join before or "
                f"during the projected shortage. No duplicate hiring "
                f"decision is created."
            )

    estimated_saving = round(
        max(alternative_cost - decision_cost, 0),
        2,
    )

    return {
        "CurrentGap": current_gap,
        "GapDays14": lookahead["GapDays"],
        "TotalGap14": lookahead["TotalGap"],
        "MaximumGap14": lookahead["MaximumGap"],
        "AverageGap14": lookahead["AverageGap"],
        "PendingWorkers": pending_workers,
        "WorkersToHire": workers_to_hire,
        "FirstGapDate": first_gap_date,
        "RecommendedHireDate": recommended_hire_date,
        "DaysBeforeGap": days_before_gap,
        "HiringCost": round(hiring_decision_cost, 2),
        "OvertimeCost": round(overtime_decision_cost, 2),
        "HybridCost": round(hybrid_decision_cost, 2),
        "DecisionCost": round(decision_cost, 2),
        "RecommendedStrategy": recommended_strategy,
        "AlternativeStrategy": alternative_strategy,
        "AlternativeCost": round(alternative_cost, 2),
        "ImplementationTime": implementation_time,
        "DecisionReason": decision_reason,
        "EstimatedSaving": estimated_saving,
    }


# ==========================================================
# INITIALISE OUTPUT
# ==========================================================

decision = df.copy()

new_columns = [
    "CurrentStaff",
    "CurrentGap",
    "GapDays14",
    "TotalGap14",
    "MaximumGap14",
    "AverageGap14",
    "PendingWorkers",
    "WorkersToHire",
    "FirstGapDate",
    "RecommendedHireDate",
    "DaysBeforeGap",
    "HiringCost",
    "OvertimeCost",
    "HybridCost",
    "DecisionCost",
    "RecommendedStrategy",
    "AlternativeStrategy",
    "AlternativeCost",
    "ImplementationTime",
    "DecisionReason",
    "EstimatedSaving",
]

for column in new_columns:
    if column in {
        "RecommendedStrategy",
        "AlternativeStrategy",
        "ImplementationTime",
        "DecisionReason",
        "FirstGapDate",
        "RecommendedHireDate",
    }:
        decision[column] = ""
    else:
        decision[column] = 0.0


# ==========================================================
# RUN ENGINE
# ==========================================================

default_staff = int(
    df["CurrentStaff"].iloc[0]
)

current_staff = default_staff
pending_hires = deque()
current_month = None

print("=" * 70)
print("Predictive Workforce Decision Engine - Business Rule Version")
print("=" * 70)

for index in range(len(df)):
    current_date = pd.to_datetime(
        df.at[index, "Date"]
    )

    month_key = current_date.to_period("M")

    # ==========================================================
    # MONTHLY WORKFORCE RESET
    # ==========================================================
    # Workforce planning and labour cost are intentionally treated
    # independently for each month.
    #
    # At the beginning of every new month:
    #   1. Reset actual staff to the default baseline staff.
    #   2. Clear pending hires from the previous month.
    #
    # This prevents workers hired for one month from becoming
    # permanent excess cost in the following month.
    # ==========================================================
    if current_month is None:
        current_month = month_key

    elif month_key != current_month:
        current_month = month_key

        # Monthly reset is intentional:
        # workforce returns to the default baseline for the new month.
        #
        # IMPORTANT:
        # Do not clear pending hires here. A hire scheduled in the
        # previous month may have been deliberately planned to become
        # available at the beginning of this new month.
        current_staff = default_staff

    # Employees whose hiring lead time has completed become
    # available today, after the monthly reset has been applied.
    current_staff, _ = apply_joining_workers(
        current_staff,
        pending_hires,
        current_date,
    )

    result = generate_decision(
        df,
        index,
        current_staff,
        pending_hires,
    )

    # If today is the hiring decision date, schedule the
    # workers to join exactly 7 days from today.
    if (
        result["RecommendedStrategy"] == "Hiring"
        and result["WorkersToHire"] > 0
    ):
        queue_hiring_request(
            pending_hires,
            result["WorkersToHire"],
            current_date,
        )

    decision.at[index, "CurrentStaff"] = current_staff
    decision.at[index, "CurrentGap"] = result["CurrentGap"]
    decision.at[index, "GapDays14"] = result["GapDays14"]
    decision.at[index, "TotalGap14"] = result["TotalGap14"]
    decision.at[index, "MaximumGap14"] = result["MaximumGap14"]
    decision.at[index, "AverageGap14"] = result["AverageGap14"]
    decision.at[index, "PendingWorkers"] = get_pending_workers(
        pending_hires
    )
    decision.at[index, "WorkersToHire"] = result["WorkersToHire"]

    decision.at[index, "FirstGapDate"] = (
        result["FirstGapDate"].strftime("%Y-%m-%d")
        if result["FirstGapDate"] is not None
        else ""
    )

    decision.at[index, "RecommendedHireDate"] = (
        result["RecommendedHireDate"].strftime("%Y-%m-%d")
        if result["RecommendedHireDate"] is not None
        else ""
    )

    decision.at[index, "DaysBeforeGap"] = result["DaysBeforeGap"]
    decision.at[index, "HiringCost"] = result["HiringCost"]
    decision.at[index, "OvertimeCost"] = result["OvertimeCost"]
    decision.at[index, "HybridCost"] = result["HybridCost"]
    decision.at[index, "DecisionCost"] = result["DecisionCost"]
    decision.at[index, "RecommendedStrategy"] = result[
        "RecommendedStrategy"
    ]
    decision.at[index, "AlternativeStrategy"] = result[
        "AlternativeStrategy"
    ]
    decision.at[index, "AlternativeCost"] = result[
        "AlternativeCost"
    ]
    decision.at[index, "ImplementationTime"] = result[
        "ImplementationTime"
    ]
    decision.at[index, "DecisionReason"] = result[
        "DecisionReason"
    ]
    decision.at[index, "EstimatedSaving"] = result[
        "EstimatedSaving"
    ]


# ==========================================================
# KPI REPORT
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
            "Total Hiring Decision Cost",
            "Total Overtime Decision Cost",
            "Total Hybrid Decision Cost",
            "Total Decision Cost",
        ],
        "Value": [
            len(decision),
            int(
                (decision["RecommendedStrategy"] == "Hiring").sum()
            ),
            int(
                (decision["RecommendedStrategy"] == "Overtime").sum()
            ),
            int(
                (decision["RecommendedStrategy"] == "Hybrid").sum()
            ),
            int(
                (decision["RecommendedStrategy"] == "No Action").sum()
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
            round(
                decision.loc[
                    decision["RecommendedStrategy"] == "Hiring",
                    "DecisionCost",
                ].sum(),
                2,
            ),
            round(
                decision.loc[
                    decision["RecommendedStrategy"] == "Overtime",
                    "DecisionCost",
                ].sum(),
                2,
            ),
            round(
                decision.loc[
                    decision["RecommendedStrategy"] == "Hybrid",
                    "DecisionCost",
                ].sum(),
                2,
            ),
            round(
                decision["DecisionCost"].sum(),
                2,
            ),
        ],
    }
)


# ==========================================================
# MODEL ASSUMPTIONS
# ==========================================================

decision_assumptions = pd.DataFrame(
    {
        "Assumption": [
            "Planning Horizon",
            "Monthly Workforce Reset",
            "Default Workforce",
            "Hiring Lead Time",
            "Hiring Trigger",
                        "Overtime Rule",
            "Hybrid Rule",
            "Hiring Cost Basis",
            "Overtime Cost Basis",
            "Working Hours Per Day",
            "Maximum Overtime Hours Per Worker",
            "Overtime Pay Multiplier",
            "Pending Hire Handling",
        ],
        "Value": [
            "14 Days Ahead",
            "Enabled at the start of every month",
            default_staff,
            "7 Days",
            "Gap >= 1 for 2 or more consecutive days",
                        "Same-day gap of 1 or 2 workers; temporary coverage",
            "Same-day isolated gap > 2 workers",
            "One month salary per newly hired worker",
            "Workforce gap x overtime hours x hourly rate x 1.5",
            WORKING_HOURS_PER_DAY,
            MAX_OVERTIME_PER_WORKER,
            OVERTIME_MULTIPLIER,
            "Pending hires scheduled for future dates are retained across month reset; hires are processed FIFO",
        ],
    }
)


# ==========================================================
# SAVE OUTPUTS
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
# CONSOLE REPORT
# ==========================================================

print()
print("=" * 60)
print("Workforce Decision Engine Completed")
print("=" * 60)

print("\nDecision Report")

print(
    decision[
        [
            "Date",
            "RequiredWorkers",
            "CurrentStaff",
            "CurrentGap",
            "RecommendedStrategy",
            "WorkersToHire",
            "FirstGapDate",
            "RecommendedHireDate",
            "DecisionCost",
        ]
    ].to_string(index=False)
)

print("\nKPI Report")
print(
    decision_kpis.to_string(index=False)
)

print("\nModel Assumptions")
print(
    decision_assumptions.to_string(index=False)
)

print("\nSaved Files")
print(OUTPUT_REPORT)
print(OUTPUT_KPI)
print(OUTPUT_ASSUMPTIONS)

print("\nStrategy Distribution")
print(
    decision["RecommendedStrategy"].value_counts()
)