from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd


def ceil_units(value: float) -> int:
    return int(math.ceil(max(0, value)))


def latest_inventory_snapshot(inventory: pd.DataFrame) -> pd.Series:
    inventory = inventory.sort_values(["Product", "Date"])
    return inventory.groupby("Product", as_index=False).tail(1).iloc[0]


def build_open_purchase_orders(
    inventory: pd.DataFrame,
    product: str,
    history_end_date: pd.Timestamp,
) -> list[dict]:
    historical_pos = inventory[
        (inventory["OrderPlaced"].eq(1))
        & (
            inventory["Date"]
            + pd.to_timedelta(
                inventory["SupplierLeadTimeDays"],
                unit="D",
            )
            > history_end_date
        )
    ].copy()

    purchase_orders = []

    for _, row in historical_pos.iterrows():
        po_date = pd.Timestamp(row["Date"])

        purchase_orders.append(
            {
                "PO_ID": f"HIST-{po_date:%Y%m%d}",
                "Product": product,
                "PO_Date": po_date,
                "ExpectedArrivalDate": (
                    po_date
                    + pd.Timedelta(
                        days=int(row["SupplierLeadTimeDays"])
                    )
                ),
                "ActualArrivalDate": pd.NaT,
                "OrderQuantity": int(row["OrderQuantity"]),
                "Status": "Open",
                "Source": "Historical open purchase order",
            }
        )

    return purchase_orders


def calculate_safety_stock(
    forecast_horizon: pd.DataFrame,
    latest_safety_stock: int,
) -> int:
    lead_time_demand = forecast_horizon["Forecast"].sum()
    lead_time_upper_bound = forecast_horizon["Upper95CI"].sum()

    forecast_uncertainty = max(
        0,
        lead_time_upper_bound - lead_time_demand,
    )

    return max(
        latest_safety_stock,
        ceil_units(forecast_uncertainty),
    )


def receive_purchase_orders(
    current_date: pd.Timestamp,
    purchase_orders: list[dict],
) -> int:
    received_quantity = 0

    for po in purchase_orders:
        if (
            po["Status"] == "Open"
            and po["ExpectedArrivalDate"] <= current_date
        ):
            received_quantity += int(po["OrderQuantity"])
            po["Status"] = "Received"
            po["ActualArrivalDate"] = current_date

    return received_quantity


def sum_open_po_quantity(
    purchase_orders: list[dict],
    current_date: pd.Timestamp,
) -> int:
    return sum(
        int(po["OrderQuantity"])
        for po in purchase_orders
        if (
            po["Status"] == "Open"
            and po["ExpectedArrivalDate"] > current_date
        )
    )


def create_purchase_order(
    po_id: str,
    product: str,
    po_date: pd.Timestamp,
    lead_time_days: int,
    order_quantity: int,
) -> dict:
    return {
        "PO_ID": po_id,
        "Product": product,
        "PO_Date": po_date,
        "ExpectedArrivalDate": (
            po_date
            + pd.Timedelta(
                days=lead_time_days
            )
        ),
        "ActualArrivalDate": pd.NaT,
        "OrderQuantity": order_quantity,
        "Status": "Open",
        "Source": "Engine generated",
    }


def format_purchase_orders(
    purchase_orders: list[dict],
) -> pd.DataFrame:
    report = pd.DataFrame(
        purchase_orders
    )

    if report.empty:
        return pd.DataFrame(
            columns=[
                "PO_ID",
                "Product",
                "PO_Date",
                "ExpectedArrivalDate",
                "ActualArrivalDate",
                "OrderQuantity",
                "Status",
                "Source",
            ]
        )

    for column in [
        "PO_Date",
        "ExpectedArrivalDate",
        "ActualArrivalDate",
    ]:
        report[column] = pd.to_datetime(
            report[column]
        ).dt.date

    return report


