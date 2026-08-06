import streamlit as st

st.title("Border Test")

with st.container(border=True):
    st.write("This should have a border.")