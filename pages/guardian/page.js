export function init(params = {}) {
    const app = document.getElementById('app');
    app.innerHTML = `
        <section class="guardian-dashboard">
            <h2>Guardian Console</h2>
            <p>Overview of your protected contacts and alerts.</p>
            <div id="guardian-list"><em>Loading trusted contacts...</em></div>
        </section>
    `;

    // Example: render a minimal trusted contacts list
    const list = document.getElementById('guardian-list');
    list.innerHTML = `
        <ul>
            <li>Alice — 999-000-111</li>
            <li>Bob — 999-000-222</li>
        </ul>
    `;
}

export function teardown() {
    const app = document.getElementById('app');
    if (app) app.innerHTML = '';
}
