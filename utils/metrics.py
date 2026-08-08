import pandas as pd

from utils.loader import (
    forecast30,
    forecast90,
    metrics,
    inventory_kpis,
    workforce,
    workforce_kpis,
)


def executive_metrics():

    # ============================================================
    # FORECAST METRICS
    # ============================================================

    accuracy = float(
        metrics["ForecastAccuracy"].iloc[0]
    )

    sales30 = float(
        forecast30["Forecast"].sum()
    )

    sales90 = float(
        forecast90["PredictedUnitsSold"].sum()
    )


    # ============================================================
    # INVENTORY METRICS
    # ============================================================

    inventory = (
        inventory_kpis
        .set_index("KPI")["Value"]
    )


    # ============================================================
    # WORKFORCE METRICS
    # ============================================================

    workforce_metrics = (
        workforce_kpis
        .set_index("Metric")["Value"]
    )


    # ------------------------------------------------------------
    # Basic workforce values
    # ------------------------------------------------------------

    workers = int(
        workforce["RequiredWorkers"].max()
    )

    current_staff = int(
        workforce["CurrentStaff"].iloc[0]
    )


    # ------------------------------------------------------------
    # Workforce gap
    # ------------------------------------------------------------

    if "WorkforceGap" in workforce.columns:

        maximum_workforce_gap = int(
            workforce["WorkforceGap"].max()
        )

        average_workforce_gap = float(
            workforce["WorkforceGap"].mean()
        )

    else:

        maximum_workforce_gap = workforce_metrics.get(
            "Maximum Workforce Gap",
            workforce_metrics.get(
                "Maximum Staff Gap",
                0
            )
        )

        average_workforce_gap = workforce_metrics.get(
            "Average Workforce Gap",
            workforce_metrics.get(
                "Average Staff Gap",
                0
            )
        )


    # ------------------------------------------------------------
    # Decision counts
    # ------------------------------------------------------------

    if "RecommendedStrategy" in workforce.columns:

        strategy_counts = (
            workforce["RecommendedStrategy"]
            .value_counts()
        )

        hiring_decisions = int(
            strategy_counts.get("Hiring", 0)
        )

        overtime_decisions = int(
            strategy_counts.get("Overtime", 0)
        )

        hybrid_decisions = int(
            strategy_counts.get("Hybrid", 0)
        )

        no_action_decisions = int(
            strategy_counts.get("No Action", 0)
        )

    else:

        hiring_decisions = workforce_metrics.get(
            "Hiring Decisions",
            workforce_metrics.get(
                "Hiring Recommendations",
                0
            )
        )

        overtime_decisions = workforce_metrics.get(
            "Overtime Decisions",
            workforce_metrics.get(
                "Overtime Recommendations",
                0
            )
        )

        hybrid_decisions = workforce_metrics.get(
            "Hybrid Decisions",
            workforce_metrics.get(
                "Hybrid Recommendations",
                0
            )
        )

        no_action_decisions = workforce_metrics.get(
            "No Action Decisions",
            workforce_metrics.get(
                "No Action Recommendations",
                0
            )
        )


    # ------------------------------------------------------------
    # Pending workers
    # ------------------------------------------------------------

    if "PendingWorkers" in workforce.columns:

        pending_workers = int(
            workforce["PendingWorkers"].max()
        )

    elif "WorkersToHire" in workforce.columns:

        pending_workers = int(
            workforce["WorkersToHire"].max()
        )

    else:

        pending_workers = workforce_metrics.get(
            "Maximum Pending Workers",
            workforce_metrics.get(
                "Maximum Pending Hires",
                0
            )
        )


    # ============================================================
    # DECISION COSTS
    # ============================================================

    # IMPORTANT:
    # Calculate these from the actual Workforce Decision Report.
    # This prevents the dashboard from showing ₹0 when the
    # decision table contains real costs.

    if "DecisionCost" in workforce.columns:

        cost_data = workforce.copy()

        cost_data["DecisionCost"] = pd.to_numeric(
            cost_data["DecisionCost"],
            errors="coerce"
        ).fillna(0)

        # Hiring
        hiring_costs = cost_data.loc[
            cost_data["RecommendedStrategy"] == "Hiring",
            "DecisionCost"
        ]

        average_hiring_cost = (
            float(hiring_costs.mean())
            if not hiring_costs.empty
            else 0
        )

        # Overtime
        overtime_costs = cost_data.loc[
            cost_data["RecommendedStrategy"] == "Overtime",
            "DecisionCost"
        ]

        average_overtime_cost = (
            float(overtime_costs.mean())
            if not overtime_costs.empty
            else 0
        )

        # Hybrid
        hybrid_costs = cost_data.loc[
            cost_data["RecommendedStrategy"] == "Hybrid",
            "DecisionCost"
        ]

        average_hybrid_cost = (
            float(hybrid_costs.mean())
            if not hybrid_costs.empty
            else 0
        )

        # Total decision cost
        labour_cost = float(
            cost_data["DecisionCost"].sum()
        )

    else:

        average_hiring_cost = workforce_metrics.get(
            "Average Hiring Cost",
            0
        )

        average_overtime_cost = workforce_metrics.get(
            "Average Overtime Cost",
            0
        )

        average_hybrid_cost = workforce_metrics.get(
            "Average Hybrid Cost",
            0
        )

        labour_cost = workforce_metrics.get(
            "Total Projected Labor Cost",
            0
        )


    # ============================================================
    # ESTIMATED SAVING
    # ============================================================

    estimated_saving = workforce_metrics.get(
        "Total Estimated Saving",
        0
    )


    # ============================================================
    # WORKFORCE UTILIZATION
    # ============================================================

    utilization = workforce_metrics.get(
        "Average Worker Utilization",
        workforce_metrics.get(
            "Average Worker Utilization(%)",
            0
        )
    )


    # ============================================================
    # INVENTORY VALUES
    # ============================================================

    opening_stock = float(
        inventory["OpeningStock"]
    )

    ending_stock = float(
        inventory["EndingStock"]
    )

    service_level = float(
        inventory["ServiceLevel"]
    ) * 100

    purchase_orders = float(
        inventory["GeneratedPurchaseOrders"]
    )


    # ============================================================
    # FINAL METRICS
    # ============================================================

    return {

        # --------------------------------------------------------
        # Forecast
        # --------------------------------------------------------

        "accuracy": accuracy,

        "sales30": sales30,

        "sales90": sales90,


        # --------------------------------------------------------
        # Workforce
        # --------------------------------------------------------

        "workers": workers,

        "staff": current_staff,

        "workforce_gap": maximum_workforce_gap,

        "average_workforce_gap": average_workforce_gap,

        "hiring_decisions": int(
            hiring_decisions
        ),

        "overtime_decisions": int(
            overtime_decisions
        ),

        "hybrid_decisions": int(
            hybrid_decisions
        ),

        "no_action_decisions": int(
            no_action_decisions
        ),

        "pending_workers": pending_workers,

        "labour_cost": labour_cost,

        "average_hiring_cost": average_hiring_cost,

        "average_overtime_cost": average_overtime_cost,

        "average_hybrid_cost": average_hybrid_cost,

        "estimated_saving": estimated_saving,

        "utilization": utilization,


        # --------------------------------------------------------
        # Inventory
        # --------------------------------------------------------

        "opening_stock": opening_stock,

        "ending_stock": ending_stock,

        "service_level": service_level,

        "purchase_orders": purchase_orders,

    }