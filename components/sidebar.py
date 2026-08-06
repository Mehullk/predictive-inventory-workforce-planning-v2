from streamlit_option_menu import option_menu
import streamlit as st


def render_sidebar():

    with st.sidebar:

        st.markdown(
            """
            <div style="padding-top:10px;padding-bottom:20px;">

            <div class="brand-title">
            📊 Predictive AI
            </div>

            <div class="brand-subtitle">
            Inventory & Workforce Planning
            </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        selected = option_menu(
            menu_title=None,
            options=[
                "Dashboard",
                "Forecast",
                "Inventory",
                "Workforce",
                "Insights",
            ],
            icons=[
                "speedometer2",
                "graph-up-arrow",
                "boxes",
                "people-fill",
                "lightbulb-fill",
            ],
            default_index=0,
            styles={
    "container": {
        "padding": "0!important",
        "background-color": "transparent",
    },

    "icon": {
    "color": "#FFFFFF",
    "font-size": "20px",
    },

    "nav-link": {
        "font-size": "17px",
        "font-weight": "600",
        "color": "#F8FAFC",
        "text-align": "left",
        "margin": "8px 0",
        "padding": "15px 18px",
        "border-radius": "18px",
        "--hover-color": "rgba(255,255,255,.06)",
        "transition": ".25s",
    },

    "nav-link-selected": {
    "background": "linear-gradient(90deg,#5B9DFF 0%,#8D7DFF 50%,#EC6AA8 100%)",
    "color": "#FFFFFF",
    "font-weight": "700",
    "border-radius": "20px",
    "box-shadow": "0 10px 22px rgba(124,184,255,.25)",
    },
}
        )

        st.markdown("---")

        st.markdown(
            """
            <div class="card">

            <b>🤖 AI Model</b>

            <br><br>

            <span class="success">● Prophet Loaded</span>

            <br>

            <span style="color:#CBD5E1;">
            Inventory Planner Ready
            </span>

            <br>

            <span style="color:#CBD5E1;">
            Workforce Planner Ready
            </span>

            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.caption("Version 1.0")

    return selected