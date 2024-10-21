import re

import streamlit as st
import requests

def gen_report_form():
    with st.form("gen_report_form"):
        name = st.text_input("Select Start Date")
        email = st.text_input("Select End Date")
        submit_button = st.form_submit_button("Submit")