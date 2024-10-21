import streamlit as st
st.set_page_config(layout="wide")

# --- HIDE STREAMLIT NAME ---
hide_st_style = """
            <style>
            #MaineMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """ 
st.markdown(hide_st_style, unsafe_allow_html=True)


# --- PAGE SETUP ---
dashboard_page = st.Page(
    page="views/dashboard.py",
    title="Inventory Tracker",
    icon=":material/bar_chart:",
    default=True,
)

history_page = st.Page(
    page="views/history.py",
    title="History",
    icon=":material/history:",
)

eoq_page = st.Page(
    page="views/c_eoq.py",
    title="EOQ",
    icon=":material/calculate:",
)

optimalalpha_page = st.Page(
    page="views/c_optimalalpha.py",
    title="Optimal Alpha",
    icon=":material/calculate:",
)

rop_page = st.Page(
    page="views/c_rop.py",
    title="ROP",
    icon=":material/calculate:",
)

adjust_metrics_page = st.Page(
    page="views/adjust_metrics.py",
    title="Adjust Metrics",
    icon=":material/calculate:",
)

# --- NAVIGATION SETUP [WITH SECTIONS] ---
pg = st.navigation(
    {
        "Inventory": [dashboard_page, history_page],
        "Calculations": [eoq_page, optimalalpha_page, rop_page, adjust_metrics_page],
    }
)

# --- SHARED ON ALL PAGES ---
st.sidebar.text("Thesis - Charlie Mulingtapang")

# --- RUN NAVIGATION ---
pg.run()
