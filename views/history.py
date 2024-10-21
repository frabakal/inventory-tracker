import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from forms.editweek import editweek_form

st.title("History")

# --- GSHEETS CONNECTION & DATA LOADING ---
conn = st.connection("gsheets", type=GSheetsConnection)
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

# --- EDIT WEEK DIALOG ---
@st.dialog("Edit Week")
def show_editweek_form(index, row):
    new_demand, new_added, new_sold, new_damaged = editweek_form(row)
    # Update the DataFrame
    if new_demand and new_added and new_sold and new_damaged:
        df_inventory.at[index, 'Demand (AT)'] = new_demand
        df_inventory.at[index, 'Added'] = new_added
        df_inventory.at[index, 'Sold'] = new_sold
        df_inventory.at[index, 'Damaged'] = new_damaged

        # Push changes to Google Sheets
        conn.update(worksheet="Sheet1", data=df_inventory)
        st.success(f"Successfully Edited Week.")
        st.rerun()

# --- PAGINATION SETTINGS ---
rows_per_page = 10
total_pages = (len(df_inventory) + rows_per_page - 1) // rows_per_page  # Ceiling division

if 'page' not in st.session_state:
    st.session_state.page = 0

# --- PAGINATION BUTTON CALLBACKS ---
def go_to_page(page):
    st.session_state.page = page

def prev_page():
    if st.session_state.page > 0:
        st.session_state.page -= 1

def next_page():
    if st.session_state.page < total_pages - 1:
        st.session_state.page += 1

# --- DISPLAY PAGINATION CONTROLS AT THE TOP ---
col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3], vertical_alignment="center")

with col2:
    if st.session_state.page == 0:
        pass
    else:
        st.button("Previous", on_click=prev_page)
        pass

with col4:
    if st.session_state.page == total_pages-1:
        pass
    else:
        st.button("Next", on_click=next_page)
        pass

# --- DISPLAY CURRENT PAGE INFO ---
with col3:
    st.write(f"Page {st.session_state.page + 1} of {total_pages}")

# --- DISPLAY CURRENT PAGE ---
start_row = st.session_state.page * rows_per_page
end_row = start_row + rows_per_page
df_page = df_inventory.iloc[start_row:end_row]

# --- DISPLAY DATA ROWS ---
for index, row in df_page.iterrows():
    with st.container(border=True):
        cols = st.columns(8)  # 7 columns for the data
        cols[0].write(f"**Week:** {row['Week']:.0f}")
        cols[1].write(f"**Week Start:** {row['Week Start']}")
        cols[2].write(f"**Week End:** {row['Week End']}")
        cols[3].write(f"**Demand (AT):** {row['Demand (AT)']:.0f}")
        cols[4].write(f"**Added:** {row['Added']:.0f}")
        cols[5].write(f"**Sold:** {row['Sold']:.0f}")
        cols[6].write(f"**Damaged:** {row['Damaged']:.0f}")
        # --- Edit Button ---
        if cols[7].button("Edit", key=f"edit-{index}"):
            show_editweek_form(index, row)

# --- DISPLAY PAGINATION CONTROLS AT THE TOP ---
col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3], vertical_alignment="center")

with col2:
    if st.session_state.page == 0:
        pass
    else:
        st.button("Previous ", on_click=prev_page)
        pass

with col4:
    if st.session_state.page == total_pages-1:
        pass
    else:
        st.button("Next ", on_click=next_page)
        pass

# --- DISPLAY CURRENT PAGE INFO ---
with col3:
    st.write(f"Page {st.session_state.page + 1} of {total_pages}")