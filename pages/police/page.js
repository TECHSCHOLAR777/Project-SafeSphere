export function init(params = {}) {
    const app = document.getElementById('app');
    app.innerHTML = `
        <section class="police-dashboard">
            <h2>Police Console</h2>
            <p>Incidents requiring attention will appear here.</p>
            <div id="police-incidents"><em>Loading...</em></div>
        </section>
    `;

    async function loadForPolice() {
        const container = document.getElementById('police-incidents');
        try {
            const res = await fetch('/incidents?limit=10');
            const json = await res.json();
            container.innerHTML = '';
            if (json.incidents && json.incidents.length) {
                const ul = document.createElement('ul');
                json.incidents.forEach(it => {
                    const li = document.createElement('li');
                    li.textContent = `${it.timestamp} — ${it.threat_level} — ${it.behavior_summary || ''}`;
                    ul.appendChild(li);
                });
                container.appendChild(ul);
            } else {
                container.innerHTML = '<p>No incidents</p>';
            }
        } catch (e) {
            container.innerHTML = '<p>Failed to load incidents</p>';
        }
    }

    loadForPolice();
}

export function teardown() {
    const app = document.getElementById('app');
    if (app) app.innerHTML = '';
}
