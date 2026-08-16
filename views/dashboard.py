import streamlit as st

from utils.loader import (
    forecast90,
    inventory_report,
    inventory_kpis,
    workforce,
    workforce_kpis,
)

from utils.metrics import executive_metrics

from components.cards import (
    section_title,
    kpi_card,
)

from components.charts import (
    forecast_chart,
    inventory_chart,
    workforce_chart,
)


def _metric_value(df, key_column, key, default=0):
    """Safely read a metric from a KPI dataframe."""
    if df is None or df.empty or key_column not in df.columns:
        return default

    matches = df.loc[df[key_column].astype(str) == str(key), "Value"]
    if matches.empty:
        return default

    return matches.iloc[0]


def _first_existing_column(df, columns, default=0):
    """Return the first available column's value for the latest row."""
    if df is None or df.empty:
        return default

    for column in columns:
        if column in df.columns:
            value = df[column].iloc[-1]
            if value is not None:
                return value

    return default


def _total_decision_cost():
    """Read the total workforce decision cost from the KPI report."""
    value = _metric_value(
        workforce_kpis,
        "Metric",
        "Total Decision Cost",
        default=None,
    )

    if value is not None:
        return float(value)

    # Compatibility fallback for older KPI files.
    hiring = _metric_value(
        workforce_kpis,
        "Metric",
        "Total Hiring Decision Cost",
        0,
    )
    overtime = _metric_value(
        workforce_kpis,
        "Metric",
        "Total Overtime Decision Cost",
        0,
    )
    hybrid = _metric_value(
        workforce_kpis,
        "Metric",
        "Total Hybrid Decision Cost",
        0,
    )

    return float(hiring) + float(overtime) + float(hybrid)


def _workers_to_hire_total():
    """Support both current and older workforce decision report schemas."""
    if workforce is None or workforce.empty:
        return 0

    for column in ("WorkersToHire", "HiringRequired"):
        if column in workforce.columns:
            return int(workforce[column].fillna(0).sum())

    return 0


def _decision_counts():
    """Return the workforce strategy counts used on the dashboard."""
    if workforce is None or workforce.empty:
        return 0, 0, 0, 0

    strategy = workforce["RecommendedStrategy"].astype(str)

    return (
        int((strategy == "Hiring").sum()),
        int((strategy == "Overtime").sum()),
        int((strategy == "Hybrid").sum()),
        int((strategy == "No Action").sum()),
    )


