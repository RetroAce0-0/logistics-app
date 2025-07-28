import streamlit as st
import pandas as pd
import os
from datetime import date
import io

# --- Page Configuration ---
st.set_page_config(
    page_title="Truck Logistics Dashboard",
    page_icon="🚚",
    layout="wide",
)

# --- Data Storage Configuration ---
DATA_FILE = "daily_truck_operations.csv"

# --- Helper Functions ---

def load_data():
    """Load data from CSV file. If file doesn't exist, create an empty DataFrame."""
    if os.path.exists(DATA_FILE):
        try:
            return pd.read_csv(DATA_FILE)
        except pd.errors.EmptyDataError:
            # If the file is empty, return an empty DataFrame with correct columns
            return pd.DataFrame(columns=["Date", "Truck ID", "Driver Name", "Origin", "Destination", "Cargo", "Status"])
    else:
        # If the file doesn't exist, create it with headers
        df = pd.DataFrame(columns=["Date", "Truck ID", "Driver Name", "Origin", "Destination", "Cargo", "Status"])
        df.to_csv(DATA_FILE, index=False)
        return df

def to_excel(df: pd.DataFrame):
    """Converts a DataFrame to an Excel file in memory."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='LogisticsData')
    processed_data = output.getvalue()
    return processed_data

# --- Securely Access API Key (Example) ---
def get_api_service():
    """
    Placeholder function to demonstrate secure API key usage.
    This function would initialize a client for a service like Google Maps or Google Sheets.
    """
    try:
        # This is the secure way to access your key from secrets.toml
        api_key = st.secrets["google_api"]["key"]
        
        # Here you would initialize your service, e.g., googlemaps.Client(key=api_key)
        # For this example, we'll just return a success message.
        st.sidebar.success("API Key loaded successfully!")
        # return initialized_service_client
    except KeyError:
        st.sidebar.error("API Key not found. Please add it to your .streamlit/secrets.toml file.")
        return None

# --- Main Application UI ---

st.title("🚚 Daily Truck Logistics Operations")
st.markdown("---")

# Initialize API Service (demonstration)
get_api_service()

# Load existing data
df = load_data()

# --- Input Form for New Entry ---
st.header("Add New Operation")
with st.form("new_operation_form", clear_on_submit=True):
    # Use columns for a cleaner layout
    col1, col2 = st.columns(2)
    with col1:
        operation_date = st.date_input("Date", value=date.today())
        truck_id = st.text_input("Truck ID", placeholder="e.g., TRUCK-001")
        driver_name = st.text_input("Driver Name", placeholder="e.g., John Doe")
        status = st.selectbox("Status", ["Scheduled", "In Transit", "Delivered", "Delayed"], index=0)
    with col2:
        origin = st.text_input("Origin", placeholder="e.g., New York, NY")
        destination = st.text_input("Destination", placeholder="e.g., Los Angeles, CA")
        cargo = st.text_area("Cargo Description", placeholder="e.g., 20 pallets of electronics")

    submitted = st.form_submit_button("Add Operation Log")

if submitted:
    if not all([truck_id, driver_name, origin, destination, cargo]):
        st.warning("Please fill out all fields before submitting.")
    else:
        new_entry = pd.DataFrame([{
            "Date": operation_date.strftime("%Y-%m-%d"),
            "Truck ID": truck_id,
            "Driver Name": driver_name,
            "Origin": origin,
            "Destination": destination,
            "Cargo": cargo,
            "Status": status
        }])
        
        # Append new entry to the existing data
        updated_df = pd.concat([df, new_entry], ignore_index=True)
        updated_df.to_csv(DATA_FILE, index=False)
        st.success("✅ Operation logged successfully!")
        # Rerun to show the updated table immediately
        st.experimental_rerun()

st.markdown("---")

# --- Display Data and Download Option ---
st.header("Operations Log")

if not df.empty:
    st.dataframe(df, use_container_width=True)
    excel_data = to_excel(df)
    st.download_button(label="📥 Download Data as Excel", data=excel_data, file_name="truck_logistics_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.info("No operations have been logged yet. Use the form above to add a new entry.")