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

    # ============================================================
    # PAGE-SPECIFIC STYLING
    # ============================================================

    st.markdown(
        """
        <style>

        /* ========================================================
           EXPANDER
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
           INVENTORY PROCESS CARDS
           ======================================================== */

        .inventory-process-card {
            min-height: 210px;
            height: 210px;
            padding: 24px;
            border-radius: 16px;
            background: #E7F1FF;
            border: 1px solid #D1E3FA;
            box-sizing: border-box;
        }

        .inventory-process-card h3 {
            margin-top: 0;
            margin-bottom: 14px;
            color: #24324A;
            font-size: 21px;
        }

        .inventory-process-card p {
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
        "Inventory Planning",
        "90-day inventory planning based on forecasted demand",
    )

    # ============================================================
    # KPI SUMMARY
    # ============================================================

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card(
            "Opening Stock",
            f"{int(metrics['opening_stock']):,}",
            "Units available at start",
            icon="📦",
        )

    with c2:
        kpi_card(
            "Ending Stock",
            f"{int(metrics['ending_stock']):,}",
            "Units remaining at end",
            icon="🏭",
        )

    with c3:
        kpi_card(
            "Service Level",
            f"{metrics['service_level']:.1f}%",
            "Demand fulfilled",
            icon="⭐",
        )

    with c4:
        kpi_card(
            "Purchase Orders",
            f"{int(metrics['purchase_orders'])}",
            "Replenishment orders",
            icon="🛒",
        )

    # ============================================================
    # KPI EXPLANATION
    # ============================================================

    st.markdown("---")

    with st.expander("ℹ️ What do these inventory KPIs mean?"):

        st.markdown(
            """
### Opening Stock

The amount of inventory available when the 90-day planning simulation begins.

### Ending Stock

The amount of inventory remaining at the end of the 90-day planning period.

### Service Level

Service Level measures how reliably the inventory plan satisfies
forecasted demand **without a stockout**.

**100% Service Level means:**

> No stockout occurred during the simulated planning period, so all
> forecasted demand was fulfilled without inventory shortage.

It does **not** mean that the warehouse is 100% full.

### Purchase Orders

The number of replenishment orders generated by the inventory planning
engine when additional stock is required.
"""
        )

    # ============================================================
    # INVENTORY TREND
    # ============================================================

    st.markdown("---")

    st.subheader("90-Day Inventory Trend")

    st.caption(
        "Projected inventory levels and replenishment requirements "
        "throughout the forecast horizon."
    )

    st.plotly_chart(
        inventory_chart(inventory_report),
        use_container_width=True,
    )

    # ============================================================
    # HOW THE INVENTORY PLAN WORKS
    # ============================================================

    st.markdown("---")

    st.subheader("How the Inventory Plan Works")

    st.caption(
        "The planning engine follows a three-stage decision process."
    )

    p1, p2, p3 = st.columns(3)

    with p1:
        st.markdown(
            """
            <div class="inventory-process-card">

            <h3>1. Forecast Demand</h3>

            <p>
            The Prophet forecasting model estimates expected demand
            for each day. These demand estimates become the input
            for inventory planning.
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    with p2:
        st.markdown(
            """
            <div class="inventory-process-card">

            <h3>2. Monitor Inventory</h3>

            <p>
            The system tracks available inventory, incoming purchase
            orders, safety stock and the reorder point.
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    with p3:
        st.markdown(
            """
            <div class="inventory-process-card">

            <h3>3. Replenish</h3>

            <p>
            When inventory position reaches the replenishment
            threshold, the system generates a purchase order to
            maintain inventory availability.
            </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    # ============================================================
    # INVENTORY CONCEPTS
    # ============================================================

    st.markdown("---")

    with st.expander("📘 Inventory Planning Concepts"):

        st.markdown(
            """
### Safety Stock

Extra inventory kept as a buffer against demand variability and uncertainty.

### Reorder Point

The inventory level at which a replenishment order should be placed
so that new stock arrives before inventory becomes insufficient.

### Inventory Position

The effective inventory available for planning, considering both
current inventory and inventory that is already on order.

### EOQ — Economic Order Quantity

The calculated replenishment quantity used by the planning system
when a new purchase order is required.

### Planning Flow

**Forecasted Demand → Safety Stock → Reorder Point → Inventory Position → Replenishment**

The system therefore makes proactive inventory decisions instead of
waiting until a stockout occurs.
"""
        )

    # ============================================================
    # INVENTORY DATA
    # ============================================================

    st.markdown("---")

    left, right = st.columns([1, 2])

    with left:

        st.subheader("Inventory KPIs")

        st.caption(
            "Detailed KPI values generated by the inventory engine."
        )

        st.dataframe(
            inventory_kpis,
            use_container_width=True,
            hide_index=True,
        )

    with right:

        st.subheader("Inventory Planning Report")

        st.caption(
            "Day-by-day inventory simulation and replenishment decisions."
        )

        st.dataframe(
            inventory_report,
            use_container_width=True,
            hide_index=True,
        )

    # ============================================================
    # FINAL INTERPRETATION
    # ============================================================

    st.markdown("---")

    if metrics["service_level"] >= 100:

        st.success(
            f"""
### Inventory Planning Result

The 90-day inventory simulation achieved a **{metrics['service_level']:.1f}% service level**.

This means the planned inventory was sufficient to satisfy the
forecasted demand throughout the simulation without a stockout.

- **Opening Stock:** {int(metrics['opening_stock']):,} units
- **Ending Stock:** {int(metrics['ending_stock']):,} units
- **Purchase Orders:** {int(metrics['purchase_orders'])}

The system maintained demand availability while using replenishment
orders to manage inventory over the forecast horizon.
"""
        )

    else:

        st.warning(
            f"""
### Inventory Planning Result

The simulated service level was **{metrics['service_level']:.1f}%**.

This indicates that some forecasted demand could not be fully satisfied
during the planning period and inventory shortages occurred.

The detailed planning report above can be used to identify the dates
where replenishment was insufficient.
"""
        )