import streamlit as st
import pandas as pd
import os
from datetime import date
import io
import requests

# --- Page Configuration ---
st.set_page_config(
    page_title="Truck Logistics Dashboard",
    page_icon="🚚",
    layout="wide",
)

# --- API Configuration ---
FLASK_API_URL = st.secrets.get("FLASK_API_URL", "http://127.0.0.1:5000")
API_KEY = st.secrets.get("INTERNAL_API_KEY")

# --- Helper Functions ---

def get_operations_data(period="monthly"):
    """Fetch operations data from the Flask API."""
    if not API_KEY:
        st.error("Internal API Key is not configured in secrets.")
        return pd.DataFrame()

    headers = {'X-API-Key': API_KEY}
    params = {'period': period}
    try:
        response = requests.get(f"{FLASK_API_URL}/api/v1/export", headers=headers, params=params)
        response.raise_for_status() # Raises an exception for 4XX/5XX errors
        # Use io.StringIO to read the CSV response text into a DataFrame
        return pd.read_csv(io.StringIO(response.text))
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch data from API: {e}")
        return pd.DataFrame()

def to_excel(df: pd.DataFrame):
    """Converts a DataFrame to an Excel file in memory."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='LogisticsData')
    processed_data = output.getvalue()
    return processed_data

# --- Main Application UI ---

st.title("🚚 Daily Truck Logistics Operations")
st.markdown("---")

if not API_KEY or FLASK_API_URL == "http://127.0.0.1:5000":
    st.warning("API Key or URL not set for production. Please check your secrets.toml file.")

# --- Input Form for New Entry ---
st.header("Add New Operation")
with st.form("new_operation_form", clear_on_submit=True):
    # These fields should match the DailyOperation model in your Flask app
    operation_date = st.date_input("Operation Date", value=date.today())
    truck_type = st.text_input("Truck Type", placeholder="e.g., Tipper")
    equipment_make = st.text_input("Equipment Make", placeholder="e.g., Scania")
    site_location = st.text_input("Site Location", placeholder="e.g., Main Quarry")
    trips_covered = st.number_input("Trips Covered", min_value=0, step=1)

    submitted = st.form_submit_button("Add Operation Log")

if submitted:
    if not all([truck_type, equipment_make, site_location]):
        st.warning("Please fill out all required fields.")
    else:
        # Prepare data payload for the API
        payload = {
            "operation_date": operation_date.strftime("%Y-%m-%d"),
            "truck_type": truck_type,
            "equipment_make": equipment_make,
            "site_location": site_location,
            "trips_covered": trips_covered,
            # Add other fields from your DailyOperation model as needed
            "number_of_trucks": 1, # Example default
        }
        headers = {'X-API-Key': API_KEY, 'Content-Type': 'application/json'}
        try:
            response = requests.post(f"{FLASK_API_URL}/api/v1/operations", headers=headers, json=payload)
            response.raise_for_status()
            st.success(f"✅ Operation logged successfully! (ID: {response.json().get('id')})")
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to submit data to API: {e}")
            if e.response:
                st.error(f"API Response: {e.response.text}")

st.markdown("---")

# --- Display Data and Download Option ---
st.header("Operations Log")

# Load existing data from the API
df = get_operations_data(period="monthly")

if not df.empty:
    st.dataframe(df, use_container_width=True)
    excel_data = to_excel(df)
    st.download_button(label="📥 Download Data as Excel", data=excel_data, file_name="truck_logistics_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.info("No operations have been logged yet. Use the form above to add a new entry.")