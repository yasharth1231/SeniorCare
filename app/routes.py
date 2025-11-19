from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Reminder, HealthLog, Appointment, EmergencyLog, CalendarEvent
from app.forms import ReminderForm, HealthLogForm, AppointmentForm, CalendarEventForm, RegistrationForm, AddUserForm
from app.utils import send_alert, process_voice_query

from datetime import datetime, time
import json

def is_alerted(emergency, user_id):
    try:
        alerted = json.loads(emergency.alerted_users or '[]')
        return user_id in alerted
    except (json.JSONDecodeError, TypeError):
        # Fallback for old string format
        return str(user_id) == emergency.alerted_users

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'senior':
        return redirect(url_for('main.senior_dashboard'))
    elif current_user.role == 'caregiver':
        return redirect(url_for('main.caregiver_dashboard'))
    elif current_user.role == 'family':
        return redirect(url_for('main.family_dashboard'))

@main.route('/senior/dashboard')
@login_required
def senior_dashboard():
    if current_user.role != 'senior':
        return redirect(url_for('main.dashboard'))
    reminders = Reminder.query.filter_by(user_id=current_user.id).filter(Reminder.scheduled_time > datetime.now()).order_by(Reminder.scheduled_time).all()
    return render_template('senior_dashboard.html', reminders=reminders)

@main.route('/caregiver/dashboard')
@login_required
def caregiver_dashboard():
    if current_user.role != 'caregiver':
        return redirect(url_for('main.dashboard'))
    seniors = User.query.filter_by(caregiver_id=current_user.id, role='senior').all()
    emergencies = [e for e in EmergencyLog.query.filter_by(status='active').all() if is_alerted(e, current_user.id)]
    return render_template('caregiver_dashboard.html', seniors=seniors, emergencies=emergencies)

@main.route('/family/dashboard')
@login_required
def family_dashboard():
    if current_user.role != 'family':
        return redirect(url_for('main.dashboard'))
    if current_user.caregiver_id:
        seniors = User.query.filter_by(caregiver_id=current_user.caregiver_id, role='senior').all()
        emergencies = [e for e in EmergencyLog.query.filter_by(status='active').all() if is_alerted(e, current_user.caregiver_id)]
    else:
        seniors = User.query.filter_by(caregiver_id=None, role='senior').all()
        emergencies = EmergencyLog.query.filter_by(status='active').all()
    return render_template('family_dashboard.html', seniors=seniors, emergencies=emergencies)

@main.route('/reminders', methods=['GET', 'POST'])
@login_required
def reminders():
    form = ReminderForm()
    user_id = current_user.id if current_user.role == 'senior' else request.args.get('user_id', type=int)
    if not user_id or not check_permission(user_id):
        flash('Unauthorized')
        return redirect(url_for('main.dashboard'))
    if form.validate_on_submit():
        # Use time format consistent with calendar event scheduling
        scheduled_time = datetime.combine(datetime.strptime(form.date.data, '%Y-%m-%d').date(), datetime.strptime(form.event_time.data, '%H:%M').time())
        reminder = Reminder(
            user_id=user_id,
            title=form.title.data,
            description=form.description.data,
            reminder_type=form.reminder_type.data,
            scheduled_time=scheduled_time,
            created_by=current_user.id
        )
        db.session.add(reminder)
        db.session.commit()
        flash('Reminder added successfully!')
        return redirect(url_for('main.reminders', user_id=user_id))
    reminders = Reminder.query.filter_by(user_id=user_id).order_by(Reminder.scheduled_time).all()
    return render_template('reminders.html', form=form, reminders=reminders, user_id=user_id)

@main.route('/reminder/<int:id>/taken', methods=['POST'])
@login_required
def mark_reminder_taken(id):
    reminder = Reminder.query.get_or_404(id)
    if not check_permission(reminder.user_id):
        flash('Unauthorized')
        return redirect(url_for('main.reminders'))
    status = request.form.get('status')
    reminder.is_taken = (status == 'taken')
    db.session.commit()
    flash('Reminder status updated!')
    if current_user.role == 'senior':
        return redirect(url_for('main.senior_dashboard'))
    else:
        return redirect(url_for('main.reminders'))

@main.route('/health', methods=['GET', 'POST'])
@login_required
def health_log():
    form = HealthLogForm()
    user_id = current_user.id if current_user.role == 'senior' else request.args.get('user_id', type=int)
    if not user_id or not check_permission(user_id):
        flash('Unauthorized')
        return redirect(url_for('main.dashboard'))
    if form.validate_on_submit():
        log = HealthLog(
            user_id=user_id,
            bp_systolic=form.bp_systolic.data,
            bp_diastolic=form.bp_diastolic.data,
            sugar_level=form.sugar_level.data,
            weight=form.weight.data,
            heart_rate=form.heart_rate.data
        )
        db.session.add(log)
        db.session.commit()
        flash('Health data logged!')
        return redirect(url_for('main.health_log', user_id=user_id))
    logs = HealthLog.query.filter_by(user_id=user_id).order_by(HealthLog.logged_at.desc()).limit(10).all()
    return render_template('health_log.html', form=form, logs=logs, user_id=user_id)

