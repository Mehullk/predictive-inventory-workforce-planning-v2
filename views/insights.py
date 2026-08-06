import streamlit as st

from utils.metrics import executive_metrics

from components.cards import (
    section_title,
    kpi_card,
)


def insights_page():

    metrics = executive_metrics()

    workforce_gap = metrics["workers"] - metrics["staff"]

    section_title(
        "Executive Insights",
        "Business intelligence generated from forecasting, inventory, and workforce planning",
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card(
            "Forecast Accuracy",
            f"{metrics['accuracy']:.2f}%",
            icon="🎯"
        )

    with c2:
        kpi_card(
            "Service Level",
            f"{metrics['service_level']:.1f}%",
            icon="⭐"
        )

    with c3:
        kpi_card(
            "90-Day Demand",
            f"{int(metrics['sales90']):,}",
            icon="📈"
        )

    with c4:
        kpi_card(
            "Workforce Gap",
            f"{int(workforce_gap)}",
            icon="👥"
        )

    st.markdown("---")

    st.subheader("Executive Summary")

    st.success(f"""
### Key Business Highlights

- Forecast Accuracy: **{metrics['accuracy']:.2f}%**
- Expected Demand (90 Days): **{int(metrics['sales90']):,} units**
- Service Level: **{metrics['service_level']:.1f}%**
- Purchase Orders Generated: **{int(metrics['purchase_orders'])}**
- Peak Workforce Required: **{int(metrics['workers'])}**
- Current Workforce: **{int(metrics['staff'])}**
""")

    st.markdown("---")

    recommendations = []

    if metrics["service_level"] >= 95:
        recommendations.append(
            "✅ Inventory service level is excellent. Maintain the current replenishment strategy."
        )
    elif metrics["service_level"] >= 90:
        recommendations.append(
            "⚠️ Inventory service level is acceptable but should be monitored closely."
        )
    else:
        recommendations.append(
            "❌ Inventory service level is below target. Increase safety stock or review reorder policies."
        )

    if workforce_gap > 0:
        recommendations.append(
            f"👷 Hire or allocate approximately **{int(workforce_gap)}** additional workers before peak demand."
        )
    elif workforce_gap < 0:
        recommendations.append(
            f"👥 Current workforce exceeds projected demand by **{abs(int(workforce_gap))}** employees."
        )
    else:
        recommendations.append(
            "✅ Current workforce exactly matches the forecasted demand."
        )

    if metrics["accuracy"] >= 90:
        recommendations.append(
            "📊 Forecast reliability is high. Planning decisions can confidently rely on the current forecasting model."
        )
    elif metrics["accuracy"] >= 80:
        recommendations.append(
            "📊 Forecast performance is good. Continue monitoring forecast deviations."
        )
    else:
        recommendations.append(
            "⚠️ Forecast accuracy should be improved before making long-term planning decisions."
        )

    st.subheader("Business Recommendations")

    for recommendation in recommendations:
        st.markdown(f"- {recommendation}")

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
        st.success("🟢 Operational Health: Excellent")
    elif score == 2:
        st.info("🟡 Operational Health: Good")
    else:
        st.error("🔴 Operational Health: Needs Attention")