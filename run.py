from app import create_app, db
from app.models import User, Reminder, HealthLog, Appointment, EmergencyLog, CalendarEvent

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Reminder': Reminder, 'HealthLog': HealthLog, 'Appointment': Appointment, 'EmergencyLog': EmergencyLog, 'CalendarEvent': CalendarEvent}

if __name__ == '__main__':
    app.run(debug=True)
