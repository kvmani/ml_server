document.addEventListener('DOMContentLoaded', () => {
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
    if (!search || !cards.length) return;
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
});
