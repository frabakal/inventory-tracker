import streamlit as st

def update_inv_form():
    with st.form("update_inv_form"):
        # Dropdown to select the field to update
        field = st.selectbox("Select field to update:", ["Added", "Sold", "Damaged"])

        # Integer input for new value with validation
        new_value = st.number_input(
            f"Input Amount:",
            min_value=0,
            value=0,
            step=1,
        )

        # Submit button
        submit_button = st.form_submit_button("Submit")

    # Return values to be handled in the main app logic
    if submit_button:
        return field, new_value
    return None, None
