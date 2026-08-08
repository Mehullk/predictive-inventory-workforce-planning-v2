import streamlit as st

from utils.metrics import executive_metrics

from components.cards import (
    section_title,
    kpi_card,
)


def insights_page():

    metrics = executive_metrics()

    # ============================================================
    # PAGE-SPECIFIC STYLING
    # ============================================================

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
           EXECUTIVE INSIGHT CARDS
           ======================================================== */

        .insight-card {
            min-height: 190px;
            height: 190px;
            padding: 24px;
            border-radius: 16px;
            background: #E7F1FF;
            border: 1px solid #D1E3FA;
            box-sizing: border-box;
        }

        .insight-card h3 {
            margin-top: 0;
            margin-bottom: 12px;
            color: #24324A;
            font-size: 20px;
        }

        .insight-card p {
            margin: 0;
            color: #334E6F;
            font-size: 15px;
            line-height: 1.6;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    # ============================================================
    # PAGE HEADER
    # ============================================================

    section_title(
        "Executive Insights",
        "Business intelligence generated from forecasting, inventory, and workforce planning",
    )

    # ============================================================
    # EXECUTIVE KPIs
    # ============================================================

    workforce_gap = int(metrics["workforce_gap"])

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        kpi_card(
            "Forecast Accuracy",
            f"{metrics['accuracy']:.2f}%",
            "Model performance",
            "#22C55E",
            "🎯",
        )

    with c2:

        kpi_card(
            "Service Level",
            f"{metrics['service_level']:.1f}%",
            "Demand fulfilled",
            "#22C55E",
            "⭐",
        )

    with c3:

        kpi_card(
            "90-Day Demand",
            f"{int(metrics['sales90']):,}",
            "Predicted units",
            "#3B82F6",
            "📈",
        )

    with c4:

        if workforce_gap > 0:
            gap_text = f"+{workforce_gap} Required"
            gap_color = "#EF4444"

        elif workforce_gap < 0:
            gap_text = f"{abs(workforce_gap)} Surplus"
            gap_color = "#22C55E"

        else:
            gap_text = "Balanced"
            gap_color = "#22C55E"

        kpi_card(
            "Maximum Workforce Gap",
            f"{workforce_gap}",
            gap_text,
            gap_color,
            "👥",
        )

    # ============================================================
    # KPI KNOWLEDGE BOX
    # ============================================================

    st.markdown("---")

    with st.expander("ℹ️ What do these executive KPIs mean?"):

        st.markdown(
            """
### Forecast Accuracy

Indicates how closely the forecasting model's predictions match
actual demand. Higher accuracy means the forecast is more reliable
for planning decisions.

### Service Level

Measures the percentage of forecasted demand fulfilled without
a stockout during the inventory simulation.

**100% Service Level means all forecasted demand was fulfilled
without an inventory shortage.**

### 90-Day Demand

The total demand predicted by the selected forecasting model
over the 90-day planning horizon.

### Maximum Workforce Gap

The largest workforce shortage identified by the validated
workforce decision engine during the planning horizon.

A positive value indicates that additional workforce capacity
is required at the point of maximum shortage.
"""
        )

    # ============================================================
    # EXECUTIVE SUMMARY
    # ============================================================

    st.markdown("---")

    st.subheader("Executive Summary")

    st.success(
        f"""
### Key Business Highlights

- **Forecast Accuracy:** {metrics['accuracy']:.2f}%
- **Expected Demand (90 Days):** {int(metrics['sales90']):,} units
- **Inventory Service Level:** {metrics['service_level']:.1f}%
- **Purchase Orders Generated:** {int(metrics['purchase_orders'])}
- **Peak Workforce Required:** {int(metrics['workers'])}
- **Current Workforce:** {int(metrics['staff'])}
- **Maximum Workforce Gap:** {workforce_gap}
"""
    )

    # ============================================================
    # HOW TO INTERPRET THE SYSTEM
    # ============================================================

    st.markdown("---")

    st.subheader("How to Interpret the Results")

    i1, i2, i3 = st.columns(3)

    with i1:

        st.markdown(
            """
            <div class="insight-card">

            <h3>1. Demand Outlook</h3>

            <p>
            The forecasting model provides the expected demand
            that drives both inventory and workforce planning.
            Reliable forecasts improve downstream planning decisions.
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    with i2:

        st.markdown(
            """
            <div class="insight-card">

            <h3>2. Inventory Readiness</h3>

            <p>
            Inventory planning uses forecasted demand to determine
            replenishment requirements and maintain service levels
            while avoiding unnecessary stockouts.
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    with i3:

        st.markdown(
            """
            <div class="insight-card">

            <h3>3. Workforce Readiness</h3>

            <p>
            Workforce planning converts demand into staffing
            requirements and selects an appropriate intervention
            such as hiring, overtime, hybrid coverage, or no action.
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    # ============================================================
    # DECISION KNOWLEDGE BOX
    # ============================================================

    with st.expander("📘 How the Decision System Works"):

        st.markdown(
            """
### Step 1 — Forecast

The Prophet forecasting model estimates future demand.

↓

### Step 2 — Inventory Planning

Forecasted demand is used to simulate inventory requirements,
replenishment and service-level performance.

↓

### Step 3 — Workforce Planning

Forecasted demand is converted into daily workforce requirements.

↓

### Step 4 — Decision Engine

The workforce engine evaluates the workforce gap and determines
the appropriate intervention.

Possible outcomes include:

**No Action → Overtime → Hybrid → Hiring**

The system therefore does not automatically recommend hiring
whenever a workforce gap appears. The recommended action depends
on the shortage characteristics and the decision rules.

↓

### Step 5 — Management Decision

The final outputs provide management with the forecast,
inventory position, staffing requirement and recommended actions
needed to support operational planning.
"""
        )

    # ============================================================
    # BUSINESS RECOMMENDATIONS
    # ============================================================

    st.markdown("---")

    st.subheader("Business Recommendations")

    recommendations = []

    # ------------------------------------------------------------
    # Inventory recommendation
    # ------------------------------------------------------------

    if metrics["service_level"] >= 100:

        recommendations.append(
            "✅ **Inventory:** The simulated service level is 100%, "
            "indicating that forecasted demand was fulfilled without "
            "a stockout during the planning horizon."
        )

    elif metrics["service_level"] >= 95:

        recommendations.append(
            "🟢 **Inventory:** Service level is strong, but inventory "
            "performance should continue to be monitored for potential "
            "shortage periods."
        )

    elif metrics["service_level"] >= 90:

        recommendations.append(
            "⚠️ **Inventory:** Service level is acceptable but should "
            "be monitored closely. Replenishment and safety-stock "
            "parameters may require review."
        )

    else:

        recommendations.append(
            "❌ **Inventory:** Service level is below the desired "
            "range. Review safety stock, reorder point and replenishment "
            "policies."
        )

    # ------------------------------------------------------------
    # Workforce recommendation
    # ------------------------------------------------------------

    if workforce_gap > 0:

        recommendations.append(
            f"👷 **Workforce:** A maximum shortage of "
            f"**{workforce_gap} worker(s)** is projected. Review the "
            "Workforce Action Plan to determine whether the engine "
            "recommends hiring, overtime or hybrid coverage."
        )

    elif workforce_gap < 0:

        recommendations.append(
            f"👥 **Workforce:** Available capacity exceeds the maximum "
            f"requirement by **{abs(workforce_gap)} worker(s)** at the "
            "measured peak-capacity level."
        )

    else:

        recommendations.append(
            "✅ **Workforce:** Current workforce capacity matches the "
            "maximum projected requirement."
        )

    # ------------------------------------------------------------
    # Forecast recommendation
    # ------------------------------------------------------------

    if metrics["accuracy"] >= 90:

        recommendations.append(
            "📊 **Forecast:** Forecast performance is strong, making "
            "the current model suitable as the planning input for "
            "inventory and workforce decisions."
        )

    elif metrics["accuracy"] >= 80:

        recommendations.append(
            "📊 **Forecast:** Forecast performance is good. Continue "
            "monitoring forecast deviations as new operational data "
            "becomes available."
        )

    else:

        recommendations.append(
            "⚠️ **Forecast:** Forecast performance should be improved "
            "before relying heavily on the model for long-term planning."
        )

    for recommendation in recommendations:

        st.markdown(
            f"- {recommendation}"
        )

    # ============================================================
    # OVERALL ASSESSMENT
    # ============================================================

    st.markdown("---")

    st.subheader("Overall Assessment")

    score = 0

    if metrics["accuracy"] >= 90:
        score += 1

    if metrics["service_level"] >= 95:
        score += 1

    if workforce_gap <= 0:
        score += 1

    if score == 3:

        st.success(
            "🟢 **Operational Health: Excellent** — "
            "Forecast performance, inventory availability and "
            "workforce capacity are all within the desired range."
        )

    elif score == 2:

        st.info(
            "🟡 **Operational Health: Good** — "
            "Most planning indicators are healthy, but at least "
            "one area requires management attention."
        )

    else:

        st.error(
            "🔴 **Operational Health: Needs Attention** — "
            "One or more major planning indicators require review."
        )

    # ============================================================
    # FINAL NOTE
    # ============================================================

    st.markdown("---")

    st.caption(
        "Executive Insights summarizes outputs from the validated "
        "forecasting, inventory planning and workforce decision engines. "
        "Detailed calculations and day-level decisions are available "
        "on the Forecast, Inventory and Workforce pages."
    )