def calculate_kpis(
    inventory_report: pd.DataFrame,
    purchase_order_report: pd.DataFrame,
    product: str,
    opening_stock: int,
    reorder_point: int,
    lead_time_days: int,
    review_period_days: int,
) -> pd.DataFrame:
    total_demand = inventory_report[
        "DemandUsed"
    ].sum()

    total_fulfilled = inventory_report[
        "FulfilledDemand"
    ].sum()

    generated_pos = purchase_order_report[
        purchase_order_report["Source"].eq(
            "Engine generated"
        )
    ]

    ending_open_pos = purchase_order_report[
        purchase_order_report["Status"].eq(
            "Open"
        )
    ]

    service_level = (
        total_fulfilled / total_demand
        if total_demand > 0
        else 1.0
    )

    return pd.DataFrame(
        [
            (
                "Product",
                product,
                "",
            ),
            (
                "ForecastStartDate",
                inventory_report["Date"].iloc[0],
                "",
            ),
            (
                "ForecastEndDate",
                inventory_report["Date"].iloc[-1],
                "",
            ),
            (
                "OpeningStock",
                opening_stock,
                "units",
            ),
            (
                "EndingStock",
                int(
                    inventory_report[
                        "ClosingStock"
                    ].iloc[-1]
                ),
                "units",
            ),
            (
                "TotalForecastDemandUsed",
                int(total_demand),
                "units",
            ),
            (
                "TotalFulfilledDemand",
                int(total_fulfilled),
                "units",
            ),
            (
                "ServiceLevel",
                round(
                    service_level * 100,
                    2,
                ),
                "%",
            ),
            (
                "StockoutDays",
                int(
                    inventory_report[
                        "StockoutFlag"
                    ].sum()
                ),
                "days",
            ),
            (
                "UnitsShort",
                int(
                    inventory_report[
                        "UnitsShort"
                    ].sum()
                ),
                "units",
            ),
            (
                "GeneratedPurchaseOrders",
                len(generated_pos),
                "count",
            ),
            (
                "GeneratedPOQuantity",
                int(
                    generated_pos[
                        "OrderQuantity"
                    ].sum()
                ),
                "units",
            ),
            (
                "EndingOpenPurchaseOrders",
                len(ending_open_pos),
                "count",
            ),
            (
                "EndingOpenPOQuantity",
                int(
                    ending_open_pos[
                        "OrderQuantity"
                    ].sum()
                ),
                "units",
            ),
            (
                "AverageClosingStock",
                round(
                    inventory_report[
                        "ClosingStock"
                    ].mean(),
                    2,
                ),
                "units",
            ),
            (
                "AverageDailyHoldingCost",
                round(
                    inventory_report[
                        "DailyHoldingCost"
                    ].mean(),
                    2,
                ),
                "currency/day",
            ),
            (
                "ReorderPointUsed",
                reorder_point,
                "units",
            ),
            (
                "LeadTimeDaysUsed",
                lead_time_days,
                "days",
            ),
            (
                "ReviewPeriodDaysUsed",
                review_period_days,
                "days",
            ),
        ],
        columns=[
            "KPI",
            "Value",
            "Unit",
        ],
    )


def planning_assumptions(
    history_end_date: pd.Timestamp,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            (
                "Starting inventory",
                f"Latest row in inventory.csv: {history_end_date.date()}",
            ),
            (
                "Demand",
                "Forecast is rounded up to whole units.",
            ),
            (
                "Opening stock",
                "Opening stock equals previous day's closing stock.",
            ),
            (
                "Closing stock",
                "Opening stock + received PO quantity - demand used.",
            ),
            (
                "Inventory position",
                "Closing stock + open purchase order quantity.",
            ),
            (
                "Lead-time demand",
                "Sum of forecast demand over supplier lead time.",
            ),
            (
                "Safety stock",
                "Maximum of latest inventory safety stock and lead-time forecast uncertainty.",
            ),
            (
                "Shortage prediction",
                "Projected inventory after lead time below safety stock.",
            ),
            (
                "PO duplicate check",
                "If an open PO already exists, no new PO is created.",
            ),
            (
                "PO quantity",
                "Covers lead-time demand + review-period demand + safety stock.",
            ),
        ],
        columns=[
            "Assumption",
            "Rule",
        ],
    )


