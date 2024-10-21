import streamlit as st
import pandas as pd
import numpy as np
from streamlit_gsheets import GSheetsConnection

st.title("Optimal Alpha Calculation")

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

# --- GSHEETS CONNECTION & SQL QUERY ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)  # Cache data to reduce API calls
def load_inventory_data():
    sql = '''
    SELECT "Week", "Demand (AT)"
    FROM Sheet1
    ORDER BY "Week" ASC
    '''
    return conn.query(sql=sql)

df_inventory = load_inventory_data()

# --- FUNCTION TO CALCULATE FORECAST AND ERRORS ---
def calculate_forecast(alpha, demand_data):
    """Calculate Exponential Smoothing Forecast and Errors."""
    forecasts = [demand_data[0]]  # Initialize with the first demand as the forecast
    for i in range(1, len(demand_data)):
        prev_forecast = forecasts[-1]
        forecast = prev_forecast + alpha * (demand_data[i - 1] - prev_forecast)
        forecasts.append(forecast)

    forecasts = np.array(forecasts)
    mse = np.mean((demand_data - forecasts) ** 2)
    mae = np.mean(np.abs(demand_data - forecasts))
    mape = np.mean(np.abs((demand_data - forecasts) / demand_data)) * 100

    return mse, mae, mape, forecasts

# --- SEARCH FOR OPTIMAL ALPHA ---
alphas = np.arange(0.01, 1.01, 0.01)  # Alphas from 0.01 to 1.0
demand_data = df_inventory["Demand (AT)"].values

optimal_alpha = None
min_mse, min_mae, min_mape = float('inf'), float('inf'), float('inf')

for alpha in alphas:
    mse, mae, mape, _ = calculate_forecast(alpha, demand_data)
    if mse < min_mse:
        min_mse, optimal_alpha_mse = mse, alpha
    if mae < min_mae:
        min_mae, optimal_alpha_mae = mae, alpha
    if mape < min_mape:
        min_mape, optimal_alpha_mape = mape, alpha

# --- DISPLAY RESULTS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Optimal Alpha Results")
    st.write(f"**Optimal Alpha (MSE):** {optimal_alpha_mse:.2f}")
    st.write(f"**Optimal Alpha (MAE):** {optimal_alpha_mae:.2f}")
    st.write(f"**Optimal Alpha (MAPE):** {optimal_alpha_mape:.2f}")

with col2:
    st.subheader("Error Metrics")
    st.write(f"**Lowest MSE:** {min_mse:.2f}")
    st.write(f"**Lowest MAE:** {min_mae:.2f}")
    st.write(f"**Lowest MAPE:** {min_mape:.2f}%")

# --- PLOT FORECAST WITH OPTIMAL ALPHA ---
_, _, _, optimal_forecast = calculate_forecast(optimal_alpha_mse, demand_data)

st.subheader("Forecast Plot")
st.line_chart(pd.DataFrame({
    "Actual Demand": demand_data,
    "Optimal Forecast (MSE)": optimal_forecast
}))
