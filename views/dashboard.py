import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from datetime import datetime, timedelta, date
from streamlit_gsheets import GSheetsConnection
from forms.addweek import addweek_form
from forms.update_inv import update_inv_form
from forms.gen_report import gen_report_form

# --- GSHEETS CONNECTION & SQL QUERIES ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ESTABLISH INVENTORY DATAFRAME ---
data = conn.read(worksheet="Sheet1")
sql = '''
SELECT
    "Week Start",
    "Week End",
    "Week",
    "Demand (AT)",
    "Added",
    "Sold",
    "Damaged"
FROM
    Sheet1
ORDER BY
    "Week" DESC
'''
df_inventory = conn.query(sql=sql, ttl=30)

sql2 = '''
SELECT
    "Week Start",
    "Week End",
    "Week",
    "Demand (AT)",
    "Added",
    "Sold",
    "Damaged"
FROM
    Sheet1
ORDER BY
    "Week" ASC
'''
df_inventory2 = conn.query(sql=sql2, ttl=30)
df_inventory3 = conn.query(sql=sql2, ttl=30)

data = conn.read(worksheet="ROP")
sql3 = '''
SELECT
    "Variables",
    "Values"
FROM
    ROP
'''
df_rop = conn.query(sql=sql3, ttl=30)
alpha = df_rop.iloc[4]["Values"]
rop_ss = df_rop.iloc[2]["Values"]

data = conn.read(worksheet="Weights")
sql = '''
SELECT
    "Forecasts",
    "First",
    "Second",
    "Third"
FROM
    Weights
'''
df_weights = conn.query(sql=sql, ttl=30)
weight1 = df_weights.iloc[0]["First"]
weight2 = df_weights.iloc[0]["Second"]
weight3 = df_weights.iloc[0]["Third"]
weights = [weight1, weight2, weight3] 

# --- GRAPH ---
df_last_5_weeks = df_inventory.head(5)
# Reverse the order for chronological plotting (from oldest to newest)
df_last_5_weeks = df_last_5_weeks.iloc[::-1]
week_5 = df_last_5_weeks.iloc[0]["Week"]
week_1 = df_last_5_weeks.iloc[-1]["Week"]


# --- MOVING AVERAGE DEMAND FORECAST ---
if len(df_inventory) >= 3:
    df_last_3_weeks = df_inventory.head(3)
    next_week_ma_forecast = df_last_3_weeks["Demand (AT)"].mean()
else:
    next_week_ma_forecast = 0


# Calculate the 3-week moving average forecast shifted by 1 (to align with future weeks)
df_inventory2["3-Week MA Forecast"] = df_inventory2["Demand (AT)"].rolling(3).mean().shift(1)

# Filter rows with valid forecasts (skip first 3 weeks due to insufficient data)
df_valid_forecast1 = df_inventory2.dropna(subset=["3-Week MA Forecast"])

# --- ERROR METRICS CALCULATION ---
df_valid_forecast1["Absolute Error"] = abs(df_valid_forecast1["Demand (AT)"] - df_valid_forecast1["3-Week MA Forecast"])
df_valid_forecast1["Squared Error"] = df_valid_forecast1["Absolute Error"] ** 2
df_valid_forecast1["Percent Error"] = df_valid_forecast1["Absolute Error"] / df_valid_forecast1["Demand (AT)"]

# Compute total MAD, MSE, and MAPE
ma_mad = df_valid_forecast1["Absolute Error"].mean()  # Mean Absolute Deviation
ma_mse = df_valid_forecast1["Squared Error"].mean()   # Mean Squared Error
ma_mape = df_valid_forecast1["Percent Error"].mean() * 100  # Mean Absolute Percentage Error



# WEIGHTED MOVING AVERAGE DEMAND FORECAST
if len(df_inventory) >= 3:
    df_last_3_weeks = df_inventory.head(3)
    next_week_wma_forecast = (df_last_3_weeks["Demand (AT)"] * [0.5, 0.33, 0.17]).sum()
