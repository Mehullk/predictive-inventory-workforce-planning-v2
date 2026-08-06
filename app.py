import streamlit as st

from components.sidebar import render_sidebar

from views.dashboard import dashboard_page
from views.forecast import forecast_page
from views.inventory import inventory_page
from views.workforce import workforce_page
from views.insights import insights_page


st.set_page_config(
    page_title="Predictive Inventory & Workforce Planning",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

with open("assets/style.css") as css:
    st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)


page = render_sidebar()


if page == "Dashboard":
    dashboard_page()

elif page == "Forecast":
    forecast_page()

elif page == "Inventory":
    inventory_page()

elif page == "Workforce":
    workforce_page()

elif page == "Insights":
    insights_page()