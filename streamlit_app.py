import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import date, time
import os

# Import your existing database model
from models import DailyOperation

# --- DATABASE SETUP ---
# This uses the same environment variable as your Flask app
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/truck_logistics')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- UI CONFIGURATION ---
st.set_page_config(
    page_title="Logistics Logger",
    page_icon="🚚",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("🚚 Daily Logistics Entry")
st.write("Please fill out the form below to log today's operations.")

# --- FORM DEFINITION ---
NIGERIAN_STATES = [
    'Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Bayelsa', 'Benue', 
    'Borno', 'Cross River', 'Delta', 'Ebonyi', 'Edo', 'Ekiti', 'Enugu', 'Gombe', 
    'Imo', 'Jigawa', 'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Kogi', 'Kwara', 
    'Lagos', 'Nasarawa', 'Niger', 'Ogun', 'Ondo', 'Osun', 'Oyo', 'Plateau', 
    'Rivers', 'Sokoto', 'Taraba', 'Yobe', 'Zamfara', 'Federal Capital Territory'
]

with st.form("daily_entry_form"):
    st.header("Core Details")
    col1, col2 = st.columns(2)
    with col1:
        operation_date = st.date_input("Operation Date", value=date.today())
    with col2:
        site_location = st.selectbox("Mining Site Location (State)", options=[""] + sorted(NIGERIAN_STATES), index=0)

    st.header("Equipment & Personnel")
    col1, col2, col3 = st.columns(3)
    with col1:
        truck_type = st.selectbox("Truck Type", ["", "Truck", "Dump-Truck", "Bulldozer"])
    with col2:
        equipment_make_options = ["", "Caterpillar", "Komatsu", "Sandvik", "Liebherr", "Epiroc", "Volvo", "12 tire man diesel", "Jac", "Shantui", "Others"]
        equipment_make_selection = st.selectbox("Make of Equipment", options=sorted(equipment_make_options))
    with col3:
        number_of_trucks = st.number_input("Number of Units", min_value=1, value=1, step=1)
    
    # Conditionally display a text input if 'Others' is selected for equipment make
    equipment_make_final = equipment_make_selection
    if equipment_make_selection == 'Others':
        equipment_make_final = st.text_input("Please specify the make", max_chars=100)

    person_type = st.radio("Personnel Type", ["Driver", "Operator"], horizontal=True)
    person_name = st.text_input(f"{person_type} Name")

    st.header("Contract Information")
    facilitator_name = st.text_input("Facilitator Name")
    
    lease_payment_status = st.selectbox("Lease Payment Status", ["", "Completed", "Outstanding"])

    # --- Conditional Lease Details ---
    lease_start_date = None
    lease_end_date = None
    lease_period_days = 0

    if lease_payment_status == 'Outstanding':
        st.subheader("Outstanding Lease Details")
        col1, col2 = st.columns(2)
        with col1:
            lease_start_date = st.date_input("Lease Start Date", value=None)
        with col2:
            lease_end_date = st.date_input("Lease End Date", value=None)import streamlit as st
            import time
            
            # This function's result is cached
            @st.cache_data
            def get_long_running_data():
                # If you change this message, the app won't update
                # because the function is cached and won't be re-executed.
                message = "This is the original message from a slow function."
                time.sleep(3) # Simulates a slow data fetch
                return message
            
            st.write("Fetching data...")
            st.write(get_long_running_data())
            

        if lease_start_date and lease_end_date:
            if lease_end_date > lease_start_date:
                lease_period_days = (lease_end_date - lease_start_date).days
                st.info(f"Calculated Lease Period: **{lease_period_days} days**")
            else:
                st.error("Lease End Date must be after Lease Start Date.")

    st.subheader("Lease Rates")
    col1, col2 = st.columns(2)
    with col1:
        daily_commission_rate = st.number_input("Daily Commission Rate per Truck (Naira)", min_value=0.0, format="%.2f")
    with col2:
        # This remains the user's input for the total contract value
        total_lease_rate = st.number_input("Total Lease Rate (Naira)", min_value=0.0, format="%.2f")

    # --- Verification Logic ---
    if lease_payment_status == 'Outstanding' and lease_period_days > 0 and daily_commission_rate > 0:
        calculated_total_rate = daily_commission_rate * number_of_trucks * lease_period_days
        st.markdown("---")
        st.write("#### Rate Verification")
        st.metric(
            label=f"Calculated Total Lease (for {number_of_trucks} unit(s) over {lease_period_days} days)",
            value=f"₦{calculated_total_rate:,.2f}"
        )
        st.write(f"The value above is calculated for your reference. The 'Total Lease Rate' you entered above will be saved.")
        st.markdown("---")
    
    st.header("Daily Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        sign_in = st.time_input("Sign In", value=None)
    with col2:
        sign_out = st.time_input("Sign Out", value=None)
    with col3:
        trips_covered = st.number_input("Trips Covered", min_value=0, step=1)
    fuel_amount = st.number_input("Fuel Administered (Litres)", min_value=0.0, format="%.2f")

    st.header("Event Reporting")
    col1, col2 = st.columns(2)
    with col1:
        had_breakdown = st.radio("Was there a breakdown?", ["No", "Yes"], horizontal=True)
    with col2:
        had_rain = st.radio("Was the day affected by rain?", ["No", "Yes"], horizontal=True)

    if had_breakdown == 'Yes':
        breakdown_explained = st.text_area("If yes, please explain the breakdown")
        hours_lost = st.number_input("Hours Lost / Downtime", min_value=0.0, format="%.2f")
    else:
        breakdown_explained = None
        hours_lost = None

    if had_rain == 'Yes':
        rain_hours_lost = st.number_input("If yes, how many hours were lost to rain?", min_value=0.0, format="%.2f")
        other_issues_no_rain = None
    else:
        rain_hours_lost = None
        other_issues_no_rain = st.text_area("If no, were there any other issues?")

    remarks = st.text_area("General Remarks")

    # --- FORM SUBMISSION ---
    submitted = st.form_submit_button("Save Entry")
    if submitted:
        # Basic validation
        is_make_invalid = not equipment_make_selection or (equipment_make_selection == 'Others' and not equipment_make_final)
        if not site_location or not truck_type or is_make_invalid:
            st.error("Please fill out all required fields: Site Location, Truck Type, and Equipment Make.")
        else:
            db_session = SessionLocal()
            try:
                new_entry = DailyOperation(
                    operation_date=operation_date,
                    site_location=site_location,
                    truck_type=truck_type,
                    equipment_make=equipment_make_final,
                    number_of_trucks=number_of_trucks,
                    person_type=person_type,
                    person_name=person_name,
                    facilitator_name=facilitator_name,
                    total_lease_rate=total_lease_rate,
                    daily_commission_rate=daily_commission_rate,
                    lease_start_date=lease_start_date,
                    lease_end_date=lease_end_date,
                    lease_payment_status=lease_payment_status,
                    sign_in=sign_in,
                    sign_out=sign_out,
                    trips_covered=trips_covered,
                    fuel_amount=fuel_amount,
                    had_breakdown=(had_breakdown == 'Yes'),
                    breakdown_explained=breakdown_explained,
                    hours_lost=hours_lost,
                    had_rain=(had_rain == 'Yes'),
                    rain_hours_lost=rain_hours_lost,
                    other_issues_no_rain=other_issues_no_rain,
                    remarks=remarks
                )
                db_session.add(new_entry)
                db_session.commit()
                st.success("Daily entry saved successfully!")
            except SQLAlchemyError as e:
                db_session.rollback()
                st.error(f"A database error occurred: {e}")
            finally:
                db_session.close()