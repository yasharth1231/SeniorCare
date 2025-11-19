from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, DateTimeField, IntegerField, FloatField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('senior', 'Senior Citizen'), ('caregiver', 'Caregiver'), ('family', 'Family Member')], validators=[Optional()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('senior', 'Senior Citizen'), ('caregiver', 'Caregiver'), ('family', 'Family Member')], validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    submit = SubmitField('Register')

class ReminderForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    reminder_type = SelectField('Type', choices=[('medication', 'Medication'), ('appointment', 'Appointment'), ('general', 'General')])
    date = StringField('Date', validators=[DataRequired()])
    event_time = StringField('Time (HH:MM)', validators=[DataRequired()])
    submit = SubmitField('Add Reminder')

class HealthLogForm(FlaskForm):
    bp_systolic = IntegerField('Systolic BP', validators=[Optional()])
    bp_diastolic = IntegerField('Diastolic BP', validators=[Optional()])
    sugar_level = FloatField('Sugar Level', validators=[Optional()])
    weight = FloatField('Weight (kg)', validators=[Optional()])
    heart_rate = IntegerField('Heart Rate', validators=[Optional()])
    submit = SubmitField('Log Health Data')

class AppointmentForm(FlaskForm):
    doctor_name = StringField('Doctor Name', validators=[DataRequired()])
    date = StringField('Date', validators=[DataRequired()])
    event_time = StringField('Time (HH:MM)', validators=[DataRequired()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Schedule Appointment')

class AddUserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Add User')

class CalendarEventForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    event_date = StringField('Event Date', validators=[DataRequired()])  # Use date picker in JS
    event_time = StringField('Event Time', validators=[Optional()])
    submit = SubmitField('Add Event')
