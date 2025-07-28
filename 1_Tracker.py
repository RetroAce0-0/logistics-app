import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import date, timedelta
import pandas as pd
import os

# Import your OLAP database models
from models import FactOperations, DimDate, DimEquipment, DimFacilitator, DimSite

# --- DATABASE SETUP ---
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/truck_logistics')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Analytics Dashboard", page_icon="📊", layout="wide")

st.title("📊 Analytics Dashboard")
st.write("Analyze operational data using pivots and charts. Use the sidebar to filter.")

# --- DATA LOADING ---
@st.cache_data(ttl=600) # Cache data for 10 minutes
def load_data():
    """Loads data from the OLAP tables for analysis."""
    db_session = SessionLocal()
    try:
        # This query joins all dimensions with the fact table
        query = db_session.query(
            FactOperations.number_of_trucks,
            FactOperations.trips_covered,
            FactOperations.fuel_amount,
            FactOperations.hours_lost_breakdown,
            FactOperations.hours_lost_rain,
            DimDate.full_date,
            DimDate.year,
            DimDate.quarter,
            DimDate.month_name,
            DimDate.week_of_year,
            DimEquipment.truck_type,
            DimEquipment.equipment_make,
            DimFacilitator.facilitator_name,
            DimSite.site_location
        ).join(DimDate, FactOperations.date_key == DimDate.date_key)\
         .join(DimEquipment, FactOperations.equipment_key == FactOperations.equipment_key)\
         .join(DimSite, FactOperations.site_key == DimSite.site_key)\
         .outerjoin(DimFacilitator, FactOperations.facilitator_key == DimFacilitator.facilitator_key)
        
        df = pd.read_sql(query.statement, db_session.bind)
        df['full_date'] = pd.to_datetime(df['full_date'])
        # Create a unique Truck ID for grouping, aligning trucks with the same make and type
        df['truck_id'] = df['equipment_make'] + ' - ' + df['truck_type']
        return df
    except Exception as e:
        st.error(f"Could not load data from the database. Have you run the 'populate-olap' command? Error: {e}")
        return pd.DataFrame()
    finally:
        db_session.close()

df = load_data()

if df.empty:
    st.warning("No data available for analysis. Please add entries and run the 'flask populate-olap' command.")
else:
    # --- SIDEBAR CONTROLS ---
    st.sidebar.header("Dashboard Filters")

    # Date Range
    min_date = df['full_date'].min().date()
    max_date = df['full_date'].max().date()
    start_date, end_date = st.sidebar.date_input(
        "Select Date Range",
        value=(max_date - timedelta(days=90), max_date),
        min_value=min_date,
        max_value=max_date
    )

    if start_date > end_date:
        st.sidebar.error("Error: End date must be after start date.")
        st.stop()

    # Filter data based on date range
    mask = (df['full_date'].dt.date >= start_date) & (df['full_date'].dt.date <= end_date)
    filtered_df = df.loc[mask].copy()

    if filtered_df.empty:
        st.warning("No data available for the selected date range.")
        st.stop()

    # --- PIVOT TABLE AND DASHBOARD ---
    st.sidebar.header("Pivot Table Controls")
    agg_level = st.sidebar.selectbox("Aggregate Data By", ['Weekly', 'Monthly', 'Quarterly', 'Yearly'])
    metrics = {
        'Total Trips Covered': 'trips_covered', 'Total Fuel (Litres)': 'fuel_amount',
        'Total Breakdown Hours': 'hours_lost_breakdown', 'Total Trucks Deployed': 'number_of_trucks'
    }
    selected_metric_label = st.sidebar.selectbox("Select Metric to Analyze", list(metrics.keys()))
    selected_metric = metrics[selected_metric_label]

    agg_map = {'Weekly': 'W-MON', 'Monthly': 'M', 'Quarterly': 'Q', 'Yearly': 'Y'}
    pivot_table = pd.pivot_table(
        filtered_df, values=selected_metric, index=pd.Grouper(key='full_date', freq=agg_map[agg_level]),
        columns='truck_id', aggfunc='sum'
    ).fillna(0)
    pivot_table.index = pivot_table.index.to_period(agg_map[agg_level]).astype(str)

    st.header(f"Pivot Table: {selected_metric_label} by Truck ID ({agg_level})")
    st.write("This table shows the performance of each truck type over the selected period.")
    st.dataframe(pivot_table.style.format("{:,.2f}").background_gradient(cmap='viridis'))

    st.header(f"Chart: {selected_metric_label} Over Time ({agg_level})")
    st.write("This chart visualizes the total performance across all trucks for each period.")
    chart_data = pivot_table.sum(axis=1)
    st.bar_chart(chart_data)

    st.header("Raw Data for Selected Period")
    st.write("The raw data below is used for the calculations above.")
    st.dataframe(filtered_df[['full_date', 'truck_id', 'facilitator_name', 'site_location', 'trips_covered', 'fuel_amount', 'hours_lost_breakdown']].reset_index(drop=True))