@main.route('/appointments', methods=['GET', 'POST'])
@login_required
def appointments():
    form = AppointmentForm()
    user_id = current_user.id if current_user.role == 'senior' else request.args.get('user_id', type=int)
    if not user_id or not check_permission(user_id):
        flash('Unauthorized')
        return redirect(url_for('main.dashboard'))
    if form.validate_on_submit():
        # Use time format consistent with calendar event scheduling
        appointment_time = datetime.combine(datetime.strptime(form.date.data, '%Y-%m-%d').date(), datetime.strptime(form.event_time.data, '%H:%M').time())
        appointment = Appointment(
            user_id=user_id,
            doctor_name=form.doctor_name.data,
            appointment_time=appointment_time,
            notes=form.notes.data,
            created_by=current_user.id
        )
        db.session.add(appointment)
        db.session.commit()
        flash('Appointment scheduled!')
        return redirect(url_for('main.appointments', user_id=user_id))
    appointments = Appointment.query.filter_by(user_id=user_id).order_by(Appointment.appointment_time).all()
    return render_template('appointments.html', form=form, appointments=appointments, user_id=user_id)

@main.route('/calendar', methods=['GET', 'POST'])
@login_required
def calendar():
    form = CalendarEventForm()
    user_id = request.args.get('user_id', type=int) or current_user.id
    if user_id != current_user.id and not check_permission(user_id):
        flash('Unauthorized')
        return redirect(url_for('main.dashboard'))
    if form.validate_on_submit():
        event = CalendarEvent(
            user_id=user_id,
            title=form.title.data,
            description=form.description.data,
            event_date=datetime.strptime(form.event_date.data, '%Y-%m-%d').date(),
            event_time=datetime.strptime(form.event_time.data, '%H:%M').time() if form.event_time.data else None,
            created_by=current_user.id
        )
        db.session.add(event)
        db.session.commit()
        flash('Event added!')
        return redirect(url_for('main.calendar', user_id=user_id))
    events = CalendarEvent.query.filter_by(user_id=user_id).order_by(CalendarEvent.event_date).all()
    return render_template('calendar.html', form=form, events=events)