def _render_workforce_decision_summary(metrics):
    """Compact but decision-focused workforce summary for the dashboard."""

    hiring_days, overtime_days, hybrid_days, no_action_days = _decision_counts()

    total_cost = _total_decision_cost()
    workers_to_hire = _workers_to_hire_total()

    st.subheader("Workforce Planning")

    st.caption(
        "Projected workforce requirement and recommended staffing actions "
        "across the 90-day planning horizon."
    )

    # ============================================================
    # WORKFORCE KPI CARDS
    # ============================================================

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        kpi_card(
            "Current Staff",
            f"{int(metrics['staff'])}",
            "Starting workforce",
            "#B8DBFC",
            
        )

    with k2:
        kpi_card(
            "Peak Required",
            f"{int(metrics['workers'])}",
            "Maximum workers needed",
            "#FFF7C7",
            
        )

    with k3:

        gap = int(metrics["workforce_gap"])

        gap_label = (
            f"+{gap} shortage"
            if gap > 0
            else "No shortage"
        )

        kpi_card(
            "Maximum Gap",
            f"{gap}",
            gap_label,
            "#FFE3E3" if gap > 0 else "#D9F5E7",
            
        )

    with k4:
        kpi_card(
            "Decision Cost",
            f"₹{total_cost:,.0f}",
            "Workforce strategy cost",
            "#E9D5FF",
            
        )

    # ============================================================
    # WORKFORCE TREND
    # ============================================================

    st.markdown("---")

    st.subheader("Required Workforce Trend")

    st.caption(
        "Required Workers shows forecast-based staffing demand. "
        "Current Staff shows available employees, while Scheduled Staff "
        "also includes approved workers who are pending their joining date."
    )

    st.plotly_chart(
        workforce_chart(workforce),
        use_container_width=True,
    )

    # ============================================================
    # WORKFORCE DECISIONS
    # ============================================================

    st.markdown("#### Workforce Decisions")

    d1, d2, d3, d4 = st.columns(4)

    with d1:
        st.metric(
            "Hiring",
            hiring_days,
        )

    with d2:
        st.metric(
            "Overtime",
            overtime_days,
        )

    with d3:
        st.metric(
            "Hybrid",
            hybrid_days,
        )

    with d4:
        st.metric(
            "Workers to Hire",
            workers_to_hire,
        )

    # ============================================================
    # MANAGEMENT ACTION MESSAGE
    # ============================================================

    if hiring_days or overtime_days or hybrid_days:

        st.warning(
            f"""
**Management action required:** {hiring_days} hiring day(s),
{overtime_days} overtime day(s), and {hybrid_days} hybrid day(s)
have been identified across the planning horizon.
"""
        )

    else:

        st.success(
            "No workforce intervention is currently required "
            "across the planning horizon."
        )

        # ============================================================
    # WORKFORCE ACTION PLAN
    # ============================================================

    if workforce is not None and not workforce.empty:

        action_plan = workforce[
            workforce["RecommendedStrategy"].isin(
                ["Hiring", "Overtime", "Hybrid"]
            )
        ].copy()

        if not action_plan.empty:

            # ========================================================
            # PREPARE MANAGEMENT-FACING TABLE
            # ========================================================

            action_plan["Date"] = (
                action_plan["Date"]
                .astype(str)
                .str[:10]
            )

            if "FirstGapDate" in action_plan.columns:
                action_plan["FirstGapDate"] = (
                    action_plan["FirstGapDate"]
                    .fillna("-")
                    .astype(str)
                    .str[:10]
                )

            if "RecommendedHireDate" in action_plan.columns:
                action_plan["RecommendedHireDate"] = (
                    action_plan["RecommendedHireDate"]
                    .fillna("-")
                    .astype(str)
                    .str[:10]
                )

            # ========================================================
            # FINAL MANAGEMENT TABLE
            # ========================================================

            display_columns = [
                "Date",
                "RequiredWorkers",
                "CurrentStaff",
                "WorkforceGap",
                "RecommendedStrategy",
                "DecisionReason",
                "WorkersToHire",
                "FirstGapDate",
                "RecommendedHireDate",
                "ImplementationTime",
                "DecisionCost",
            ]

            display_columns = [
                column
                for column in display_columns
                if column in action_plan.columns
            ]

            action_table = action_plan[
                display_columns
            ].copy()

            # ========================================================
            # COMPACT MANAGEMENT-FACING REASON
            # ========================================================

            def compact_reason(row):

                strategy = row.get(
                    "RecommendedStrategy",
                    ""
                )

                gap = int(
                    row.get(
                        "WorkforceGap",
                        0
                    ) or 0
                )

                if strategy == "Overtime":

                    return (
                        f"Current shortage: {gap} worker"
                        f"{'s' if abs(gap) != 1 else ''} → "
                        "same-day overtime"
                    )

                if strategy == "Hiring":

                    workers = int(
                        row.get(
                            "WorkersToHire",
                            0
                        ) or 0
                    )

                    first_gap = row.get(
                        "FirstGapDate",
                        "-"
                    )

                    if str(first_gap) in [
                        "nan",
                        "NaT",
                        "None",
                    ]:
                        first_gap = "-"

                    return (
                        f"Future shortage from "
                        f"{str(first_gap)[:10]} "
                        f"→ hire {workers} now"
                    )

                if strategy == "Hybrid":

                    workers = int(
                        row.get(
                            "WorkersToHire",
                            0
                        ) or 0
                    )

                    return (
                        f"Shortage requires "
                        f"{workers} hire"
                        f"{'s' if workers != 1 else ''} "
                        "plus temporary overtime"
                    )

                return "No intervention required"

            action_table["DecisionReason"] = (
                action_table.apply(
                    compact_reason,
                    axis=1,
                )
            )

            # ========================================================
            # FRIENDLY COLUMN NAMES
            # ========================================================

            action_table = action_table.rename(
                columns={
                    "Date": "Decision Date",
                    "RequiredWorkers": "Required Staff",
                    "CurrentStaff": "Available Staff",
                    "WorkforceGap": "Gap",
                    "RecommendedStrategy": "Recommended Action",
                    "DecisionReason": "Why?",
                    "WorkersToHire": "Workers to Hire",
                    "FirstGapDate": "First Shortage",
                    "RecommendedHireDate": "Recommended Hire Date",
                    "ImplementationTime": "Implementation",
                    "DecisionCost": "Decision Cost",
                }
            )

            # ========================================================
            # FORMAT NUMERIC COLUMNS
            # ========================================================

            for column in [
                "Required Staff",
                "Available Staff",
                "Gap",
                "Workers to Hire",
            ]:

                if column in action_table.columns:

                    action_table[column] = (
                        action_table[column]
                        .fillna(0)
                        .astype(int)
                    )

            # ========================================================
            # FORMAT DATES
            # ========================================================

            for column in [
                "First Shortage",
                "Recommended Hire Date",
            ]:

                if column in action_table.columns:

                    action_table[column] = (
                        action_table[column]
                        .replace(
                            {
                                "nan": "—",
                                "NaT": "—",
                                "None": "—",
                            }
                        )
                        .astype(str)
                        .str[:10]
                    )

            # ========================================================
            # FORMAT DECISION COST
            # ========================================================

            if "Decision Cost" in action_table.columns:

                action_table["Decision Cost"] = (
                    action_table["Decision Cost"]
                    .apply(
                        lambda x:
                        f"₹{float(x):,.0f}"
                        if x is not None
                        and str(x) not in [
                            "nan",
                            "None",
                        ]
                        else "₹0"
                    )
                )

            # ========================================================
            # DISPLAY
            # ========================================================

            st.markdown("####  Workforce Action Plan")

            st.caption(
                "Only dates requiring a workforce intervention are shown. "
                "The same decision table is used on the Workforce Planning page."
            )

            st.dataframe(
                action_table,
                use_container_width=True,
                hide_index=True,
                column_config={

                    "Decision Date":
                        st.column_config.TextColumn(
                            "Decision Date",
                            width="small",
                        ),

                    "Required Staff":
                        st.column_config.NumberColumn(
                            "Required Staff",
                            width="small",
                        ),

                    "Available Staff":
                        st.column_config.NumberColumn(
                            "Available Staff",
                            width="small",
                        ),

                    "Gap":
                        st.column_config.NumberColumn(
                            "Gap",
                            width="small",
                        ),

                    "Recommended Action":
                        st.column_config.TextColumn(
                            "Recommended Action",
                            width="medium",
                        ),

                    "Why?":
                        st.column_config.TextColumn(
                            "Why?",
                            width="medium",
                        ),

                    "Workers to Hire":
                        st.column_config.NumberColumn(
                            "Workers to Hire",
                            width="small",
                        ),

                    "First Shortage":
                        st.column_config.TextColumn(
                            "First Shortage",
                            width="small",
                        ),

                    "Recommended Hire Date":
                        st.column_config.TextColumn(
                            "Recommended Hire Date",
                            width="medium",
                        ),

                    "Implementation":
                        st.column_config.TextColumn(
                            "Implementation",
                            width="medium",
                        ),

                    "Decision Cost":
                        st.column_config.TextColumn(
                            "Decision Cost",
                            width="small",
                        ),
                },
            )

            # ========================================================
            # HOW TO READ THE TABLE
            # ========================================================

            st.info(
                """
### How to read this table

- **Required Staff:** Workers needed based on forecasted demand.
- **Available Staff:** Workers available at the decision point.
- **Gap:** Required Staff − Available Staff.
- **Recommended Action:** Workforce strategy selected by the decision engine.
- **Why?:** Short management explanation of why the action is recommended.
- **Workers to Hire:** Permanent workers included in the hiring decision.
- **First Shortage:** First future date where workforce capacity becomes insufficient.
- **Recommended Hire Date:** When hiring should be initiated.
- **Implementation:** Whether the action is immediate or should be initiated in advance.
- **Decision Cost:** Estimated cost of the recommended intervention.

**Important:** A hiring decision can occur when the current Gap is 0.  
This means the system is acting in advance because a future shortage has been forecast and hiring requires lead time.
"""
            )


