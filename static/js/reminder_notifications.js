document.addEventListener("DOMContentLoaded", function() {
    let soundOn = true;
    const alarm = new Audio("https://actions.google.com/sounds/v1/alarms/alarm_clock.ogg");
    const toggleBtn = document.getElementById("toggleSound");
    const reminderList = document.getElementById("reminderList");
    const popup = document.createElement("div");
    popup.id = "notificationPopup";
    popup.style.cssText = "position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; border: 2px solid red; padding: 20px; z-index: 10000; display: none; font-size: 18px; color: black;";
    document.body.appendChild(popup);
    popup.addEventListener("click", () => popup.style.display = "none");

    toggleBtn.addEventListener("click", () => {
        soundOn = !soundOn;
        toggleBtn.textContent = soundOn ? "🔊 Sound ON" : "🔇 Sound OFF";
    });

    function fetchDueItems() {
        fetch('/api/due_reminders')
            .then(res => res.json())
            .then(reminders => {
                reminders.forEach(reminder => {
                    displayReminder('Reminder', reminder.title, reminder.scheduled_time);
                    if (soundOn) alarm.play();
                    fetch(`/api/mark_notified/reminder/${reminder.id}`, {method: "POST"});
                });
            });

        fetch('/api/due_appointments')
            .then(res => res.json())
            .then(appointments => {
                appointments.forEach(appointment => {
                    displayReminder('Appointment', `Appointment with Dr. ${appointment.doctor_name}`, appointment.appointment_time);
                    if (soundOn) alarm.play();
                    fetch(`/api/mark_notified/appointment/${appointment.id}`, {method: "POST"});
                });
            });

        fetch('/api/due_events')
            .then(res => res.json())
            .then(events => {
                events.forEach(event => {
                    displayReminder('Event', event.title, event.event_date + (event.event_time ? ' ' + event.event_time : ''));
                    if (soundOn) alarm.play();
                    fetch(`/api/mark_notified/event/${event.id}`, {method: "POST"});
                });
            });
    }

    function displayReminder(type, title, time) {
        const tr = document.createElement("tr");
        const tdType = document.createElement("td");
        tdType.textContent = type;
        const tdTitle = document.createElement("td");
        tdTitle.textContent = title;
        const tdTime = document.createElement("td");
        tdTime.textContent = new Date(time).toLocaleString();
        tr.appendChild(tdType);
        tr.appendChild(tdTitle);
        tr.appendChild(tdTime);
        reminderList.appendChild(tr);
        popup.textContent = `${type}: ${title}`;
        popup.style.display = "block";
        setTimeout(() => popup.style.display = "none", 5000); // Hide after 5 seconds
    }

    setInterval(fetchDueItems, 10000);
    fetchDueItems();
});
