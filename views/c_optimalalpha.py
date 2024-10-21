import streamlit as st
import numpy as np
from streamlit_gsheets import GSheetsConnection

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

# Load the data from Google Sheets
df_inventory = load_inventory_data()

# --- CSS STYLE ---
style = """
    <style>
    .custom-button {
        width: 150px;
        height: 40px;
        margin: 0 auto;
    }
    strong, b {
        color: #ff6700;
    }
    </style>
"""
st.markdown(style, unsafe_allow_html=True)

# Extract the "Demand (AT)" column for analysis
if "Demand (AT)" in df_inventory.columns:
    data = df_inventory["Demand (AT)"].tolist()

# Function to calculate the Mean Squared Error (MSE)
def calculate_mse(data, forecast):
    return np.mean((np.array(data[1:]) - np.array(forecast[1:])) ** 2)

# Function to calculate the Mean Absolute Error (MAE)
def calculate_mae(data, forecast):
    return np.mean(np.abs(np.array(data[1:]) - np.array(forecast[1:])))

# Function to calculate the Mean Absolute Percentage Error (MAPE)
def calculate_mape(data, forecast):
    non_zero_data = np.array(data[1:])
    forecast_values = np.array(forecast[1:])
    mask = non_zero_data != 0
    return np.mean(np.abs((non_zero_data[mask] - forecast_values[mask]) / non_zero_data[mask])) * 100

# Function to perform Simple Exponential Smoothing
def simple_exponential_smoothing(data, alpha):
    forecast = [data[0]]  # The first forecast is the first data point
    for i in range(1, len(data)):
        forecast.append(alpha * data[i - 1] + (1 - alpha) * forecast[-1])
    return forecast

# Function to find the optimal alpha by minimizing MSE, MAE, and MAPE
def find_optimal_alpha(data):
    best_mse, best_mae, best_mape = float('inf'), float('inf'), float('inf')
    best_alpha_mse = best_alpha_mae = best_alpha_mape = 0.0
    results = []

    for alpha in np.arange(0.01, 1.01, 0.01):
        forecast = simple_exponential_smoothing(data, alpha)
        mse = calculate_mse(data, forecast)
        mae = calculate_mae(data, forecast)
        mape = calculate_mape(data, forecast)

        results.append((alpha, mse, mae, mape))

        if mse < best_mse:
            best_mse, best_alpha_mse = mse, alpha
        if mae < best_mae:
            best_mae, best_alpha_mae = mae, alpha
        if mape < best_mape:
            best_mape, best_alpha_mape = mape, alpha

    return (best_alpha_mse, best_mse), (best_alpha_mae, best_mae), (best_alpha_mape, best_mape), results

# Streamlit Interface
st.title("Simple Exponential Smoothing & Error Metrics")

# Find optimal alphas and display results
(opt_mse, mse_value), (opt_mae, mae_value), (opt_mape, mape_value), results = find_optimal_alpha(data)

# Display Optimal Alphas
st.subheader("Optimal Alphas")

@st.dialog("View Data")
def show_table(df):
    st.write(df)

if st.button("View Data"):
    show_table(df_inventory)

col = st.columns([2,2,2], gap="small",)
col[0].write(f"**Optimal Alpha for MSE:** {opt_mse:.2f} (MSE: {mse_value:.4f})")
col[1].write(f"**Optimal Alpha for MAE:** {opt_mae:.2f} (MAE: {mae_value:.4f})")
col[2].write(f"**Optimal Alpha for MAPE:** {opt_mape:.2f} (MAPE: {mape_value:.2f}%)")

# Display Error Metrics with Bold Formatting for Optimal Values
st.subheader("MSE, MAE, and MAPE for All Alphas")

# Print each row with bold formatting for optimal values
for alpha, mse, mae, mape in results:
                
    mse_str = f"**{mse:.4f}**" if mse == mse_value else f"{mse:.4f}"
    mae_str = f"**{mae:.4f}**" if mae == mae_value else f"{mae:.4f}"
    mape_str = f"**{mape:.2f}%**" if mape == mape_value else f"{mape:.2f}%"

    with st.container(border=True):
        cols = st.columns([2,2,2,2])
        cols[0].write(f"Alpha {alpha:.2f}")
        cols[1].write(f"MSE = {mse_str}")
        cols[2].write(f"MAE = {mae_str}")
        cols[3].write(f"MAPE = {mape_str}")
