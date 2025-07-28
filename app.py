import io
from datetime import date, datetime, timedelta

from functools import wraps
import pandas as pd
from dateutil.relativedelta import relativedelta
from flask import Flask, Response, jsonify, request, render_template, flash, redirect, url_for
from models import db, DailyOperation, DimDate, DimEquipment, DimSite, DimFacilitator, FactOperations
from sqlalchemy.exc import SQLAlchemyError
from forms import DailyEntryForm

app = Flask(__name__)

# --- API Authentication Decorator ---
def require_api_key(f):
    """Decorator to protect API endpoints with a key."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for the API key in the request headers
        api_key = request.headers.get('X-API-Key')
        # Compare with the key stored in the app's config
        if not api_key or api_key != app.config['INTERNAL_API_KEY']:
            app.logger.warning(f"Unauthorized API access attempt from IP: {request.remote_addr}")
            return jsonify({"error": "Unauthorized. Invalid or missing API key."}), 401
        return f(*args, **kwargs)
    return decorated_function


# Load configuration from the config.py file
app.config.from_object('config.Config')
db.init_app(app)

@app.cli.command('init-db')
def init_db_command():
    """Creates the database tables."""
    with app.app_context():
        db.create_all()
    print('Initialized the database.')

@app.cli.command('populate-olap')
def populate_olap_command():
    """Populates the OLAP dimension and fact tables from the daily operations."""
    print("Starting OLAP data population...")
    
    # A more robust solution would track processed IDs, but for this example, we'll check existence.
    operations = DailyOperation.query.all()
    
    with db.session.no_autoflush:
        for op in operations:
            # Check if a fact record for this operation already exists
            fact_exists = FactOperations.query.filter_by(source_operation_id=op.id).first()
            if fact_exists:
                continue

            # 1. Get or Create Date Dimension
            date_dim = DimDate.query.filter_by(full_date=op.operation_date).first()
            if not date_dim:
                dt = op.operation_date
                date_dim = DimDate(
                    date_key=int(dt.strftime('%Y%m%d')),
                    full_date=dt, year=dt.year, quarter=(dt.month - 1) // 3 + 1,
                    month=dt.month, month_name=dt.strftime('%B'), day=dt.day,
                    day_of_week=dt.strftime('%A'), week_of_year=dt.isocalendar()[1]
                )
                db.session.add(date_dim)
                db.session.flush()

            # 2. Get or Create Equipment Dimension
            equip_dim = DimEquipment.query.filter_by(truck_type=op.truck_type, equipment_make=op.equipment_make).first()
            if not equip_dim:
                equip_dim = DimEquipment(truck_type=op.truck_type, equipment_make=op.equipment_make)
                db.session.add(equip_dim)
                db.session.flush()

            # 3. Get or Create Site Dimension
            site_dim = DimSite.query.filter_by(site_location=op.site_location).first()
            if not site_dim:
                site_dim = DimSite(site_location=op.site_location)
                db.session.add(site_dim)
                db.session.flush()

            # 4. Get or Create Facilitator Dimension
            facilitator_dim = None
            if op.facilitator_name:
                facilitator_dim = DimFacilitator.query.filter_by(facilitator_name=op.facilitator_name).first()
                if not facilitator_dim:
                    facilitator_dim = DimFacilitator(facilitator_name=op.facilitator_name)
                    db.session.add(facilitator_dim)
                    db.session.flush()

            # 5. Create Fact Record
            fact = FactOperations(
                date_key=date_dim.date_key, equipment_key=equip_dim.equipment_key,
                site_key=site_dim.site_key, facilitator_key=facilitator_dim.facilitator_key if facilitator_dim else None,
                number_of_trucks=op.number_of_trucks, trips_covered=op.trips_covered, fuel_amount=op.fuel_amount,
                hours_lost_breakdown=op.hours_lost, hours_lost_rain=op.rain_hours_lost,
                total_lease_rate=op.total_lease_rate, daily_commission=op.daily_commission_rate,
                source_operation_id=op.id
            )
            db.session.add(fact)
    try:
        db.session.commit()
        print("OLAP tables populated successfully.")
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"An error occurred: {e}")

def get_quarter_start(dt):
    """Calculates the start date of the quarter for a given date."""
    return date(dt.year, 3 * ((dt.month - 1) // 3) + 1, 1)

@app.route('/', methods=['GET', 'POST'])
def entry():
    """Serves the main data entry form."""
    form = DailyEntryForm()
    if form.validate_on_submit():
        try:
            # Handle conditional breakdown data
            breakdown_explained_data = form.breakdown_explained.data if form.had_breakdown.data == 'Yes' else None
            hours_lost_data = form.hours_lost.data if form.had_breakdown.data == 'Yes' else None

            # Handle conditional rain data
            rain_hours_lost_data = form.rain_hours_lost.data if form.had_rain.data == 'Yes' else None
            other_issues_data = form.other_issues_no_rain.data if form.had_rain.data == 'No' else None

            new_entry = DailyOperation(
                truck_type=form.truck_type.data,
                number_of_trucks=form.number_of_trucks.data,
                equipment_make=form.equipment_make.data,
                site_location=form.site_location.data,
                person_type=form.person_type.data,
                person_name=form.person_name.data,
                trips_covered=form.trips_covered.data,
                operation_date=form.operation_date.data,
                facilitator_name=form.facilitator_name.data,
                daily_commission_rate=form.daily_commission_rate.data,
                total_lease_rate=form.total_lease_rate.data,
                expected_lease_days=form.expected_lease_days.data,
                lease_start_date=form.lease_start_date.data,
                lease_end_date=form.lease_end_date.data,
                lease_payment_status=form.lease_payment_status.data,
                sign_in=form.sign_in.data,
                sign_out=form.sign_out.data,
                fuel_amount=form.fuel_amount.data,
                minimum_daily_quota=form.minimum_daily_quota.data,
                had_breakdown=(form.had_breakdown.data == 'Yes'),
                breakdown_explained=breakdown_explained_data,
                hours_lost=hours_lost_data,
                had_rain=(form.had_rain.data == 'Yes'),
                rain_hours_lost=rain_hours_lost_data,
                other_issues_no_rain=other_issues_data,
                remarks=form.remarks.data
            )
            db.session.add(new_entry)
            db.session.commit()
            flash('Daily entry saved successfully!', 'success')
            return redirect(url_for('entry'))
        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error(f"Database error on form submission: {e}")
            flash('A database error occurred while saving the entry. Please try again.', 'danger')
    return render_template('form.html', form=form)

@app.route('/tracker')
def tracker():
    """Serves the contract tracker page."""
    from sqlalchemy import func

    # --- Example 1: Original view of contracts (distinct facilitators) ---
    # This still queries the OLTP table for operational data.
    contracts = db.session.query(DailyOperation).distinct(DailyOperation.facilitator_name).order_by(DailyOperation.facilitator_name, DailyOperation.operation_date.desc()).all()

    # --- Example 2: New OLAP-style query ---
    # Get total trips and fuel usage per equipment type for the last 90 days.
    ninety_days_ago = date.today() - timedelta(days=90)
    start_date_key = int(ninety_days_ago.strftime('%Y%m%d'))

    analytics_data = db.session.query(
        DimEquipment.truck_type,
        DimEquipment.equipment_make,
        func.sum(FactOperations.trips_covered).label('total_trips'),
        func.sum(FactOperations.fuel_amount).label('total_fuel')
    ).join(FactOperations, DimEquipment.equipment_key == FactOperations.equipment_key)\
     .join(DimDate, FactOperations.date_key == DimDate.date_key)\
     .filter(DimDate.date_key >= start_date_key)\
     .group_by(DimEquipment.truck_type, DimEquipment.equipment_make)\
     .order_by(DimEquipment.truck_type, func.sum(FactOperations.trips_covered).desc())\
     .all()
    return render_template('tracker.html', contracts=contracts, today=date.today(), analytics_data=analytics_data)

@app.route('/api/v1/operations', methods=['POST'])
@require_api_key
def create_operation():
    """
    API endpoint to create a new daily operation entry.
    Expects a JSON payload with the operation data.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    # Basic validation
    required_fields = ['truck_type', 'equipment_make', 'site_location', 'operation_date']
    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing required fields: {required_fields}"}), 400

    try:
        # Convert date strings to date objects
        for date_field in ['operation_date', 'lease_start_date', 'lease_end_date']:
            if data.get(date_field):
                data[date_field] = datetime.strptime(data[date_field], '%Y-%m-%d').date()

        new_entry = DailyOperation(**data)
        db.session.add(new_entry)
        db.session.commit()
        return jsonify({"message": "Operation created successfully", "id": new_entry.id}), 201
    except (SQLAlchemyError, TypeError, ValueError) as e:
        db.session.rollback()
        app.logger.error(f"Error creating operation: {e}")
        return jsonify({"error": "Failed to create operation.", "details": str(e)}), 500

