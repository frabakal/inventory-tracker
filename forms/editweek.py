import streamlit as st

def editweek_form(row_data):
    with st.form("editweek_form"):
        demand_int = int(row_data["Demand (AT)"])
        added_int = int(row_data["Added"])
        sold_int = int(row_data["Sold"])
        damaged_int = int(row_data["Damaged"])
        st.write(f"**Week no. {row_data['Week']:.0f}: {row_data['Week Start']} - {row_data['Week End']}**")
        new_demand = st.number_input(
            "Demand (AT)", 
            value=demand_int,
            min_value=0,
            step=1
        )
        new_added = st.number_input(
            "Added", 
            value=added_int, 
            min_value=0,
            step=1
        )
        new_sold = st.number_input(
            "Sold", 
            value=sold_int, 
            min_value=0,
            step=1
        )
        new_damaged = st.number_input(
            "Damaged", 
            value=damaged_int, 
            min_value=0,
            step=1
        )

        # Submit button
        submit_button = st.form_submit_button("Save")

        if submit_button:
            return new_demand, new_added, new_sold, new_damaged
        return None, None, None, None