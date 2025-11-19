from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.Enum('senior', 'caregiver', 'family'), nullable=False)
    phone = db.Column(db.String(20))
    caregiver_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    reminder_type = db.Column(db.Enum('medication', 'appointment', 'general'), nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    is_taken = db.Column(db.Boolean, default=False)
    notified = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HealthLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bp_systolic = db.Column(db.Integer)
    bp_diastolic = db.Column(db.Integer)
    sugar_level = db.Column(db.Float)
    weight = db.Column(db.Float)
    heart_rate = db.Column(db.Integer)
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    doctor_name = db.Column(db.String(255))
    appointment_time = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.Enum('scheduled', 'completed', 'cancelled'), default='scheduled')
    notified = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EmergencyLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    emergency_type = db.Column(db.String(100))
    message = db.Column(db.Text)
    alerted_users = db.Column(db.Text)  # JSON string of user IDs
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    status = db.Column(db.Enum('active', 'resolved'), default='active')
    triggered_at = db.Column(db.DateTime, default=datetime.now)

class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date)
    event_time = db.Column(db.Time)
    notified = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Define relationships after all classes to avoid forward reference issues
User.reminders = db.relationship('Reminder', backref='user', lazy=True, foreign_keys=[Reminder.user_id])
User.health_logs = db.relationship('HealthLog', backref='user', lazy=True)
User.appointments = db.relationship('Appointment', backref='user', lazy=True, foreign_keys=[Appointment.user_id])
User.emergency_logs = db.relationship('EmergencyLog', backref='user', lazy=True)
User.calendar_events = db.relationship('CalendarEvent', backref='user', lazy=True, foreign_keys=[CalendarEvent.user_id])
