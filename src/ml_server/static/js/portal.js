document.addEventListener('DOMContentLoaded', () => {
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
