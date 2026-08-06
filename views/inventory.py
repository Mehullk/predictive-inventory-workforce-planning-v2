import streamlit as st

from utils.loader import (
    inventory_kpis,
    inventory_report,
)

from utils.metrics import executive_metrics

from components.cards import (
    section_title,
    kpi_card,
)

from components.charts import (
    inventory_chart,
)


def inventory_page():

    metrics = executive_metrics()

    section_title(
        "Inventory Planning",
        "Inventory KPIs and planning recommendations",
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card(
            "Opening Stock",
            f"{int(metrics['opening_stock']):,}",
            icon="📦"
        )

    with c2:
        kpi_card(
            "Ending Stock",
            f"{int(metrics['ending_stock']):,}",
            icon="🏭"
        )

    with c3:
        kpi_card(
            "Service Level",
            f"{metrics['service_level']:.1f}%",
            icon="⭐"
        )

    with c4:
        kpi_card(
            "Purchase Orders",
            f"{int(metrics['purchase_orders'])}",
            icon="🛒"
        )

    st.markdown("---")

    st.subheader("Inventory Trend")

    st.plotly_chart(
        inventory_chart(inventory_report),
        use_container_width=True,
    )

    st.markdown("---")

    left, right = st.columns([1, 2])

    with left:

        st.subheader("Inventory KPIs")

        st.dataframe(
            inventory_kpis,
            use_container_width=True,
            hide_index=True,
        )

    with right:

        st.subheader("Inventory Planning Report")

        st.dataframe(
            inventory_report,
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    st.success(
        f"""
### Inventory Summary

- **Opening Stock:** {int(metrics['opening_stock']):,}
- **Ending Stock:** {int(metrics['ending_stock']):,}
- **Service Level:** {metrics['service_level']:.1f}%
- **Purchase Orders Generated:** {int(metrics['purchase_orders'])}

The inventory plan has been generated using the forecasted demand from the Prophet model and recommends replenishment quantities to maintain the target service level.
"""
    )