@app.route('/api/v1/export', methods=['GET'])
@require_api_key
def export_data():
    """
    API endpoint to export data as CSV.
    Query Parameters:
    - period: 'weekly', 'monthly', 'quarterly'
    - start_date: 'YYYY-MM-DD' (used with end_date)
    - end_date: 'YYYY-MM-DD' (used with start_date)
    """
    today = date.today()
    period = request.args.get('period')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    start_date, end_date = None, None

    if period:
        if period == 'weekly':
            start_date = today - timedelta(days=6)
            end_date = today
        elif period == 'monthly':
            start_date = today.replace(day=1)
            end_date = today
        elif period == 'quarterly':
            start_date = get_quarter_start(today)
            end_date = today
        else:
            return jsonify({"error": "Invalid period. Use 'weekly', 'monthly', or 'quarterly'."}), 400
    elif start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
    else:
        return jsonify({"error": "Please provide a 'period' or both 'start_date' and 'end_date'."}), 400

    try:
        query = DailyOperation.query.filter(
            DailyOperation.operation_date.between(start_date, end_date)
        )
        
        # Use pandas to read directly from the SQLAlchemy query
        df = pd.read_sql(query.statement, db.session.bind)

        if df.empty:
            return jsonify({"message": "No data found for the selected period."}), 404

        # Create an in-memory text buffer
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        
        # Seek to the start of the buffer
        buffer.seek(0)

        return Response(
            buffer,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=logistics_data_{start_date}_to_{end_date}.csv"}
        )

    except SQLAlchemyError as e:
        app.logger.error(f"Database error during export: {e}")
        return jsonify({"error": "A database error occurred."}), 500

if __name__ == '__main__':
    app.run(debug=True)