def dashboard_page():
    metrics = executive_metrics()

    section_title(
        "Enterprise Decision Support",
        "90-day demand, inventory and workforce planning recommendations",
    )

    # ============================================================
    # 1. KPI CARDS — ALL THREE MODULES
    # ============================================================
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card(
            "90-Day Demand",
            f"{int(metrics['sales90']):,}",
            "Forecasted units",
            "#B8DBFC",
            
        )

    with c2:
        kpi_card(
            "Inventory Service Level",
            f"{metrics['service_level']:.1f}%",
            "Inventory status",
            "#D9F5E7",
            
        )

    with c3:
        kpi_card(
            "Workforce Gap",
            f"{int(metrics['workforce_gap'])}",
            "Maximum projected shortage",
            "#FFF7C7",
            
        )

    with c4:
        kpi_card(
            "Decision Cost",
            f"₹{_total_decision_cost():,.0f}",
            "Workforce decision output",
            "#E9D5FF",
            
        )

    st.markdown(
        """
        <div style="
            margin-top: 6px;
            margin-bottom: 20px;
            padding: 12px 16px;
            border-radius: 12px;
            background: rgba(236, 244, 255, 0.75);
            color: #5C6E88;
            font-size: 14px;
        ">
            <b>Decision flow:</b>
            Demand forecast → Inventory planning → Workforce planning
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ============================================================
    # 2. SALES FORECAST — FIRST ANALYTICAL SECTION
    # ============================================================
    st.subheader("Sales Forecast")
    st.caption(
        "Expected demand over the next 90 days from the selected forecasting model."
    )

    f1, f2, f3 = st.columns(3)

    with f1:
        kpi_card(
            "Forecast Accuracy",
            f"{metrics['accuracy']:.2f}%",
            "Model performance",
            "#D9F5E7",
            
        )

    with f2:
        kpi_card(
            "30-Day Demand",
            f"{int(metrics['sales30']):,}",
            "Near-term forecast",
            "#B8DBFC",
            
        )

    with f3:
        kpi_card(
            "90-Day Demand",
            f"{int(metrics['sales90']):,}",
            "Planning horizon",
            "#E9D5FF",
            
        )

    st.plotly_chart(
        forecast_chart(forecast90),
        use_container_width=True,
    )

    # ============================================================
    # 3. INVENTORY PLANNING
    # ============================================================
    st.divider()

    st.subheader("Inventory Planning")
    st.caption(
        "Inventory position and replenishment status driven by forecasted demand."
    )

    i1, i2, i3, i4 = st.columns(4)

    with i1:
        kpi_card(
            "Opening Stock",
            f"{int(metrics['opening_stock']):,}",
            "Planning-period opening",
            "#B8DBFC",
            
        )

    with i2:
        kpi_card(
            "Ending Stock",
            f"{int(metrics['ending_stock']):,}",
            "Projected ending position",
            "#D9F5E7",
            
        )

    with i3:
        kpi_card(
            "Service Level",
            f"{metrics['service_level']:.1f}%",
            "Target inventory service",
            "#D9F5E7",
            
        )

    with i4:
        kpi_card(
            "Purchase Orders",
            f"{int(metrics['purchase_orders'])}",
            "Generated orders",
            "#FFF7C7",
            
        )

    st.plotly_chart(
        inventory_chart(inventory_report),
        use_container_width=True,
    )

    # One compact inventory decision panel.
    if inventory_report is not None and not inventory_report.empty:
        latest_inventory = inventory_report.iloc[-1]

        

        

    # ============================================================
    # 4. WORKFORCE PLANNING — PRIMARY DECISION SECTION
    # ============================================================
    st.divider()

    # Visually give workforce more room than the other branches.
    _render_workforce_decision_summary(metrics)

    st.divider()

    st.caption(
        "The dashboard summarizes decision outputs. Detailed forecast, inventory, "
        "and workforce analysis remains available on their respective pages."
    )