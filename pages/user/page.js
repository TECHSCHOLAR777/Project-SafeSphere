export function init(params = {}) {
    const app = document.getElementById('app');
    app.innerHTML = `
        <section class="user-dashboard">
            <h2>User Dashboard</h2>
            <div class="user-actions">
                <button id="user-sos" class="btn danger">SOS</button>
                <button id="user-share-location" class="btn">Share Location</button>
            </div>
            <div id="user-incidents" class="incidents">
                <h3>Recent Incidents</h3>
                <ul id="incidents-list"><li>Loading...</li></ul>
            </div>
        </section>
    `;

    document.getElementById('user-sos').addEventListener('click', () => {
        // Reuse ActionHandler if present
        if (window.ActionHandler && typeof window.ActionHandler.triggerSOS === 'function') {
            window.ActionHandler.triggerSOS();
        } else {
            alert('SOS triggered');
        }
    });

    document.getElementById('user-share-location').addEventListener('click', async () => {
        if (!navigator.geolocation) return alert('Geolocation not supported');
        navigator.geolocation.getCurrentPosition(pos => {
            Toast.show('Location shared', 'info');
            console.log('Shared location:', pos.coords);
        }, err => {
            Toast.show('Failed to get location', 'error');
        });
    });

    // Load recent incidents from backend if available
    async function loadIncidents() {
        const list = document.getElementById('incidents-list');
        try {
            const res = await fetch('/incidents?limit=5');
            const json = await res.json();
            list.innerHTML = '';
            if (json.incidents && json.incidents.length) {
                json.incidents.forEach(it => {
                    const li = document.createElement('li');
                    li.textContent = `${it.timestamp} — ${it.threat_level} — score:${it.threat_score}`;
                    list.appendChild(li);
                });
            } else {
                list.innerHTML = '<li>No recent incidents</li>';
            }
        } catch (e) {
            list.innerHTML = '<li>Unable to fetch incidents</li>';
        }
    }

    loadIncidents();
}

export function teardown() {
    const app = document.getElementById('app');
    if (app) app.innerHTML = '';
}
