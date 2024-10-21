import streamlit as st

from streamlit_gsheets import GSheetsConnection

st.title("Adjust Metrics")

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
data = conn.read(worksheet="ROP")
sql = '''
SELECT
    "Variables",
    "Values"
FROM
    ROP
'''
df_rop = conn.query(sql=sql, ttl=30)
alpha = df_rop.iloc[4]["Values"] #Obtain Alpha

data2 = conn.read(worksheet="Weights")
sql2 = '''
SELECT
    "Forecasts",
    "First",
    "Second",
    "Third"
FROM
    Weights
'''
df_weights = conn.query(sql=sql2, ttl=30)
weight1 = df_weights.iloc[0]["First"]
weight2 = df_weights.iloc[0]["Second"]
weight3 = df_weights.iloc[0]["Third"]
weights = [weight1, weight2, weight3]  # Obtain Weights: Most recent week gets higher weight

@st.dialog("Change Metrics")
def show_edit(alpha, weight1, weight2, weight3):
    new_alpha = st.number_input("Exponential Smoothing Alpha", value=alpha, step=0.01)
    new_weight1 = st.number_input("First Week Weight", value=weight1, step=0.01)
    new_weight2 = st.number_input("Second Week Weight", value=weight2, step=0.01)
    new_weight3 = st.number_input("Third Week Weight", value=weight3, step=0.01)

    if st.button("Save"):
        if (new_alpha > 0) and (new_weight1 > 0) and (new_weight2 > 0) and (new_weight3 > 0):  # Validate to prevent division by zero
            df_rop.at[4, "Values"] = new_alpha  # Update Alpha value in DataFrame
            conn.update(worksheet="ROP", data=df_rop)
            df_weights.at[0, "First"] = new_weight1  # Update First Week Weight value in DataFrame
            df_weights.at[0, "Second"] = new_weight2
            df_weights.at[0, "Third"] = new_weight3
            conn.update(worksheet="Weights", data=df_weights)
            st.success("Alpha and Weights updated successfully!")
            st.rerun()
        else:
            st.error("Alpha and Weights must be greater than 0.")
            pass

col1, col2 = st.columns(2)
con1 = col1.container(border=True)

with con1:
    st.subheader("Current Metrics Settings")
    st.write(f"**Exponential Smoothing Alpha:** {alpha:.2f}")
    st.write(f"**3-Week WMA Weights:**")
    st.write(f"Farthest Week: {weight1:.2f}")
    st.write(f"Middle Week: {weight2:.2f}")
    st.write(f"Closest Week: {weight3:.2f}")
    if st.button("Edit"):
        show_edit(alpha, weight1, weight2, weight3)