from sqlalchemy import Column, Integer, String, Date, Time, Numeric, Boolean, Text
from sqlalchemy.orm import declarative_base
from flask_sqlalchemy import SQLAlchemy # Keep for db object

db = SQLAlchemy()
Base = declarative_base()

class DailyOperation(db.Model, Base):
    __tablename__ = 'daily_operation'

    id = Column(Integer, primary_key=True)
    
    # Core Info
    truck_type = Column(String(50), nullable=False)
    number_of_trucks = Column(Integer, nullable=False)
    equipment_make = Column(String(100), nullable=False)
    site_location = Column(String(100), nullable=False)
    person_type = Column(String(50), nullable=True) # 'Driver' or 'Operator'
    person_name = Column(String(100), nullable=True)
    trips_covered = Column(Integer, nullable=True)
    operation_date = Column(Date, nullable=False)
    
    # Contract / Facilitator Info
    facilitator_name = Column(String(100), nullable=True)
    daily_commission_rate = Column(Numeric(12, 2), nullable=True)
    total_lease_rate = Column(Numeric(12, 2), nullable=True)
    expected_lease_days = Column(Integer, nullable=True)
    lease_start_date = Column(Date, nullable=True)
    lease_end_date = Column(Date, nullable=True)
    lease_payment_status = Column(String(50), nullable=True) # 'Completed' or 'Outstanding'

    # Daily Metrics
    sign_in = Column(Time, nullable=True)
    sign_out = Column(Time, nullable=True)
    fuel_amount = Column(Numeric(10, 2), nullable=True)
    minimum_daily_quota = Column(Integer, nullable=True)
    
    # Event Tracking
    had_breakdown = Column(Boolean, nullable=False, default=False)
    breakdown_explained = Column(Text, nullable=True)
    hours_lost = Column(Numeric(5, 2), nullable=True)
    had_rain = Column(Boolean, nullable=False, default=False)
    rain_hours_lost = Column(Numeric(5, 2), nullable=True)
    other_issues_no_rain = Column(Text, nullable=True)
    remarks = Column(Text, nullable=True)

# --- OLAP / Data Warehouse Models ---
# These tables are designed for fast analytical queries.
# They would be populated from the DailyOperation table periodically.

class DimDate(db.Model, Base):
    __tablename__ = 'dim_date'
    date_key = Column(Integer, primary_key=True) # e.g., 20231225
    full_date = Column(Date, nullable=False, unique=True)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    month_name = Column(String(20), nullable=False)
    day = Column(Integer, nullable=False)
    day_of_week = Column(String(20), nullable=False)
    week_of_year = Column(Integer, nullable=False)

class DimEquipment(db.Model, Base):
    __tablename__ = 'dim_equipment'
    equipment_key = Column(Integer, primary_key=True)
    truck_type = Column(String(50), nullable=False)
    equipment_make = Column(String(100), nullable=False)
    __table_args__ = (db.UniqueConstraint('truck_type', 'equipment_make', name='_truck_type_make_uc'),)

class DimSite(db.Model, Base):
    __tablename__ = 'dim_site'
    site_key = Column(Integer, primary_key=True)
    site_location = Column(String(100), nullable=False, unique=True)

class DimFacilitator(db.Model, Base):
    __tablename__ = 'dim_facilitator'
    facilitator_key = Column(Integer, primary_key=True)
    facilitator_name = Column(String(100), nullable=False, unique=True)

class FactOperations(db.Model, Base):
    __tablename__ = 'fact_operations'
    id = Column(Integer, primary_key=True)
    
    # Foreign keys to dimension tables
    date_key = Column(Integer, db.ForeignKey('dim_date.date_key'), nullable=False)
    equipment_key = Column(Integer, db.ForeignKey('dim_equipment.equipment_key'), nullable=False)
    site_key = Column(Integer, db.ForeignKey('dim_site.site_key'), nullable=False)
    facilitator_key = Column(Integer, db.ForeignKey('dim_facilitator.facilitator_key'), nullable=True)

    # Measures (the numbers we want to analyze)
    number_of_trucks = Column(Integer, nullable=False)
    trips_covered = Column(Integer)
    fuel_amount = Column(Numeric(10, 2))
    hours_lost_breakdown = Column(Numeric(5, 2))
    hours_lost_rain = Column(Numeric(5, 2))
    total_lease_rate = Column(Numeric(12, 2))
    daily_commission = Column(Numeric(12, 2))
    
    # Link back to the original record for drill-through
    source_operation_id = Column(Integer, db.ForeignKey('daily_operation.id'))
