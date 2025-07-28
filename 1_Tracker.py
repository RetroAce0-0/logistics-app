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
        # Get the most recent entry for each facilitator to represent the contract
        contracts_df = df.sort_values('operation_date', ascending=False).drop_duplicates('facilitator_name')
        
        # Calculate days remaining
        contracts_df['lease_end_date'] = pd.to_datetime(contracts_df['lease_end_date']).dt.date
        contracts_df['days_remaining'] = (contracts_df['lease_end_date'] - date.today()).dt.days
        
        # Select and rename columns for display
        display_df = contracts_df[[
            'facilitator_name', 'lease_start_date', 'lease_end_date', 
            'days_remaining', 'total_lease_rate', 'lease_payment_status', 'site_location'
        ]].rename(columns={'facilitator_name': 'Facilitator', 'lease_start_date': 'Start Date', 'lease_end_date': 'End Date', 'days_remaining': 'Days Remaining', 'total_lease_rate': 'Lease Rate (₦)', 'lease_payment_status': 'Status', 'site_location': 'Location'})

        st.dataframe(display_df)

except Exception as e:
    st.error(f"Could not load tracker data. Please check the database connection. Error: {e}")