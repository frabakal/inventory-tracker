import streamlit as st

def addweek_form():
    with st.form("addweek_form"):
        # Select Start Week date
        new_start_week = st.date_input("Select Start Date:")
        
        # Select End Week date
        new_end_week = st.date_input("Select End Date:")

        # Integer input for new value with validation
        inv_value = st.number_input(
            f"Input Amount:",
            min_value=0,
            value=0,
            step=1,
        )

        # Submit button
        submit_button = st.form_submit_button("Submit")

    if submit_button:
        # Convert the dates to the desired format: MMDDYY
        new_start_week_str = new_start_week.strftime('%m%d%y')
        new_end_week_str = new_end_week.strftime('%m%d%y')

        # Return formatted dates and inventory value
        return new_start_week_str, new_end_week_str, inv_value

    # Return None if not submitted
    return None, None, None