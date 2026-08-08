import streamlit as st

from utils.loader import (
    forecast30,
    forecast90,
)

from utils.metrics import executive_metrics

from components.cards import (
    section_title,
    kpi_card,
)

from components.charts import (
    forecast_chart,
)


def forecast_page():

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

        div[data-testid="stExpander"] {
            margin: 18px 0 28px 0 !important;
            border: none !important;
            padding: 0 !important;
            border-radius: 16px !important;
            overflow: hidden !important;
            box-shadow: 0 4px 16px rgba(36, 50, 74, 0.08) !important;
        }


        /* ========================================================
        EXPANDER HEADER
        ======================================================== */

        div[data-testid="stExpander"] details summary {
            background: #EEF5FF !important;
            border: 1px solid #D5E4F7 !important;
            border-radius: 16px !important;
            padding: 17px 20px !important;
            min-height: 54px !important;
            box-sizing: border-box !important;
        }

        div[data-testid="stExpander"] details summary,
        div[data-testid="stExpander"] details summary *,
        div[data-testid="stExpander"] details summary p,
        div[data-testid="stExpander"] details summary span {
            color: #24324A !important;
        }

        div[data-testid="stExpander"] details summary p {
            margin: 0 !important;
            font-size: 16px !important;
            font-weight: 650 !important;
        }

        div[data-testid="stExpander"] details summary:hover {
            background: #E5F0FF !important;
            border-color: #C7DCF5 !important;
        }


        /* ========================================================
        ACTUAL EXPANDED CONTENT
        ======================================================== */

        /* Streamlit's actual content group */
        div[data-testid="stExpander"] details > div[role="group"] {
            background: #F8FBFF !important;

            border-left: 1px solid #D5E4F7 !important;
            border-right: 1px solid #D5E4F7 !important;
            border-bottom: 1px solid #D5E4F7 !important;

            border-bottom-left-radius: 16px !important;
            border-bottom-right-radius: 16px !important;

            padding: 26px 32px !important;

            box-sizing: border-box !important;
        }


        /* Markdown container INSIDE the expander */
        div[data-testid="stExpander"]
        div[data-testid="stMarkdownContainer"] {
            background: transparent !important;
            color: #425B79 !important;
        }


        /* ALL text inside markdown */
        div[data-testid="stExpander"]
        div[data-testid="stMarkdownContainer"] * {
            color: #425B79 !important;
        }


        /* Knowledge headings */
        div[data-testid="stExpander"]
        div[data-testid="stMarkdownContainer"] h1,
        div[data-testid="stExpander"]
        div[data-testid="stMarkdownContainer"] h2,
        div[data-testid="stExpander"]
        div[data-testid="stMarkdownContainer"] h3 {
            color: #24324A !important;

            font-weight: 700 !important;

            margin-top: 12px !important;
            margin-bottom: 8px !important;
        }


        /* First heading */
        div[data-testid="stExpander"]
        div[data-testid="stMarkdownContainer"] h3:first-child {
            margin-top: 0 !important;
        }


        /* Paragraphs */
        div[data-testid="stExpander"]
        div[data-testid="stMarkdownContainer"] p {
            color: #425B79 !important;

            font-size: 15px !important;
            line-height: 1.6 !important;

            margin-top: 6px !important;
            margin-bottom: 14px !important;
        }


        /* Bold text */
        div[data-testid="stExpander"]
        div[data-testid="stMarkdownContainer"] strong {
            color: #24324A !important;
            font-weight: 700 !important;
        }


        /* Lists */
        div[data-testid="stExpander"]
        div[data-testid="stMarkdownContainer"] ul,
        div[data-testid="stExpander"]
        div[data-testid="stMarkdownContainer"] ol {
            margin-top: 8px !important;
            margin-bottom: 12px !important;
            padding-left: 24px !important;
        }

        div[data-testid="stExpander"]
        div[data-testid="stMarkdownContainer"] li {
            color: #425B79 !important;
            line-height: 1.55 !important;
            margin-bottom: 6px !important;
        }





        
        /* ========================================================
           FORECAST PROCESS CARDS
           ======================================================== */

        .forecast-process-card {
            min-height: 210px;
            height: 210px;
            padding: 24px;
            border-radius: 16px;
            background: #E7F1FF;
            border: 1px solid #D1E3FA;
            box-sizing: border-box;
        }

        .forecast-process-card h3 {
            margin-top: 0;
            margin-bottom: 14px;
            color: #24324A;
            font-size: 21px;
        }

        .forecast-process-card p {
            margin: 0;
            color: #334E6F;
            font-size: 15px;
            line-height: 1.65;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    # ============================================================
    # PAGE HEADER
    # ============================================================

    section_title(
        "Sales Forecast",
        "Prophet model predictions with confidence intervals",
    )

    # ============================================================
    # KPI SUMMARY
    # ============================================================

    c1, c2, c3 = st.columns(3)

    with c1:
        kpi_card(
            "Forecast Accuracy",
            f"{metrics['accuracy']:.2f}%",
            "Model Performance",
            "#22C55E",
            "🎯",
        )

    with c2:
        kpi_card(
            "30-Day Forecast",
            f"{int(metrics['sales30']):,}",
            "Predicted Units",
            "#3B82F6",
            "📅",
        )

    with c3:
        kpi_card(
            "90-Day Forecast",
            f"{int(metrics['sales90']):,}",
            "Predicted Units",
            "#F59E0B",
            "📈",
        )

    # ============================================================
    # KPI KNOWLEDGE BOX
    # ============================================================

    st.markdown("---")

    with st.expander(
        "ℹ️ What do these forecast KPIs mean?"
    ):

        st.markdown(
            """
### Forecast Accuracy

Forecast Accuracy indicates how closely the forecasting model's
predictions match actual observed demand.

The project uses the model's validation accuracy as the primary
measure of forecast reliability.

### 30-Day Forecast

The total number of units predicted to be demanded over the
next 30 days.

### 90-Day Forecast

The total number of units predicted to be demanded over the
next 90 days.

The 90-day forecast is used as the longer planning horizon for
inventory and workforce decisions.
"""
        )

    # ============================================================
    # SALES FORECAST
    # ============================================================

    st.markdown("---")

    st.subheader("Sales Forecast")

    # ============================================================
    # 90-DAY FORECAST — DEFAULT
    # ============================================================

    tab1, tab2 = st.tabs([
        "90-Day Forecast",
        "30-Day Forecast",
    ])

    with tab1:

        st.caption(
            "Expected demand over the next 90 days."
        )

        st.plotly_chart(
            forecast_chart(forecast90),
            use_container_width=True,
        )

        st.markdown(
            "#### 90-Day Forecast Data"
        )

        st.dataframe(
            forecast90,
            use_container_width=True,
            hide_index=True,
        )

    # ============================================================
    # 30-DAY FORECAST
    # ============================================================

    with tab2:

        st.caption(
            "Expected demand over the next 30 days."
        )

        fig30 = forecast_chart(
            forecast30
        )

        fig30.update_layout(
            title=dict(
                text="30-Day Sales Forecast",
                font=dict(
                    size=22,
                    color="#24324A",
                ),
                x=0,
                xanchor="left",
            )
        )

        st.plotly_chart(
            fig30,
            use_container_width=True,
        )

        st.markdown(
            "#### 30-Day Forecast Data"
        )

        st.dataframe(
            forecast30,
            use_container_width=True,
            hide_index=True,
        )

    # ============================================================
    # FORECAST CONCEPTS
    # ============================================================

    st.markdown("---")

    with st.expander(
        "📘 Forecasting Concepts"
    ):

        st.markdown(
            """
### Prophet Forecasting Model

The project uses Facebook Prophet to estimate future demand
from historical time-series patterns.

### Forecast

The central forecast represents the model's expected demand
for each future date.

### 95% Confidence Interval

The shaded region around the forecast represents the model's
95% confidence interval.

It provides a range showing uncertainty around the predicted
demand rather than treating the forecast as an exact value.

### Why Forecasting Matters

Forecasting is the first stage of the planning system.

**Forecasted Demand → Inventory Planning → Workforce Planning**

The demand forecast therefore becomes the common planning input
for downstream operational decisions.
"""
        )

    # ============================================================
    # FORECAST PROCESS
    # ============================================================

    st.markdown("---")

    st.subheader(
        "How the Forecast Supports Planning"
    )

    st.caption(
        "The forecast acts as the common demand signal for the "
        "inventory and workforce planning modules."
    )

    p1, p2, p3 = st.columns(3)

    with p1:

        st.markdown(
            """
            <div class="forecast-process-card">

            <h3>1. Predict Demand</h3>

            <p>
            The Prophet model estimates future daily demand
            using learned patterns from historical data.
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    with p2:

        st.markdown(
            """
            <div class="forecast-process-card">

            <h3>2. Plan Inventory</h3>

            <p>
            Forecasted demand is used to estimate inventory
            requirements, replenishment needs and service-level
            performance.
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    with p3:

        st.markdown(
            """
            <div class="forecast-process-card">

            <h3>3. Plan Workforce</h3>

            <p>
            Forecasted demand is converted into workforce
            requirements and used by the decision engine to
            recommend staffing actions.
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    # ============================================================
    # FINAL FORECAST INTERPRETATION
    # ============================================================

    st.markdown("---")

    if metrics["accuracy"] >= 90:

        st.success(
            f"""
### Forecasting Result

The selected forecasting model achieved **{metrics['accuracy']:.2f}%**
forecast accuracy.

This indicates strong predictive performance and supports using the
forecast as the demand input for the inventory and workforce planning
modules.

- **30-Day Expected Demand:** {int(metrics['sales30']):,} units
- **90-Day Expected Demand:** {int(metrics['sales90']):,} units
"""
        )

    elif metrics["accuracy"] >= 80:

        st.info(
            f"""
### Forecasting Result

The selected forecasting model achieved **{metrics['accuracy']:.2f}%**
forecast accuracy.

The model provides a useful planning signal, while forecast deviations
should continue to be monitored as new actual demand becomes available.
"""
        )

    else:

        st.warning(
            f"""
### Forecasting Result

The selected forecasting model achieved **{metrics['accuracy']:.2f}%**
forecast accuracy.

Forecast performance should be reviewed before relying heavily on the
model for long-term operational decisions.
"""
        )