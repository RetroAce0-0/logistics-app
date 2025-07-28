import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import date
import pandas as pd
import os

# Import your existing database model
from models import DailyOperation

# --- DATABASE SETUP ---
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/truck_logistics')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Contract Tracker", page_icon="📊", layout="wide")

st.title("📊 Contract Tracker")
st.write("This page provides an overview of ongoing contracts for accountability.")

try:
    db_session = SessionLocal()
    # Use pandas to read data, which is more efficient for display
    query = db_session.query(DailyOperation).statement
    df = pd.read_sql(query, db_session.bind)
    db_session.close()

    if df.empty:
        st.warning("No contract data found. Please submit a daily entry first.")
    else:
        # Get the most recent entry for each facilitator to represent the contract status
        contracts_df = df.sort_values('operation_date', ascending=False).drop_duplicates('facilitator_name').copy()
        
        # --- Calculations for Display ---
        
        # 1. Days Remaining / Outstanding
        contracts_df['lease_end_date'] = pd.to_datetime(contracts_df['lease_end_date']).dt.date
        
        def calculate_days_remaining(end_date):
            if pd.notna(end_date):
                return (end_date - date.today()).days
            return None
            
        contracts_df['days_remaining'] = contracts_df['lease_end_date'].apply(calculate_days_remaining)

        # 2. Outstanding Payment Status
        contracts_df['Outstanding Payment?'] = contracts_df['lease_payment_status'].apply(
            lambda x: 'Yes' if x == 'Outstanding' else 'No'
        )

        # 3. Breakdown Hours (from most recent entry)
        contracts_df['breakdown_hours_last_report'] = contracts_df['hours_lost']
        
        # Select and rename columns for display
        display_df = contracts_df[[
            'facilitator_name', 'lease_start_date', 'lease_end_date', 
            'days_remaining', 'lease_payment_status', 'Outstanding Payment?',
            'total_lease_rate', 'breakdown_hours_last_report', 'site_location'
        ]].rename(columns={
            'facilitator_name': 'Facilitator', 'lease_start_date': 'Start Date', 
            'lease_end_date': 'End Date', 'days_remaining': 'Lease Days Remaining/Outstanding', 
            'lease_payment_status': 'Status', 'Outstanding Payment?': 'Payment Outstanding?',
            'total_lease_rate': 'Lease Rate (₦)', 'breakdown_hours_last_report': 'Breakdown Hours (Last Report)',
            'site_location': 'Location'
        })

        st.dataframe(display_df)
        st.info("💡 **Note:** 'Breakdown Hours' reflects the downtime reported on the most recent entry date for that contract, not the total for the entire lease period.")

except Exception as e:
    st.error(f"Could not load tracker data. Please check the database connection. Error: {e}")