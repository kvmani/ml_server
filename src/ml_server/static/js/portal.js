document.addEventListener('DOMContentLoaded', () => {
    const sessionStarted = Number(sessionStorage.getItem('mlSessionStarted')) || Date.now();
    sessionStorage.setItem('mlSessionStarted', String(sessionStarted));
    const sessionDuration = () => Math.max(0, Date.now() - sessionStarted);
    const currentToolId = window.location.pathname.startsWith('/pdf_tools') ? 'pdf-tools'
        : window.location.pathname.startsWith('/tabular_ml') ? 'tabular-ml' : undefined;
    const track = (eventName, details = {}, beacon = false) => {
        const body = JSON.stringify({
            event_name: eventName,
            path: window.location.pathname,
            duration_ms: sessionDuration(),
            visibility: document.visibilityState,
            tool_id: currentToolId,
            ...details
        });
        if (beacon && navigator.sendBeacon) {
            navigator.sendBeacon('/api/analytics/event', new Blob([body], { type: 'application/json' }));
            return;
        }
        fetch('/api/analytics/event', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body, keepalive: true
        }).catch(() => {});
    };
    track('page_view');
    window.setInterval(() => track('heartbeat'), 60000);
    window.addEventListener('pagehide', () => track('session_end', {}, true));

    const activeUserCount = document.getElementById('active-user-count');
    const refreshPresence = async () => {
        if (!activeUserCount) return;
        try {
            const response = await fetch('/api/active-users', { headers: { Accept: 'application/json' } });
            if (!response.ok) return;
            const payload = await response.json();
            const count = Math.max(1, Number(payload.active_users) || 1);
            activeUserCount.textContent = String(count);
            const label = activeUserCount.nextElementSibling;
            if (label) label.textContent = count === 1 ? 'user' : 'users';
        } catch (_error) {
            // Presence is advisory; the landing page remains fully usable offline.
        }
    };
    if (activeUserCount) {
        refreshPresence();
        window.setInterval(refreshPresence, 15000);
    }

    const search = document.getElementById('tool-search');
    const cards = [...document.querySelectorAll('[data-tool-card]')];
    const count = document.getElementById('tool-count');
    const empty = document.getElementById('tool-empty');
    cards.forEach(card => {
        const launch = card.querySelector('[data-tool-launch]');
        if (launch) launch.addEventListener('click', () => track('tool_open', {
            tool_id: card.dataset.toolId
        }, true));
    });
    if (search && cards.length) {
        const update = () => {
            const query = search.value.trim().toLowerCase();
            let visible = 0;
            cards.forEach(card => {
                const match = !query || card.dataset.search.includes(query);
                card.hidden = !match;
                if (match) visible += 1;
            });
            count.textContent = `${visible} of ${cards.length} tools`;
            empty.hidden = visible !== 0;
        };
        search.addEventListener('input', update);
        update();
    }

    const form = document.getElementById('feedback-form');
    const title = document.getElementById('feedback-modal-title');
    const kindInput = document.getElementById('feedback-kind');
    const result = document.getElementById('feedback-result');
    const submit = document.getElementById('feedback-submit');
    document.querySelectorAll('[data-feedback-kind]').forEach(button => button.addEventListener('click', () => {
        const feature = button.dataset.feedbackKind === 'feature_request';
        kindInput.value = feature ? 'feature_request' : 'feedback';
        title.textContent = feature ? 'Request a feature' : 'Send feedback';
        submit.textContent = feature ? 'Submit request' : 'Submit feedback';
        result.hidden = true;
    }));
    if (form) form.addEventListener('submit', async event => {
        event.preventDefault();
        submit.disabled = true;
        result.hidden = true;
        document.getElementById('feedback-page-url').value = window.location.href;
        const started = performance.now();
        try {
            const response = await fetch(form.action, { method: 'POST', body: new FormData(form) });
            const payload = await response.json();
            if (!response.ok || !payload.success) throw new Error(payload.message || 'Submission failed');
            result.className = 'feedback-result feedback-success';
            result.textContent = `Thank you — saved as reference #${payload.reference}.`;
            result.hidden = false;
            form.querySelector('textarea').value = '';
            track('major_action', { duration_ms: Math.round(performance.now() - started) });
        } catch (error) {
            result.className = 'feedback-result feedback-error';
            result.textContent = error.message || 'Could not submit your message. Please try again.';
            result.hidden = false;
        } finally {
            submit.disabled = false;
        }
    });
});
