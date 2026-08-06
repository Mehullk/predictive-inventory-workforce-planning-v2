import streamlit as st


def section_title(title: str, subtitle: str = ""):
    st.title(title)

    if subtitle:
        st.caption(subtitle)

    st.write("")


def kpi_card(title, value, delta=None, delta_color="normal", icon="📊"):

    with st.container(border=True):

        left, right = st.columns([5,1], vertical_alignment="top")

        with left:

            st.caption(title)

            st.markdown(
                f"""
                <div style="
                    font-size:42px;
                    font-weight:800;
                    color:#24324A;
                    line-height:1.1;
                    margin-top:-4px;
                    margin-bottom:12px;
                ">
                    {value}
                </div>
                """,
                unsafe_allow_html=True
            )

            if delta:

                if delta_color in ["#22C55E", "#D9F5E7"]:
                    bg="#DDF6E8"

                elif delta_color in ["#3B82F6", "#B8DBFC"]:
                    bg="#DCEEFF"

                elif delta_color in ["#F59E0B", "#FFF7C7"]:
                    bg="#FFF6CC"

                elif delta_color in ["#EF4444", "#FFE3E3"]:
                    bg="#FFE8EC"

                else:
                    bg="#EEF4FF"

                st.markdown(
                    f"""
                    <div style="
                        display:inline-block;
                        background:{bg};
                        padding:8px 16px;
                        border-radius:12px;
                        font-weight:600;
                        font-size:15px;
                    ">
                        {delta}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with right:

            st.markdown(
                f"""
                <div style="
                    text-align:right;
                    font-size:44px;
                    margin-top:8px;
                ">
                    {icon}
                </div>
                """,
                unsafe_allow_html=True
            )


def info_card(title, body):

    with st.container(border=True):

        st.subheader(title)

        st.write(body)


def status_card(title, status):

    with st.container(border=True):

        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(title)

        with col2:

            if status.lower() == "critical":
                st.error(status)

            elif status.lower() == "warning":
                st.warning(status)

            else:
                st.success(status)