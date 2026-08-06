import streamlit as st

from utils.loader import (
    workforce,
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

    section_title(
        "Workforce Planning",
        "AI-assisted workforce requirement planning",
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        kpi_card(
            "Current Staff",
            f"{int(metrics['staff'])}",
            "Available Workforce",
            "#3B82F6",
            "👥",
        )

    with c2:
        kpi_card(
            "Peak Workforce",
            f"{int(metrics['workers'])}",
            "Maximum Required",
            "#F59E0B",
            "👷",
        )

    with c3:
        gap = int(metrics["workers"] - metrics["staff"])

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
            "Workforce Gap",
            f"{gap}",
            delta,
            color,
            "⚖️",
        )

    st.markdown("---")

    st.subheader("Required Workforce Trend")

    st.plotly_chart(
        workforce_chart(workforce),
        use_container_width=True,
    )

    st.markdown("---")

    st.subheader("Workforce Planning Report")

    st.dataframe(
        workforce,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")

    gap = int(metrics["workers"] - metrics["staff"])

    if gap > 0:

        st.warning(
            f"""
### Workforce Recommendation

- Current Staff: **{int(metrics['staff'])}**
- Peak Workforce Required: **{int(metrics['workers'])}**
- Additional Staff Needed: **{gap}**

Based on the forecasted demand, hiring or reallocating approximately **{gap}** additional workers is recommended during peak demand periods.
"""
        )

    elif gap < 0:

        st.success(
            f"""
### Workforce Recommendation

Current staffing exceeds the projected peak demand by **{abs(gap)}** employees.

No additional hiring is required. Existing staff can be reallocated to improve operational efficiency.
"""
        )

    else:

        st.success(
            """
### Workforce Recommendation

Current staffing perfectly matches the forecasted workforce requirement.

No hiring or downsizing is recommended.
"""
        )