else:
    next_week_wma_forecast = 0

# --- 3-WEEK WEIGHTED MOVING AVERAGE FORECAST ---
# Helper function to apply weights to rolling windows
def weighted_moving_average(window):
    return (window * weights).sum()

# Apply weighted moving average with a rolling window of 3, shifted by 1 (to align with the forecast)
df_inventory2["3-Week WMA Forecast"] = (
    df_inventory2["Demand (AT)"]
    .rolling(3)
    .apply(weighted_moving_average, raw=True)
    .shift(1)
)

# Filter rows with valid forecasts (skip first 3 weeks due to insufficient data)
df_valid_forecast2 = df_inventory2.dropna(subset=["3-Week WMA Forecast"])

# --- ERROR METRICS CALCULATION ---
df_valid_forecast2["Absolute Error"] = abs(df_valid_forecast2["Demand (AT)"] - df_valid_forecast2["3-Week WMA Forecast"])
df_valid_forecast2["Squared Error"] = df_valid_forecast2["Absolute Error"] ** 2
df_valid_forecast2["Percent Error"] = df_valid_forecast2["Absolute Error"] / df_valid_forecast2["Demand (AT)"]

# Compute total MAD, MSE, and MAPE
wma_mad = df_valid_forecast2["Absolute Error"].mean()  # Mean Absolute Deviation
wma_mse = df_valid_forecast2["Squared Error"].mean()   # Mean Squared Error
wma_mape = df_valid_forecast2["Percent Error"].mean() * 100  # Mean Absolute Percentage Error

# EXPONENTIAL SMOOTHING DEMAND FORECAST
df_inventory2["ES Forecast"] = pd.NA

for i in range(len(df_inventory2)):
    if i == 0:
        # Forecast for the first row equals its demand
        df_inventory2.at[i, "ES Forecast"] = df_inventory2.iloc[i]["Demand (AT)"]
    else:
        # ES Forecast: Previous forecast + alpha * (Previous demand - Previous forecast)
        prev_forecast = df_inventory2.iloc[i - 1]["ES Forecast"]
        prev_demand = df_inventory2.iloc[i - 1]["Demand (AT)"]
        df_inventory2.at[i, "ES Forecast"] = prev_forecast + alpha * (prev_demand - prev_forecast)

# Filter rows with valid forecasts (drop initial rows with NaNs)
df_valid_forecast3 = df_inventory2.dropna(subset=["3-Week WMA Forecast", "ES Forecast"])

# --- ERROR METRICS CALCULATION ---
# For Exponential Smoothing
df_valid_forecast3["ES Absolute Error"] = abs(df_valid_forecast3["Demand (AT)"] - df_valid_forecast3["ES Forecast"])
df_valid_forecast3["ES Squared Error"] = df_valid_forecast3["ES Absolute Error"] ** 2
df_valid_forecast3["ES Percent Error"] = df_valid_forecast3["ES Absolute Error"] / df_valid_forecast3["Demand (AT)"]

# --- COMPUTE TOTAL MAD, MSE, AND MAPE ---
# ES Metrics
es_mad = df_valid_forecast3["ES Absolute Error"].mean()
es_mse = df_valid_forecast3["ES Squared Error"].mean()
es_mape = df_valid_forecast3["ES Percent Error"].mean() * 100

# Calculate forecast for the next week
last_forecast = df_inventory2.iloc[-1]["ES Forecast"]
last_demand = df_inventory2.iloc[-1]["Demand (AT)"]
next_week_es_forecast = last_forecast + alpha * (last_demand - last_forecast)

