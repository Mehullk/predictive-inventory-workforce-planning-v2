import streamlit as st

from utils.loader import (
    forecast90,
    inventory_report,
    workforce,
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


def dashboard_page():

    metrics = executive_metrics()

    section_title(
        "Enterprise Dashboard",
        "AI-powered inventory and workforce planning overview",
    )

    # =========================
    # KPI ROW
    # =========================

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card(
            "Forecast Accuracy",
            f"{metrics['accuracy']:.2f}%",
            "Prophet Model",
            "#D9F5E7",
            "🎯",
        )

    with c2:
        kpi_card(
            "90-Day Forecast",
            f"{int(metrics['sales90']):,}",
            "Predicted Units",
            "#B8DBFC",
            "📈",
        )

    with c3:
        kpi_card(
            "Service Level",
            f"{metrics['service_level']:.1f}%",
            "Inventory KPI",
            "#D9F5E7",
            "📦",
        )

    with c4:
        kpi_card(
            "Peak Workforce",
            f"{int(metrics['workers'])}",
            "Workers",
            "#FFF7C7",
            "👷",
        )

    st.divider()

    # =========================
    # FORECAST
    # =========================

    st.subheader("Sales Forecast")

    st.plotly_chart(
        forecast_chart(forecast90),
        use_container_width=True,
    )

    st.divider()

    # =========================
    # TWO CHARTS
    # =========================

    left, right = st.columns(2)

    with left:

        st.subheader("Inventory")

        st.plotly_chart(
            inventory_chart(inventory_report),
            use_container_width=True,
        )

    with right:

        st.subheader("Workforce Planning")

        st.plotly_chart(
            workforce_chart(workforce),
            use_container_width=True,
        )

        w1, w2, w3 = st.columns(3)

        with w1:
            st.metric(
                "Labour Cost",
                f"₹{workforce['ProjectedLaborCost'].sum():,.0f}"
            )

        with w2:
            st.metric(
                "Hiring Days",
                int((workforce["HiringRequired"] > 0).sum())
            )

        with w3:
            st.metric(
                "Avg Utilisation",
                f"{workforce['WorkerUtilization(%)'].mean():.1f}%"
            )