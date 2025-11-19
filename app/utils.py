from twilio.rest import Client
from flask import current_app
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from datetime import datetime, timedelta

def send_alert(user_id, message):
    # Send SMS alert using Twilio (if configured)
    try:
        if current_app.config.get('TWILIO_ACCOUNT_SID'):
            client = Client(current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN'])
            # Assume user has phone, send to caregiver/family
            from app.models import User
            user = User.query.get(user_id)
            if user and user.phone:
                client.messages.create(
                    body=message,
                    from_=current_app.config['TWILIO_PHONE_NUMBER'],
                    to=user.phone
                )
    except Exception as e:
        # Log the error, but don't raise to avoid breaking SOS
        print(f"Failed to send SMS alert: {e}")

def process_voice_query(query, user):
    query = query.lower()
    response = ""

    if 'reminder' in query or 'medicine' in query:
        response = "You have pending reminders. Please check your dashboard."
    elif 'health' in query:
        response = "Your last health log shows normal vitals. Log new data if needed."
    elif 'appointment' in query:
        response = "Your next appointment is scheduled. Check appointments page."
    elif 'sos' in query:
        response = "SOS activated. Help is on the way."
        # Trigger SOS logic if needed
    elif 'calendar' in query or 'event' in query:
        response = "Check your calendar for upcoming events."
    else:
        response = "I'm sorry, I didn't understand. Try asking about reminders, health, appointments, or calendar."

    return response

def classify_health_status(user_id):
    from app.models import HealthLog, Reminder, Appointment
    from app import db

    # Fetch recent health logs (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    health_logs = HealthLog.query.filter_by(user_id=user_id).filter(HealthLog.logged_at >= thirty_days_ago).all()

    if not health_logs:
        return "No Data", "Insufficient health data for classification."

    # Prepare data for classification
    data = []
    for log in health_logs:
        data.append({
            'bp_systolic': log.bp_systolic or 120,
            'bp_diastolic': log.bp_diastolic or 80,
            'sugar_level': log.sugar_level or 100,
            'weight': log.weight or 70,
            'heart_rate': log.heart_rate or 70
        })

    df = pd.DataFrame(data)

    # Define thresholds for health status based on provided ranges
    # Healthy: BP <120/80, Sugar <140, Heart Rate 60-100
    # At Risk: BP 130-139/80-89, Sugar 140-199, Heart Rate slightly <60 or >100
    # Needs Attention: BP ≥140/90, Sugar ≥200, Heart Rate <60 or >100 (abnormal or persistent)

    def classify_row(row):
        # Check for Needs Attention first (most severe)
        if (row['bp_systolic'] >= 140 or row['bp_diastolic'] >= 90 or
            row['sugar_level'] >= 200 or row['heart_rate'] < 60 or row['heart_rate'] > 100):
            return 'Needs Attention'
        # Check for At Risk
        elif ((130 <= row['bp_systolic'] <= 139 and 80 <= row['bp_diastolic'] <= 89) or
              (140 <= row['sugar_level'] <= 199) or
              (row['heart_rate'] < 60 or row['heart_rate'] > 100)):
            return 'At Risk'
        # Otherwise Healthy
        elif (row['bp_systolic'] < 120 and row['bp_diastolic'] < 80 and
              row['sugar_level'] < 140 and 60 <= row['heart_rate'] <= 100):
            return 'Healthy'
        else:
            return 'At Risk'  # Default to At Risk if doesn't fit other categories

    df['status'] = df.apply(classify_row, axis=1)

    # Get the most recent status
    latest_status = df.iloc[-1]['status']

    # Get latest values (most recent log)
    latest_bp_sys = df.iloc[-1]['bp_systolic']
    latest_bp_dia = df.iloc[-1]['bp_diastolic']
    latest_sugar = df.iloc[-1]['sugar_level']
    latest_weight = df.iloc[-1]['weight']
    latest_hr = df.iloc[-1]['heart_rate']

    # Calculate average metrics
    avg_bp_sys = df['bp_systolic'].mean()
    avg_bp_dia = df['bp_diastolic'].mean()
    avg_sugar = df['sugar_level'].mean()
    avg_weight = df['weight'].mean()
    avg_hr = df['heart_rate'].mean()

    return latest_status, {
        'latest_bp_systolic': round(latest_bp_sys, 1),
        'latest_bp_diastolic': round(latest_bp_dia, 1),
        'latest_sugar_level': round(latest_sugar, 1),
        'latest_weight': round(latest_weight, 1),
        'latest_heart_rate': round(latest_hr, 1),
        'avg_bp_systolic': round(avg_bp_sys, 1),
        'avg_bp_diastolic': round(avg_bp_dia, 1),
        'avg_sugar_level': round(avg_sugar, 1),
        'avg_weight': round(avg_weight, 1),
        'avg_heart_rate': round(avg_hr, 1)
    }

def rank_tasks(user_id):
    from app.models import Reminder, Appointment, CalendarEvent
    from app import db

    tasks = []

    # Get upcoming reminders
    now = datetime.now()
    reminders = Reminder.query.filter_by(user_id=user_id).filter(Reminder.scheduled_time > now).all()
    for r in reminders:
        urgency = 1 if r.reminder_type == 'medication' else 0.5
        time_diff = (r.scheduled_time - now).total_seconds() / 3600  # hours
        priority = urgency / max(time_diff, 1)  # Higher priority for urgent and soon tasks
        tasks.append({
            'type': 'reminder',
            'title': r.title,
            'scheduled_time': r.scheduled_time,
            'priority': priority,
            'urgency': 'urgent' if r.reminder_type == 'medication' else 'normal'
        })

    # Get upcoming appointments
    appointments = Appointment.query.filter_by(user_id=user_id).filter(Appointment.appointment_time > now).all()
    for a in appointments:
        time_diff = (a.appointment_time - now).total_seconds() / 3600
        priority = 0.8 / max(time_diff, 1)
        tasks.append({
            'type': 'appointment',
            'title': f"Appointment with {a.doctor_name}",
            'scheduled_time': a.appointment_time,
            'priority': priority,
            'urgency': 'normal'
        })

    # Get upcoming calendar events
    events = CalendarEvent.query.filter_by(user_id=user_id).filter(CalendarEvent.event_date >= now.date()).all()
    for e in events:
        event_datetime = datetime.combine(e.event_date, e.event_time or time(9, 0))
        if event_datetime > now:
            time_diff = (event_datetime - now).total_seconds() / 3600
            priority = 0.3 / max(time_diff, 1)
            tasks.append({
                'type': 'event',
                'title': e.title,
                'scheduled_time': event_datetime,
                'priority': priority,
                'urgency': 'normal'
            })

    # Sort by priority (higher first)
    tasks.sort(key=lambda x: x['priority'], reverse=True)

    return tasks[:10]  # Top 10 tasks
