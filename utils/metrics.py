import pandas as pd
from utils.loader import *

def executive_metrics():

    accuracy = metrics["ForecastAccuracy"].iloc[0]

    sales30 = forecast30["Forecast"].sum()

    sales90 = forecast90["PredictedUnitsSold"].sum()

    workers = workforce["RequiredWorkers"].max()

    current_staff = workforce["CurrentStaff"].iloc[0]

    inventory = inventory_kpis.set_index("KPI")["Value"]

    workforce_metrics = workforce_kpis.set_index("Metric")["Value"]

    return {

    "accuracy": accuracy,

    "sales30": sales30,

    "sales90": sales90,

    "workers": workers,

    "staff": current_staff,

    "opening_stock": inventory["OpeningStock"],

    "ending_stock": inventory["EndingStock"],

    "service_level": float(inventory["ServiceLevel"]) * 100,

    "purchase_orders": inventory["GeneratedPurchaseOrders"],

    "labour_cost": workforce_metrics["TotalProjectedLaborCost"],

    "utilization": workforce_metrics["AverageWorkerUtilization"],

    "hiring_days": workforce_metrics["HiringDays"]

}