# --- DATE CALCULATIONS ---
current_date = datetime.now()
last_week_end = pd.to_datetime(df_inventory.iloc[0]["Week End"])
if current_date > (last_week_end+ timedelta(days=1)):
    new_week_start = last_week_end + timedelta(days=1)
    new_week_end = new_week_start + timedelta(days=6)
    new_week_number = df_inventory.iloc[0]["Week"] + 1
    new_demand = df_inventory.iloc[0]["Demand (AT)"]
    new_row = pd.DataFrame({
        "Week Start": [new_week_start.strftime('%m/%d/%Y')],
        "Week End": [new_week_end.strftime('%m/%d/%Y')],
        "Week": [new_week_number],
        "Demand (AT)": [new_demand],
        "Added": [0],
        "Sold": [0],
        "Damaged": [0]
    })
    updated_df=pd.concat([df_inventory3, new_row], ignore_index=True)
    conn.update(worksheet="Sheet1", data=updated_df)
    st.error("System is updating... Please Refresh the page.")
else:
    pass

# --- CURRENT INVENTORY STATS ---
current_stock = df_inventory.iloc[0]["Demand (AT)"]
current_added = df_inventory.iloc[0]["Added"]
current_sold = df_inventory.iloc[0]["Sold"]
current_damaged = df_inventory.iloc[0]["Damaged"]
if current_stock < rop_ss:
    notify_reorder = (f"Stock Reorder Required")
else:
    notify_reorder = (f"Stock Reorder Not Required")

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


# --- FUNCTION FORMS ----
@st.dialog("Add Week")
def show_addweek_form(df_inventory3):
    new_start_week, new_end_week, inv_value = addweek_form()
    df_inventory4 = df_inventory3.copy()
    if new_start_week and new_end_week:
        # Ensure all input dates are parsed correctly, regardless of format
        new_start_dt = pd.to_datetime(new_start_week, errors='coerce')
        new_end_dt = pd.to_datetime(new_end_week, errors='coerce')

        if pd.isna(new_start_dt) or pd.isna(new_end_dt):
            st.error("Please enter valid dates in recognizable formats (e.g., 'MM/DD/YYYY', 'August 29, 2022').")
            return  # Exit if date parsing fails

        # Convert DataFrame columns to datetime with flexible parsing
        df_inventory3["Week Start"] = pd.to_datetime(df_inventory3["Week Start"], errors='coerce', dayfirst=False)
        df_inventory3["Week End"] = pd.to_datetime(df_inventory3["Week End"], errors='coerce', dayfirst=False)
        df_inventory3 = df_inventory3.dropna()
        if df_inventory3["Week Start"].isna().any() or df_inventory3["Week End"].isna().any():
            st.error("Some dates in your data could not be parsed. Please check the date formats.")
            return

        # Validate if new dates overlap with any existing week ranges
        overlapping_rows = df_inventory3[
            (df_inventory3["Week Start"] <= new_end_dt) &
            (df_inventory3["Week End"] >= new_start_dt)
        ]
        if not overlapping_rows.empty:
            st.error("The selected week range overlaps with an existing week. Please choose a different range.")
            return  # Exit if overlap is found

        # Validate if new dates are in the future
        today = date.today()
        if (pd.to_datetime(new_start_dt) > pd.to_datetime(today)) or (pd.to_datetime(new_end_dt) > pd.to_datetime(today)):
            st.warning(f"Start date and End date hasn't occured yet. Please choose another date.")
            return  # Exit if overlap is found

        # Add the new week with validated values
        new_row = pd.DataFrame({
            "Week Start": [new_start_dt.strftime('%m/%d/%Y')],
            "Week End": [new_end_dt.strftime('%m/%d/%Y')],
            "Week": [len(df_inventory3) + 1],  # New week ID
            "Demand (AT)": [inv_value],
            "Added": [0],
            "Sold": [0],
            "Damaged": [0]
        })

        # Append the new row and sort by 'Week Start'
        updated_df = pd.concat([df_inventory4, new_row], ignore_index=True)
        updated_df["Week Start"] = pd.to_datetime(updated_df["Week Start"], errors='coerce')
        updated_df = updated_df.sort_values(by="Week Start").reset_index(drop=True)

        # Recalculate week numbers
        updated_df["Week"] = range(1, len(updated_df) + 1)

        # Update the Google Sheet
        conn.update(worksheet="Sheet1", data=updated_df)

        st.success(f"Successfully added Week {len(updated_df)}: {new_start_dt.strftime('%m/%d/%Y')} to {new_end_dt.strftime('%m/%d/%Y')}.")
        st.rerun()

