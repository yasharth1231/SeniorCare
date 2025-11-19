// JavaScript for Senior Citizen Assistant App

// Function to handle SOS button
function triggerSOS() {
    if (confirm('Are you sure you want to send an SOS alert?')) {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition((position) => {
                const latitude = position.coords.latitude;
                const longitude = position.coords.longitude;

                fetch('/sos', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        latitude: latitude,
                        longitude: longitude
                    })
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message || 'SOS sent successfully');
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Failed to send SOS');
                });
            }, (error) => {
                console.error('Geolocation error:', error);
                alert('Unable to get location. SOS sent without location.');
                // Send SOS without location
                fetch('/sos', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({})
                })
                .then(response => response.json())
                .then(data => {
                    alert(data.message || 'SOS sent successfully');
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Failed to send SOS');
                });
            });
        } else {
            alert('Geolocation is not supported by this browser. SOS sent without location.');
            fetch('/sos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message || 'SOS sent successfully');
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to send SOS');
            });
        }
    }
}

// Function to start voice assistant
function startVoice() {
    const query = prompt("Speak your query or type it here:");
    if (query) {
        fetch('/voice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.response || 'No response');
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Voice query failed');
        });
    }
}

// Function to mark reminder as taken
function markTaken(reminderId) {
    fetch(`/reminder/${reminderId}/taken`, {
        method: 'POST'
    })
    .then(response => {
        if (response.ok) {
            location.reload();
        } else {
            alert('Failed to mark reminder');
        }
    });
}

// Date picker for calendar
document.addEventListener('DOMContentLoaded', function() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(input => {
        input.min = new Date().toISOString().split('T')[0];
    });
});
