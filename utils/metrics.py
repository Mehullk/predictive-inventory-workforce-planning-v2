import pandas as pd

from utils.loader import (
    forecast30,
    forecast90,
    metrics,
    inventory_kpis,
    workforce,
    workforce_kpis,
    purchase_orders,
)


def executive_metrics():


    accuracy = float(
        metrics["ForecastAccuracy"].iloc[0]
    )

    sales30 = float(
        forecast30["Forecast"].sum()
    )

    sales90 = float(
        forecast90["PredictedUnitsSold"].sum()
    )


  

    inventory = (
        inventory_kpis
        .set_index("KPI")["Value"]
    )


    
    workforce_metrics = (
        workforce_kpis
        .set_index("Metric")["Value"]
    )



    workers = int(
        workforce["RequiredWorkers"].max()
    )

    current_staff = int(
        workforce["CurrentStaff"].iloc[0]
    )


 

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


   

    estimated_saving = workforce_metrics.get(
        "Total Estimated Saving",
        0
    )



    utilization = workforce_metrics.get(
        "Average Worker Utilization",
        workforce_metrics.get(
            "Average Worker Utilization(%)",
            0
        )
    )


   

    opening_stock = float(
        inventory["OpeningStock"]
    )

    ending_stock = float(
        inventory["EndingStock"]
    )

    service_level = float(
        inventory["ServiceLevel"]
    ) * 100

    purchase_orders_count = float(
        inventory["GeneratedPurchaseOrders"]
    )


   

    forecast_dates = pd.to_datetime(
        forecast90["Date"],
        errors="coerce"
    ).dropna()

    forecast_start = (
        forecast_dates.min().strftime("%d %b %Y")
        if not forecast_dates.empty
        else "N/A"
    )

    forecast_end = (
        forecast_dates.max().strftime("%d %b %Y")
        if not forecast_dates.empty
        else "N/A"
    )

    average_daily_demand = (
        float(forecast90["PredictedUnitsSold"].mean())
        if "PredictedUnitsSold" in forecast90.columns and not forecast90.empty
        else 0.0
    )

    
    engine_po_dates = pd.to_datetime(
        purchase_orders.loc[
            purchase_orders["Source"].astype(str).str.strip().eq("Engine generated"),
            "PO_Date"
        ],
        errors="coerce"
    ).dropna().sort_values()

    if len(engine_po_dates) >= 2:
        average_days_between_orders = float(
            engine_po_dates.diff().dt.days.dropna().mean()
        )
    else:
        average_days_between_orders = 0.0


 

    return {

       
        "accuracy": accuracy,

        "sales30": sales30,

        "sales90": sales90,

        "average_daily_demand": average_daily_demand,

        "forecast_start": forecast_start,

        "forecast_end": forecast_end,

        "average_days_between_orders": average_days_between_orders,



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


      

        "opening_stock": opening_stock,

        "ending_stock": ending_stock,

        "service_level": service_level,

        "purchase_orders": purchase_orders_count,

    }