def run_inventory_engine(
    inventory_path: Path,
    forecast_path: Path,
    output_dir: Path,
    review_period_days: int = 14,
) -> None:
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    inventory = pd.read_csv(
        inventory_path,
        parse_dates=["Date"],
    )

    forecast = pd.read_csv(
        forecast_path,
        parse_dates=["Date"],
    ).reset_index(drop=True)

    required_inventory_columns = [
        "Date",
        "Product",
        "StockOnHand",
        "ReorderPoint",
        "SafetyStock",
        "OrderPlaced",
        "OrderQuantity",
        "SupplierLeadTimeDays",
        "DailyHoldingCost",
    ]

    missing_inventory = [
        column
        for column in required_inventory_columns
        if column not in inventory.columns
    ]

    if missing_inventory:
        raise ValueError(
            f"Missing inventory columns: {missing_inventory}"
        )

    required_forecast_columns = [
        "Date",
        "Forecast",
        "Lower95CI",
        "Upper95CI",
    ]

    missing_forecast = [
        column
        for column in required_forecast_columns
        if column not in forecast.columns
    ]

    if missing_forecast:
        raise ValueError(
            f"Missing forecast columns: {missing_forecast}"
        )

    if len(forecast) != 90:
        raise ValueError(
            f"Expected 90 forecast rows, found {len(forecast)}."
        )

    forecast = forecast.sort_values(
        "Date"
    ).reset_index(drop=True)

    latest = latest_inventory_snapshot(
        inventory
    )

    product = str(
        latest["Product"]
    )

    history_end_date = pd.Timestamp(
        latest["Date"]
    )

    stock = int(
        latest["StockOnHand"]
    )

    reorder_point = int(
        latest["ReorderPoint"]
    )

    latest_safety_stock = int(
        latest["SafetyStock"]
    )

    lead_time_days = int(
        round(
            float(
                latest[
                    "SupplierLeadTimeDays"
                ]
            )
        )
    )

    holding_cost_per_unit = (
        inventory["DailyHoldingCost"].sum()
        /
        inventory[
            "StockOnHand"
        ].clip(lower=1).sum()
    )

    purchase_orders = build_open_purchase_orders(
        inventory,
        product,
        history_end_date,
    )

    pending_orders = purchase_orders.copy()

    daily_rows = []

    for day_index, forecast_row in forecast.iterrows():
        current_date = pd.Timestamp(
            forecast_row["Date"]
        )

        opening_stock = stock

        received_quantity = receive_purchase_orders(
            current_date,
            pending_orders,
        )

        stock += received_quantity

        forecast_demand = float(
            forecast_row["Forecast"]
        )

        demand_units = ceil_units(
            forecast_demand
        )

        fulfilled_demand = min(
            stock,
            demand_units,
        )

        units_short = max(
            0,
            demand_units - stock,
        )

        stock = max(
            0,
            stock - demand_units,
        )

        lead_time_horizon = forecast.iloc[
            day_index + 1 :
            day_index + 1 + lead_time_days
        ]

        if len(lead_time_horizon) < lead_time_days:
            lead_time_horizon = forecast.iloc[
                day_index :
                day_index + lead_time_days
            ]

        lead_time_demand = float(
            lead_time_horizon[
                "Forecast"
            ].sum()
        )

        safety_stock = calculate_safety_stock(
            lead_time_horizon,
            latest_safety_stock,
        )

        open_po_quantity = sum_open_po_quantity(
            pending_orders,
            current_date,
        )

        inventory_position = (
            stock
            + open_po_quantity
        )

        projected_inventory = (
            inventory_position
            - ceil_units(
                lead_time_demand
            )
        )

        need_replenishment = (
            inventory_position <= reorder_point
            or projected_inventory < safety_stock
        )

        open_po_available = (
            open_po_quantity > 0
        )

        created_po_id = ""
        order_quantity_created = 0
        action = "Do Nothing"

        if (
            need_replenishment
            and open_po_available
        ):
            action = (
                "Do Nothing - Open PO Available"
            )

        elif need_replenishment:
            review_horizon = forecast.iloc[
                day_index
                + 1
                + lead_time_days :
                day_index
                + 1
                + lead_time_days
                + review_period_days
            ]

            if review_horizon.empty:
                review_horizon = forecast.iloc[
                    day_index + 1 :
                ]

            review_period_demand = float(
                review_horizon[
                    "Forecast"
                ].sum()
            )

            target_inventory = ceil_units(
                lead_time_demand
                + review_period_demand
                + safety_stock
            )

            order_quantity_created = max(
                0,
                target_inventory
                - inventory_position,
            )

            if order_quantity_created > 0:
                created_po_id = (
                    f"PO-{current_date:%Y%m%d}-"
                    f"{len(purchase_orders) + 1:03d}"
                )

                new_po = create_purchase_order(
                    po_id=created_po_id,
                    product=product,
                    po_date=current_date,
                    lead_time_days=lead_time_days,
                    order_quantity=order_quantity_created,
                )

                purchase_orders.append(
                    new_po
                )

                pending_orders.append(
                    new_po
                )

                inventory_position += (
                    order_quantity_created
                )

                projected_inventory = (
                    inventory_position
                    - ceil_units(
                        lead_time_demand
                    )
                )

                action = (
                    "Create Purchase Order"
                )

        daily_rows.append(
            {
                "Date": current_date.date().isoformat(),
                "Product": product,
                "OpeningStock": opening_stock,
                "ReceivedQuantity": received_quantity,
                "ForecastDemand": round(
                    forecast_demand,
                    2,
                ),
                "DemandUsed": demand_units,
                "FulfilledDemand": fulfilled_demand,
                "ClosingStock": stock,
                "InventoryPosition": inventory_position,
                "ReorderPoint": reorder_point,
                "LeadTimeDays": lead_time_days,
                "LeadTimeDemand": round(
                    lead_time_demand,
                    2,
                ),
                "SafetyStock": safety_stock,
                "ProjectedInventoryAfterLeadTime": projected_inventory,
                "NeedReplenishment": (
                    "YES"
                    if need_replenishment
                    else "NO"
                ),
                "OpenPurchaseOrderAvailable": (
                    "YES"
                    if open_po_available
                    else "NO"
                ),
                "CreatedPO_ID": created_po_id,
                "OrderQuantityCreated": (
                    order_quantity_created
                ),
                "StockoutFlag": (
                    1
                    if units_short > 0
                    else 0
                ),
                "UnitsShort": units_short,
                "DailyHoldingCost": round(
                    stock
                    * holding_cost_per_unit,
                    2,
                ),
                "Action": action,
            }
        )

    inventory_report = pd.DataFrame(
        daily_rows
    )

    purchase_order_report = (
        format_purchase_orders(
            purchase_orders
        )
    )

    kpi_report = calculate_kpis(
        inventory_report=inventory_report,
        purchase_order_report=purchase_order_report,
        product=product,
        opening_stock=int(
            latest["StockOnHand"]
        ),
        reorder_point=reorder_point,
        lead_time_days=lead_time_days,
        review_period_days=review_period_days,
    )

    assumptions = planning_assumptions(
        history_end_date
    )

    inventory_report.to_csv(
        output_dir
        / "Inventory_Planning_Report.csv",
        index=False,
    )

    purchase_order_report.to_csv(
        output_dir
        / "Purchase_Orders_Generated.csv",
        index=False,
    )

    kpi_report.to_csv(
        output_dir
        / "Inventory_KPIs.csv",
        index=False,
    )

    assumptions.to_csv(
        output_dir
        / "Inventory_Planning_Assumptions.csv",
        index=False,
    )

    print("=" * 65)
    print("INVENTORY PLANNING COMPLETED")
    print("=" * 65)
    print(
        f"Inventory history end : {history_end_date.date()}"
    )
    print(
        f"Opening stock         : {int(latest['StockOnHand'])}"
    )
    print(
        f"Reorder point         : {reorder_point}"
    )
    print(
        f"Safety stock          : {latest_safety_stock}"
    )
    print(
        f"Lead time             : {lead_time_days} days"
    )
    print(
        f"Forecast start        : {forecast['Date'].min().date()}"
    )
    print(
        f"Forecast end          : {forecast['Date'].max().date()}"
    )
    print(
        f"Forecast demand used  : {int(inventory_report['DemandUsed'].sum())}"
    )
    print(
        f"Ending stock          : {int(inventory_report['ClosingStock'].iloc[-1])}"
    )
    print(
        f"Service level         : {kpi_report.loc[kpi_report['KPI'].eq('ServiceLevel'), 'Value'].iloc[0]:.2f}%"
    )
    print(
        f"Generated POs         : {len(purchase_order_report[purchase_order_report['Source'].eq('Engine generated')])}"
    )
    print(
        f"Generated PO quantity : {int(purchase_order_report.loc[purchase_order_report['Source'].eq('Engine generated'), 'OrderQuantity'].sum())}"
    )
    print("=" * 65)


def parse_args() -> argparse.Namespace:
    project_root = Path(
        __file__
    ).resolve().parents[1]

    default_inventory = (
        project_root
        / "Data"
        / "Raw"
        / "inventory.csv"
    )

    default_forecast = (
        project_root
        / "outputs"
        / "forecast_90_days_direct.csv"
    )

    default_output = (
        project_root
        / "Inventory & workforce planning csv"
        / "outputs"
    )

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--inventory",
        type=Path,
        default=default_inventory,
    )

    parser.add_argument(
        "--forecast",
        type=Path,
        default=default_forecast,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
    )

    parser.add_argument(
        "--review-period-days",
        type=int,
        default=14,
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    run_inventory_engine(
        inventory_path=args.inventory,
        forecast_path=args.forecast,
        output_dir=args.output,
        review_period_days=args.review_period_days,
    )