@st.dialog("Update Inventory")
def show_update_inv_form(current_added, current_sold, current_damaged, current_stock):
    field, new_value = update_inv_form()
    if field and new_value:
        if field == "Added":
            current_added += new_value
            current_stock += new_value
        elif field == "Sold":
            current_sold += new_value
            current_stock -= new_value
        elif field == "Damaged":
            current_damaged += new_value
            current_stock -= new_value

        # Update the Google Sheet with the new values
        df_inventory3.iloc[-1, df_inventory3.columns.get_loc(field)] += new_value
        df_inventory3.iloc[-1, df_inventory3.columns.get_loc("Demand (AT)")] = current_stock
        conn.update(worksheet="Sheet1", data=df_inventory3)
        st.success(f"Inventory updated successfully! {current_stock:.0f} in stock.")
        st.rerun()

@st.dialog("Generate Report")
def show_gen_report_form():
    gen_report_form()

@st.dialog("Forecast Error Metrics", width="large")
def show_error_metrics():
    # Function to display the appropriate DataFrame based on button click
    def show_dataframe(selected_df):
        if selected_df == 'df1':
            return df_valid_forecast1[["Week Start", "Week","Demand (AT)", "3-Week MA Forecast", "Absolute Error", "Squared Error", "Percent Error"]]
        elif selected_df == 'df2':
            return df_valid_forecast2[["Week Start", "Week", "Demand (AT)", "3-Week WMA Forecast", "Absolute Error", "Squared Error", "Percent Error"]]
        elif selected_df == 'df3':
            return df_valid_forecast3[["Week Start", "Week", "Demand (AT)", "ES Forecast", "ES Absolute Error", "ES Squared Error", "ES Percent Error"]]

    # Create columns for buttons
    col1, col2, col3 = st.columns([1, 1, 1])

    # Initialize a variable to hold the selected DataFrame
    selected_dataframe = None

    # Button actions within each column
    with col1:
        if st.button("3-Week MA Forecast", use_container_width=True):
            selected_dataframe = show_dataframe('df1')

    with col2:
        if st.button("3-Week WMA Forecast", use_container_width=True):
            selected_dataframe = show_dataframe('df2')

    with col3:
        if st.button("Exponential Smoothing", use_container_width=True):
            selected_dataframe = show_dataframe('df3')

    # Display the selected DataFrame below the buttons, if one is selected
    if selected_dataframe is not None:
        st.dataframe(selected_dataframe, use_container_width=True)

# --- HEADER SECTION ---
st.title("Inventory Tracker", anchor=False)

col1, col2, col3 = st.columns(3, gap="small")
with col1:
    if st.button("Add Week", use_container_width=True):
        show_addweek_form(df_inventory3)
with col2:
    if st.button("Update Inventory", use_container_width=True):
            show_update_inv_form(current_added, current_sold, current_damaged, current_stock)
with col3:
    if st.button("Generate Report", use_container_width=True):
            show_gen_report_form()

