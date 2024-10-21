import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.title("ROP")

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

# --- GSHEETS CONNECTION & SQL QUERIES ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ESTABLISH INVENTORY DATAFRAME ---
data = conn.read(worksheet="ROP")
sql = '''
SELECT
    "Variables",
    "Values"
FROM
    ROP
'''
df_rop = conn.query(sql=sql, ttl=30)

data = conn.read(worksheet="Sheet1")
sql = '''
SELECT
    "Week",
    "Demand (AT)",
FROM
    Sheet1
ORDER BY
    "Week" ASC
'''
df_inventory = conn.query(sql=sql, ttl=30)

lead_time = df_rop.iloc[0]["Values"]
current_rop = df_rop.iloc[1]["Values"]
current_ropss = df_rop.iloc[2]["Values"]
z_score = df_rop.iloc[3]["Values"]
alpha = df_rop.iloc[4]["Values"]
lead_time_in_weeks = lead_time / 7

@st.dialog("Change ROP")
def show_rop(lead_time, z_score):
    lead_time = int(lead_time)
    new_lead_time = st.number_input("Lead Time", value=lead_time, step=1)
    new_z_score = st.number_input("Z-Score", value=z_score, step=0.01)

    if st.button("Save"):
        # Validate if EOQ has changed
        if (new_lead_time != lead_time) or (new_z_score != z_score):
            if (new_lead_time > 0) or (new_z_score > 0):  # Validate to prevent division by zero
                df_rop.at[0, "Values"] = new_lead_time  # Update EOQ value in DataFrame
                df_rop.at[3, "Values"] = new_z_score  # Update EOQ value in DataFrame

                # EXPONENTIAL SMOOTHING DEMAND FORECAST
                df_inventory["ES Forecast"] = pd.NA

                for i in range(len(df_inventory)):
                    if i == 0:
                        # Forecast for the first row equals its demand
                        df_inventory.at[i, "ES Forecast"] = df_inventory.iloc[i]["Demand (AT)"]
                    else:
                        # ES Forecast: Previous forecast + alpha * (Previous demand - Previous forecast)
                        prev_forecast = df_inventory.iloc[i - 1]["ES Forecast"]
                        prev_demand = df_inventory.iloc[i - 1]["Demand (AT)"]
                        df_inventory.at[i, "ES Forecast"] = prev_forecast + alpha * (prev_demand - prev_forecast)
                
                # Compute new ROP and ROP with Safety Stock
                avg_forecast = df_inventory["ES Forecast"].mean()  # Average forecast over the period
                demand_during_lead = avg_forecast * (new_lead_time / 7)  # Demand during lead time
                std_dev = df_inventory["ES Forecast"].std()  # Standard deviation of forecast

                new_rop = demand_during_lead  # New ROP
                new_ropss = new_rop + new_z_score * std_dev * (new_lead_time / 7) ** 0.5  # ROP with Safety Stock

                # Update DataFrame with new ROP values
                df_rop.at[1, "Values"] = new_rop
                df_rop.at[2, "Values"] = new_ropss


                conn.update(worksheet="ROP", data=df_rop)  # Save to Google Sheets
                st.success("EOQ updated successfully!")
                st.rerun()  # Refresh the app after saving
            else:
                st.error("Lead Time and Z-Score must be greater than 0.")
        else:
            st.warning("No changes were made.")

col1, col2 = st.columns(2, gap="small", vertical_alignment="center")
con1 = col1.container(border=True)
con2 = col2.container(border=True)

with con1:
    st.subheader("Current ROP Settings")
    st.write(f"**Lead Time:** {lead_time:.0f}")
    st.write(f"**Z-Score:** {z_score:.2f}")
    st.write(f"**ROP:** {current_rop:.0f}")
    st.write(f"**ROP with Safety Stock:** {current_ropss:.0f}")
    if st.button("Edit"):
        show_rop(lead_time, z_score)

#input lead time
#input z-score
#view z-score image
#print rop & rop with safety stock

#df inventory &  es computations & alpha