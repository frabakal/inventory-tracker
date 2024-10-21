import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("Economic Order Quantity (EOQ)")

# --- GSHEETS CONNECTION & SQL QUERIES ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ESTABLISH INVENTORY DATAFRAME ---
data = conn.read(worksheet="EOQ")
sql = '''
SELECT
    "Variables",
    "Values"
FROM
    EOQ
'''
df_eoq = conn.query(sql=sql, ttl=30)
current_eoq = df_eoq.iloc[0]["Values"]

# --- CSS STYLE ---
style = """
    <style>
    .custom-button {
        width: 150px;
        height: 40px;
        margin: 0 auto;
    }
    strong, b {
        color: #36cbd3;
    }
    </style>
"""
st.markdown(style, unsafe_allow_html=True)

@st.dialog("Change EOQ")
def show_eoq(current_eoq, df_eoq):
    current_eoq = int(current_eoq)
    new_eoq = st.number_input("Current EOQ", value=current_eoq, step=1)

    if st.button("Save"):
        # Validate if EOQ has changed
        if new_eoq != current_eoq:
            df_eoq.at[0, "Values"] = new_eoq  # Update EOQ value in DataFrame
            conn.update(worksheet="EOQ", data=df_eoq)  # Save to Google Sheets
            st.success("EOQ updated successfully!")
            st.rerun()  # Refresh the app after saving
        else:
            st.warning("No changes were made.")

col1, col2, col3 = st.columns(3)
con1 = col1.container(border=True)
con2 = col2.container(border=True)

with col1:
    with con1:
        st.subheader("EOQ Calculator")
        cost_per_order = st.number_input("Cost per order", min_value=0.0, value=0.0)
        annual_demand = st.number_input("Annual demand", min_value=0.0, value=0.0)
        holding_cost = st.number_input("Holding cost", min_value=0.01, value=1.0)
        col4, col5 = st.columns(2, gap="small", vertical_alignment="center")
        with col4:
            if st.button("Calculate"):
                if holding_cost <= 0:  # Validate to prevent division by zero
                    st.error("Holding cost must be greater than 0.")
                else:
                    eoq = ((2 * annual_demand * cost_per_order) / holding_cost) ** 0.5
                    with col5:
                        st.write(f"**EOQ:** {eoq:.0f}")
        
with col2:
    with con2:
        st.subheader("Current EOQ")
        st.write(f"**EOQ:** {current_eoq:.0f}")
        if st.button("Edit"):
            show_eoq(current_eoq, df_eoq)