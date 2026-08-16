import streamlit as st

from utils.loader import (
    workforce,
    workforce_kpis,
)

from utils.metrics import executive_metrics

from components.cards import (
    section_title,
    kpi_card,
)

from components.charts import (
    workforce_chart,
)


def workforce_page():

    metrics = executive_metrics()

   

    st.markdown(
        """
        <style>

        /* ========================================================
           KNOWLEDGE / EXPANDER BOXES
           ======================================================== */

        div[data-testid="stExpander"] details summary {
            background-color: #EEF4FF !important;
            color: #24324A !important;
            border: 1px solid #D8E5F5 !important;
            border-radius: 12px !important;
        }

        div[data-testid="stExpander"] details summary:hover {
            background-color: #E2ECFB !important;
            color: #24324A !important;
        }

        div[data-testid="stExpander"] details[open] summary {
            background-color: #EEF4FF !important;
            color: #24324A !important;
            border-bottom-left-radius: 0 !important;
            border-bottom-right-radius: 0 !important;
        }

        div[data-testid="stExpander"] details summary p {
            color: #24324A !important;
            font-weight: 600 !important;
        }

        div[data-testid="stExpander"] details summary svg {
            color: #24324A !important;
        }

        div[data-testid="stExpander"] details > div {
            background-color: #FFFFFF !important;
            color: #24324A !important;
            border: 1px solid #D8E5F5 !important;
            border-top: none !important;
        }

        div[data-testid="stExpander"] details > div p,
        div[data-testid="stExpander"] details > div li,
        div[data-testid="stExpander"] details > div h1,
        div[data-testid="stExpander"] details > div h2,
        div[data-testid="stExpander"] details > div h3 {
            color: #24324A !important;
        }

        /* ========================================================
           WORKFORCE PROCESS CARDS
           ======================================================== */

        .workforce-process-card {
            min-height: 210px;
            height: 210px;
            padding: 24px;
            border-radius: 16px;
            background: #E7F1FF;
            border: 1px solid #D1E3FA;
            box-sizing: border-box;
        }

        .workforce-process-card h3 {
            margin-top: 0;
            margin-bottom: 14px;
            color: #24324A;
            font-size: 21px;
        }

        .workforce-process-card p {
            margin: 0;
            color: #334E6F;
            font-size: 15px;
            line-height: 1.65;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    

    section_title(
        "Workforce Planning",
        
    )

    
    c1, c2, c3, c4 = st.columns(4)

    with c1:

        kpi_card(
            "Current Staff",
            f"{int(metrics['staff'])}",
            "Available Workforce",
            "#3B82F6",
            
        )

    with c2:

        kpi_card(
            "Peak Workforce",
            f"{int(metrics['workers'])}",
            "Maximum Required",
            "#F59E0B",
            
        )

    with c3:

        gap = int(metrics["workforce_gap"])

        if gap > 0:
            delta = f"+{gap} Required"
            color = "#EF4444"

        elif gap < 0:
            delta = f"{abs(gap)} Surplus"
            color = "#22C55E"

        else:
            delta = "Balanced"
            color = "#22C55E"

        kpi_card(
            "Maximum Workforce Gap",
            f"{gap}",
            delta,
            color,
            
        )

    with c4:

        no_action = int(
            metrics["no_action_decisions"]
        )

        kpi_card(
            "No Action Days",
            f"{no_action}",
            "No intervention required",
            "#22C55E",
            
        )

   

    st.markdown("---")

    with st.expander(" What do these workforce KPIs mean?"):

        st.markdown(
            """
### Current Staff

The number of workers available at the beginning of the
workforce planning simulation.

### Peak Workforce

The maximum number of workers required on any day during
the planning horizon based on forecasted demand.

### Maximum Workforce Gap

The largest projected difference between required workers
and available workers.

- **Positive gap:** additional workers are required.
- **Zero gap:** workforce capacity is sufficient.
- **Negative gap:** available workforce exceeds the requirement.

### No Action Days

The number of planning days where the workforce decision engine
determines that no intervention is required.

These KPIs provide a quick management-level view of workforce
capacity and potential shortages.
"""
        )

   

    st.markdown("---")

    st.subheader(
        "Required Workforce Trend"
    )

    st.caption(
        "Projected workforce requirement compared with available and scheduled staff."
    )

    st.plotly_chart(
        workforce_chart(workforce),
        use_container_width=True,
    )

 

    st.markdown("---")

    st.subheader(" Workforce Action Plan")

    st.caption(
        "Dates where the decision engine recommends an intervention. "
        "The table explains what action is required, why it is recommended, "
        "and when the workforce change takes effect."
    )

    
    action_plan = workforce[
        workforce["RecommendedStrategy"].isin(
            ["Hiring", "Overtime", "Hybrid"]
        )
    ].copy()

    if action_plan.empty:

        st.success(
            "No workforce intervention is currently required "
            "during the planning horizon."
        )

    else:

       

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

        action_table = action_plan[display_columns].copy()

                

        def compact_reason(row):

            strategy = row.get("RecommendedStrategy", "")
            gap = int(row.get("WorkforceGap", 0) or 0)

            if strategy == "Overtime":
                return (
                    f"Current shortage: {gap} worker"
                    f"{'s' if abs(gap) != 1 else ''} → "
                    "same-day overtime"
                )

            if strategy == "Hiring":

                workers = int(
                    row.get("WorkersToHire", 0) or 0
                )

                first_gap = row.get(
                    "FirstGapDate",
                    "-"
                )

                if str(first_gap) in ["nan", "NaT", "None"]:
                    first_gap = "-"

                return (
                    f"Future shortage from {str(first_gap)[:10]} "
                    f"→ hire {workers} now"
                )

            if strategy == "Hybrid":

                workers = int(
                    row.get("WorkersToHire", 0) or 0
                )

                return (
                    f"Shortage requires {workers} hire"
                    f"{'s' if workers != 1 else ''} "
                    "plus temporary overtime"
                )

            return "No intervention required"


        action_table["DecisionReason"] = action_table.apply(
            compact_reason,
            axis=1,
        )

        # Friendly management-facing names.
        action_table = action_table.rename(
            columns={
                "Date": "Decision Date",
                "RequiredWorkers": "Required Staff",
                "CurrentStaff": "Available Staff",
                "WorkforceGap": "Gap",
                "RecommendedStrategy": "Recommended Action",
                "DecisionReason": "Why This Action?",
                "WorkersToHire": "Workers to Hire",
                "FirstGapDate": "First Shortage",
                "RecommendedHireDate": "Recommended Hire Date",
                "ImplementationTime": "Implementation",
                "DecisionCost": "Decision Cost",
            }
        )

    

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

     

        for column in [
            "First Shortage",
            "Recommended Hire Date",
        ]:

            if column in action_table.columns:

                action_table[column] = (
                    action_table[column]
                    .replace(
                        {
                            "nan": "-",
                            "NaT": "-",
                            "None": "-",
                        }
                    )
                    .astype(str)
                    .str[:10]
                )

     

        if "Decision Cost" in action_table.columns:

            action_table["Decision Cost"] = (
                action_table["Decision Cost"]
                .apply(
                    lambda x:
                    f"₹{float(x):,.0f}"
                    if x is not None
                    and str(x) not in ["nan", "None"]
                    else "₹0"
                )
            )

       

        st.dataframe(
            action_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Decision Date": st.column_config.TextColumn(
                    "Decision Date",
                    width="small",
                ),

                "Required Staff": st.column_config.NumberColumn(
                    "Required Staff",
                    width="small",
                ),

                "Available Staff": st.column_config.NumberColumn(
                    "Available Staff",
                    width="small",
                ),

                "Gap": st.column_config.NumberColumn(
                    "Gap",
                    width="small",
                ),

                "Recommended Action": st.column_config.TextColumn(
                    "Recommended Action",
                    width="medium",
                ),

                "Why This Action?": st.column_config.TextColumn(
                    "Why This Action?",
                    width="large",
                ),

                "Workers to Hire": st.column_config.NumberColumn(
                    "Workers to Hire",
                    width="small",
                ),

                "First Shortage": st.column_config.TextColumn(
                    "First Shortage",
                    width="small",
                ),

                "Recommended Hire Date": st.column_config.TextColumn(
                    "Recommended Hire Date",
                    width="medium",
                ),

                "Implementation": st.column_config.TextColumn(
                    "Implementation",
                    width="medium",
                ),

                "Decision Cost": st.column_config.TextColumn(
                    "Decision Cost",
                    width="small",
                ),
            },
        )

        
        st.info(
            """
    ### How to read this table

    - **Required Staff:** Number of workers needed based on forecasted demand.
    - **Available Staff:** Workforce available at the decision point.
    - **Gap:** Required Staff − Available Staff. A positive value means there is a current shortage.
    - **Recommended Action:** The strategy selected by the workforce decision engine.
    - **Why This Action?:** The actual decision-engine explanation for why the strategy was selected.
    - **Workers to Hire:** Number of permanent workers included in the hiring decision.
    - **First Shortage:** First future date where the workforce becomes insufficient.
    - **Recommended Hire Date:** Date on which hiring should be initiated so workers are available before the projected shortage.
    - **Implementation:** Whether the action is required immediately or should be initiated in advance.
    - **Decision Cost:** Estimated cost associated with the recommended intervention.

    **Important:** A hiring decision can occur even when the current Gap is 0.  
    This means the system is acting **in advance** because a future shortage has been forecast and hiring requires lead time.
    """
        )


    with st.expander("📘 Workforce Planning Concepts"):

        st.markdown(
            """
### Workforce Gap

The difference between the number of workers required and
the workers currently available.

**Gap = Required Workers − Available Workers**

A positive gap indicates a workforce shortage.

### Hiring

Hiring is recommended when a workforce shortage persists
across consecutive planning days according to the decision
rules.

The hiring decision also considers the hiring lead time so
that workers are scheduled before the expected shortage.

### Overtime

Overtime provides temporary same-day coverage for smaller
workforce gaps without permanently increasing staff.

The planning engine limits overtime hours per worker per day.

### Hybrid Strategy

Hybrid provides temporary coverage for severe isolated
workforce shortages where permanent hiring is not justified
by the persistence of the shortage.

### Pending Workers

Workers who have been approved for hiring but have not yet
joined the workforce.

They are tracked according to their scheduled joining date.

### No Action

No workforce intervention is required when available staff
are sufficient for the projected requirement.

### Decision Flow

**Demand Forecast → Required Workforce → Workforce Gap → Decision Strategy**

The decision engine then selects the appropriate response:

**No Action → Overtime → Hybrid → Hiring**

depending on the shortage characteristics and planning rules.
"""
        )

    

    st.markdown("---")

    st.subheader(
        "Workforce Strategy Summary"
    )

    s1, s2, s3, s4 = st.columns(4)

    with s1:

        kpi_card(
            "Hiring Decisions",
            f"{int(metrics['hiring_decisions'])}",
            "Hiring recommended",
            "#EF4444",
            
        )

    with s2:

        kpi_card(
            "Overtime Decisions",
            f"{int(metrics['overtime_decisions'])}",
            "Temporary coverage",
            "#F59E0B",
            
        )

    with s3:

        kpi_card(
            "Hybrid Decisions",
            f"{int(metrics['hybrid_decisions'])}",
            "Hiring + overtime",
            "#8B5CF6",
            
        )

    with s4:

        kpi_card(
            "Pending Workers",
            f"{int(metrics['pending_workers'])}",
            "Maximum scheduled",
            "#3B82F6",
            
        )

  

    st.markdown("---")

    st.subheader(
        "Workforce Decision Cost Summary"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        kpi_card(
            "Average Hiring Cost",
            f"₹{metrics['average_hiring_cost']:,.0f}",
            "Per decision",
            "#EF4444",
            
        )

    with c2:

        kpi_card(
            "Average Overtime Cost",
            f"₹{metrics['average_overtime_cost']:,.0f}",
            "Per decision",
            "#F59E0B",
            
        )

    with c3:

        kpi_card(
            "Average Hybrid Cost",
            f"₹{metrics['average_hybrid_cost']:,.0f}",
            "Per decision",
            "#8B5CF6",
            
        )

    

    st.markdown("---")

    st.subheader(
        "Latest-Day Workforce Recommendation"
    )

    latest = workforce.iloc[-1]

    strategy = latest["RecommendedStrategy"]

    reason = latest["DecisionReason"]

    implementation = latest["ImplementationTime"]

    workers_to_hire = latest.get(
        "WorkersToHire",
        0
    )

    if strategy == "Hiring":

        st.error(
            f"""
### 🔴 Hiring Recommended

**Workers to Hire:** {int(workers_to_hire)}

**Implementation:** {implementation}

**Reason:** {reason}
"""
        )

    elif strategy == "Overtime":

        st.warning(
            f"""
### 🟠 Overtime Recommended

**Implementation:** {implementation}

**Reason:** {reason}
"""
        )

    elif strategy == "Hybrid":

        st.warning(
            f"""
### 🟣 Hybrid Strategy Recommended

**Implementation:** {implementation}

**Reason:** {reason}
"""
        )

    else:

        st.success(
            f"""
### 🟢 No Action Required

**Implementation:** {implementation}

**Reason:** {reason}

For the latest forecasted date, the available workforce is sufficient.
"""
        )



    st.markdown("---")

    st.subheader(
        " Detailed Workforce Analysis"
    )

    st.caption(
    "Complete day-by-day workforce requirements and decision-engine "
    "outputs used to generate the Workforce Action Plan above."
    )

    st.dataframe(
        workforce,
        use_container_width=True,
        hide_index=True,
    )