# --- MAIN DASHBOARD SECTION ---
st.write("\n")
st.write("\n")
col1, col2 = st.columns(2, gap="small", vertical_alignment="center")
con1 = col1.container(border=True)
con2 = col1.container(border=True)
with col1:

    # CURRENT INVENTORY CONTAINER
    with con1:
        st.subheader("Current Inventory", anchor=False)
        col3, col4 = st.columns([2,1], gap="small", vertical_alignment="top")
        with col3:
            st.write(
                f"""
            - **Date:** {date.today().strftime("%m/%d/%Y")}
            - **Current Stock:** {current_stock:.0f}
            - **Sold:** {current_sold:.0f}
            - **Status:** {notify_reorder}
            """
            )
        with col4:
            st.write(
                f"""
            - **Week No.** {week_1:.0f}
            - **Added:** {current_added:.0f}
            - **Damaged:** {current_damaged:.0f}
            """
            )

    # NEXT WEEK'S FORECAST CONTAINER
    with con2:
        
        col8, col9 = st.columns([3,1], gap="small", vertical_alignment="center")
        with col8:
            st.subheader("Next Week's Forecast", anchor=False)
        with col9:
            #use button to view more
            if st.button("View More", use_container_width=True):
                show_error_metrics()
        st.write(f"**3 week Moving Average:** {next_week_ma_forecast:.2f}")
        col5, col6, col7 = st.columns(3, gap="small", vertical_alignment="top")
        with col5:
            st.write(f"MAD: {ma_mad:.2f}")
        with col6:
            st.write(f"MSE: {ma_mse:.2f}")
        with col7:
            st.write(f"MAPE: {ma_mape:.2f}%")
        st.write(f"**3 week Weighted Moving Average:** {next_week_wma_forecast:.2f}")
        col5, col6, col7 = st.columns(3, gap="small", vertical_alignment="top")
        with col5:
            st.write(f"MAD: {wma_mad:.2f}")
        with col6:
            st.write(f"MSE: {wma_mse:.2f}")
        with col7:
            st.write(f"MAPE: {wma_mape:.2f}%")
        st.write(f"**Exponential Smoothing:** {next_week_es_forecast:.2f}")
        col5, col6, col7 = st.columns(3, gap="small", vertical_alignment="top")
        with col5:
            st.write(f"MAD: {es_mad:.2f}")
        with col6:
            st.write(f"MSE: {es_mse:.2f}")
        with col7:
            st.write(f"MAPE: {es_mape:.2f}%")

# GRAPH
with col2:
    st.subheader(f"Week {week_5:.0f} - Week {week_1:.0f} Inventory with Forecasts")
    # Prepare data for the graph
    df_graph_data = df_last_5_weeks.set_index("Week")[["Demand (AT)"]]
    last_week = df_last_5_weeks.iloc[-1]["Week"]
    next_week = last_week + 1  # Increment the week number

    # Create a new DataFrame with the demand + forecast points for connection
    df_combined = df_graph_data.copy()
    df_combined.loc[next_week] = None  # Placeholder for forecast connections

    # Create individual forecast points for graphing
    forecast_data = {
        "3-Week MA Forecast": next_week_ma_forecast,
        "3-Week WMA Forecast": next_week_wma_forecast,
        "Exponential Smoothing": next_week_es_forecast
    }

    # Plotting the graph
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot Demand (AT) with the existing data points
    df_graph_data["Demand (AT)"].plot(
        ax=ax, marker='o', linestyle='-', label="Demand (AT)", color='black'
    )

    # Draw lines connecting the last demand point to the forecasts
    for label, forecast_value in forecast_data.items():
        ax.plot(
            [last_week, next_week],  # x-axis: last week to next week
            [df_graph_data.iloc[-1]["Demand (AT)"], forecast_value],  # y-axis: demand to forecast
            linestyle='--',
            marker='o',
            label=f"{label}",
            color={
                "3-Week MA Forecast": 'blue',
                "3-Week WMA Forecast": 'green',
                "Exponential Smoothing": 'red'
            }[label]
        )

    # Customize the graph
    ax.set_title("Inventory for the Last 5 Weeks with Next Week's Forecasts")
    ax.set_xlabel("Week")
    ax.set_ylabel("Demand (AT)")
    ax.legend(loc='upper left')
    ax.grid(True)

    # Display the graph in Streamlit
    st.pyplot(fig)