@main.route('/sos', methods=['POST'])
@login_required
def sos():
    if current_user.role != 'senior':
        return jsonify({'error': 'Unauthorized'}), 403
    try:
        data = request.get_json()
        latitude = data.get('latitude')
        if latitude is not None:
            latitude = float(latitude)
        longitude = data.get('longitude')
        if longitude is not None:
            longitude = float(longitude)
        alerted_ids = [current_user.caregiver_id] if current_user.caregiver_id else []
        emergency = EmergencyLog(
            user_id=current_user.id,
            emergency_type='SOS',
            message='Emergency button pressed',
            alerted_users=json.dumps(alerted_ids),
            latitude=latitude,
            longitude=longitude
        )
        db.session.add(emergency)
        db.session.commit()
        for user_id in alerted_ids:
            send_alert(user_id, f"SOS from {current_user.username}")
        return jsonify({'message': 'SOS sent'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to send SOS: ' + str(e)}), 500

@main.route('/voice', methods=['POST'])
@login_required
def voice_query():
    query = request.json.get('query')
    response = process_voice_query(query, current_user)
    return jsonify({'response': response})

def check_permission(user_id):
    user = User.query.get(user_id)
    if not user:
        return False
    if current_user.role == 'senior':
        return current_user.id == user_id
    elif current_user.role == 'caregiver':
        return user.caregiver_id == current_user.id
    elif current_user.role == 'family':
        return current_user.caregiver_id == user.caregiver_id
    return False

@main.route('/caregiver/add_user', methods=['GET', 'POST'])
@login_required
def caregiver_add_user():
    if current_user.role != 'caregiver':
        flash('Unauthorized')
        return redirect(url_for('main.dashboard'))
    form = AddUserForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash('User not found')
            return redirect(url_for('main.caregiver_add_user'))
        if user.role not in ['senior', 'family']:
            flash('Can only add senior or family users')
            return redirect(url_for('main.caregiver_add_user'))
        user.caregiver_id = current_user.id
        db.session.commit()
        flash('User linked successfully!')
        return redirect(url_for('main.caregiver_dashboard'))
    return render_template('add_user.html', form=form, action='caregiver_add_user')

@main.route('/family/add_user', methods=['GET', 'POST'])
@login_required
def family_add_user():
    if current_user.role != 'family':
        flash('Unauthorized')
        return redirect(url_for('main.dashboard'))
    form = AddUserForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash('User not found')
            return redirect(url_for('main.family_add_user'))
        if user.role not in ['senior', 'family']:
            flash('Can only add senior or family users')
            return redirect(url_for('main.family_add_user'))
        user.caregiver_id = current_user.caregiver_id
        db.session.commit()
        flash('User linked successfully!')
        return redirect(url_for('main.family_dashboard'))
    return render_template('add_user.html', form=form, action='family_add_user')

# API routes for notifications
@main.route('/api/due_reminders', methods=['GET'])
@login_required
def get_due_reminders():
    if current_user.role != 'senior':
        return jsonify({'error': 'Unauthorized'}), 403
    now = datetime.now()
    reminders = Reminder.query.filter(
        Reminder.user_id == current_user.id,
        Reminder.is_taken == False,
        Reminder.notified == False,
        Reminder.scheduled_time <= now
    ).all()
    data = [{'id': r.id, 'title': r.title, 'scheduled_time': r.scheduled_time.isoformat()} for r in reminders]
    return jsonify(data)

@main.route('/api/due_appointments', methods=['GET'])
@login_required
def get_due_appointments():
    if current_user.role != 'senior':
        return jsonify({'error': 'Unauthorized'}), 403
    now = datetime.now()
    appointments = Appointment.query.filter(
        Appointment.user_id == current_user.id,
        Appointment.status == 'scheduled',
        Appointment.notified == False,
        Appointment.appointment_time <= now
    ).all()
    data = [{'id': a.id, 'doctor_name': a.doctor_name, 'appointment_time': a.appointment_time.isoformat()} for a in appointments]
    return jsonify(data)

@main.route('/api/due_events', methods=['GET'])
@login_required
def get_due_events():
    if current_user.role != 'senior':
        return jsonify({'error': 'Unauthorized'}), 403
    now = datetime.now()
    events = CalendarEvent.query.filter(
        CalendarEvent.user_id == current_user.id,
        CalendarEvent.notified == False
    ).all()
    due_events = []
    for e in events:
        if e.event_date < now.date():
            due_events.append(e)
        elif e.event_date == now.date():
            if e.event_time is None or e.event_time <= now.time():
                due_events.append(e)
    data = [{'id': e.id, 'title': e.title, 'event_date': e.event_date.isoformat(), 'event_time': e.event_time.isoformat() if e.event_time else None} for e in due_events]
    return jsonify(data)

@main.route('/api/mark_notified/<string:type>/<int:item_id>', methods=['POST'])
@login_required
def mark_notified(type, item_id):
    if current_user.role != 'senior':
        return jsonify({'error': 'Unauthorized'}), 403
    if type == 'reminder':
        item = Reminder.query.get(item_id)
        if item and item.user_id == current_user.id:
            item.notified = True
            item.is_taken = True  # Mark as taken too
            db.session.commit()
            return jsonify({'message': 'Reminder marked'})
    elif type == 'appointment':
        item = Appointment.query.get(item_id)
        if item and item.user_id == current_user.id:
            item.notified = True
            item.status = 'completed'
            db.session.commit()
            return jsonify({'message': 'Appointment marked'})
    elif type == 'event':
        item = CalendarEvent.query.get(item_id)
        if item and item.user_id == current_user.id:
            item.notified = True
            db.session.commit()
            return jsonify({'message': 'Event marked'})
    return jsonify({'error': 'Item not found'}), 404

@main.route('/insights')
@login_required
def insights():
    user_id = None
    if current_user.role == 'senior':
        user_id = current_user.id
    else:
        user_id = request.args.get('user_id', type=int)
        if user_id and not check_permission(user_id):
            flash('Unauthorized')
            return redirect(url_for('main.dashboard'))

    # Get linked seniors for caregiver/family
    seniors = []
    if current_user.role == 'caregiver':
        seniors = User.query.filter_by(caregiver_id=current_user.id, role='senior').all()
    elif current_user.role == 'family':
        if current_user.caregiver_id:
            seniors = User.query.filter_by(caregiver_id=current_user.caregiver_id, role='senior').all()
        else:
            seniors = User.query.filter_by(caregiver_id=None, role='senior').all()

    health_status = None
    health_metrics = None
    ranked_tasks = None

    if user_id:
        from app.utils import classify_health_status, rank_tasks
        health_status, health_metrics = classify_health_status(user_id)
        ranked_tasks = rank_tasks(user_id)

    return render_template('insights.html', health_status=health_status, health_metrics=health_metrics, ranked_tasks=ranked_tasks, user_id=user_id, seniors=seniors)






