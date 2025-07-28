from flask_wtf import FlaskForm
from wtforms import (SelectField, DateField, TimeField, DecimalField, TextAreaField, 
                     IntegerField, StringField, RadioField)
from wtforms.validators import DataRequired, Optional, NumberRange, InputRequired, Length

NIGERIAN_STATES = [
    'Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Bayelsa', 'Benue',
    'Borno', 'Cross River', 'Delta', 'Ebonyi', 'Edo', 'Ekiti', 'Enugu', 'Gombe',
    'Imo', 'Jigawa', 'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Kogi', 'Kwara',
    'Lagos', 'Nasarawa', 'Niger', 'Ogun', 'Ondo', 'Osun', 'Oyo', 'Plateau', 
    'Rivers', 'Sokoto', 'Taraba', 'Yobe', 'Zamfara', 'Federal Capital Territory'
]

NIGERIAN_STATES_CHOICES = [('', '-- Select a State --')] + sorted([(s, s) for s in NIGERIAN_STATES])

class DailyEntryForm(FlaskForm):
    truck_type = SelectField(
        'Truck Type',
        choices=[
            ('', '-- Select a Type --'), # Add a placeholder
            ('truck', 'Truck'),
            ('dump-truck', 'Dump-Truck'),
            ('bulldozer', 'Bulldozer')
        ],
        validators=[DataRequired(message="Please select a truck type.")]
    )
    equipment_make = SelectField(
        'Make of Equipment',
        choices=[
            ('', '-- Select a Make --'),
            ('Caterpillar', 'Caterpillar'),
            ('Komatsu', 'Komatsu'),
            ('Sandvik', 'Sandvik'),
            ('Liebherr', 'Liebherr'),
            ('Epiroc', 'Epiroc'),
            ('Volvo', 'Volvo')
        ],
        validators=[DataRequired(message="Please select the equipment make.")]
    )
    site_location = SelectField('Mining Site Location (State)', choices=NIGERIAN_STATES_CHOICES, validators=[DataRequired()])
    number_of_trucks = IntegerField('Number of Units', default=1, validators=[DataRequired(), NumberRange(min=1, message="Must be at least 1.")])
    person_type = RadioField('Personnel Type', choices=[('Driver', 'Driver'), ('Operator', 'Operator')], validators=[Optional()])
    person_name = StringField('Driver/Operator Name', validators=[Optional(), Length(max=100)])
    trips_covered = IntegerField('Trips Covered', default=0, validators=[Optional(), NumberRange(min=0)])
    operation_date = DateField('Operation Date', validators=[DataRequired()])
    
    # Contract Fields
    facilitator_name = StringField('Facilitator Name', validators=[Optional(), Length(max=100)])
    daily_commission_rate = DecimalField('Daily Commission Rate (Naira)', places=2, validators=[Optional()])
    total_lease_rate = DecimalField('Total Lease Rate (Naira)', places=2, validators=[Optional()])
    expected_lease_days = IntegerField('Expected Days Agreed Upon', validators=[Optional(), NumberRange(min=1)])
    lease_start_date = DateField('Lease Start Date', validators=[Optional()])
    lease_end_date = DateField('Lease End Date', validators=[Optional()])
    lease_payment_status = SelectField('Lease Payment Status', choices=[('', '-- Select --'), ('Outstanding', 'Outstanding'), ('Completed', 'Completed')], validators=[Optional()])

    sign_in = TimeField('Sign In', validators=[Optional()])
    sign_out = TimeField('Sign Out', validators=[Optional()])
    fuel_amount = DecimalField('Fuel Administered (Litres)', places=2, validators=[Optional()])
    minimum_daily_quota = IntegerField('Minimum Daily Quota (e.g., trips)', validators=[Optional(), NumberRange(min=0)])
    had_rain = RadioField(
        'Was the day affected by rain?',
        choices=[('No', 'No'), ('Yes', 'Yes')],
        default='No',
        validators=[InputRequired()]
    )
    had_breakdown = RadioField(
        'Was there a breakdown?',
        choices=[('No', 'No'), ('Yes', 'Yes')],
        default='No',
        validators=[InputRequired()]
    )
    breakdown_explained = TextAreaField('If yes, please explain the breakdown', validators=[Optional()])
    hours_lost = DecimalField('Hours Lost / Downtime', places=2, validators=[Optional(), NumberRange(min=0)])
    rain_hours_lost = DecimalField('If yes, how many hours were lost to rain?', places=2, validators=[Optional(), NumberRange(min=0)])
    other_issues_no_rain = TextAreaField('If no, were there any other issues?', validators=[Optional()])
    remarks = TextAreaField('Remarks')
