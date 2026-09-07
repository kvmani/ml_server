/* Admin operations console.
 *
 * The page ships empty and every panel fills itself from /admin/api/*. That
 * keeps the live view refreshing on its own short timer without redrawing the
 * analytics, and it means the same JSON an operator can curl is exactly what
 * the charts are drawn from.
 *
 * Every value that reaches the DOM does so through textContent. Log lines,
 * request paths and client addresses all originate outside this application,
 * so none of them may ever be parsed as markup.
 */
(function () {
    'use strict';

    var LIVE_REFRESH_MS = 5000;
    var ANALYTICS_REFRESH_MS = 60000;

    var state = {
        window: '24h',
        months: 6,
        activePanel: 'overview',
        autoRefresh: true,
        charts: {},
        timers: {}
    };

    // -- tiny DOM helpers --------------------------------------------------
    function el(tag, className, text) {
        var node = document.createElement(tag);
        if (className) { node.className = className; }
        if (text !== undefined && text !== null) { node.textContent = String(text); }
        return node;
    }

    function clear(node) {
        while (node && node.firstChild) { node.removeChild(node.firstChild); }
    }

    function byId(id) { return document.getElementById(id); }

    function number(value) {
        if (value === null || value === undefined || isNaN(value)) { return '0'; }
        return Number(value).toLocaleString();
    }

    function ms(value) {
        var amount = Number(value || 0);
        if (amount >= 1000) { return (amount / 1000).toFixed(2) + ' s'; }
        return Math.round(amount) + ' ms';
    }

    function seconds(value) {
        var amount = Number(value || 0);
        if (amount < 60) { return amount.toFixed(0) + 's'; }
        if (amount < 3600) { return Math.floor(amount / 60) + 'm ' + Math.round(amount % 60) + 's'; }
        return Math.floor(amount / 3600) + 'h ' + Math.floor((amount % 3600) / 60) + 'm';
    }

    function showError(message) {
        var banner = byId('error-banner');
        if (!banner) { return; }
        if (!message) {
            banner.hidden = true;
            return;
        }
        banner.textContent = message;
        banner.hidden = false;
    }

    function fetchJson(url) {
        return fetch(url, { headers: { Accept: 'application/json' }, credentials: 'same-origin' })
            .then(function (response) {
                if (response.status === 401) {
                    window.location.href = '/admin/login';
                    throw new Error('Session expired');
                }
                if (!response.ok) { throw new Error('Request failed: ' + response.status); }
                return response.json();
            });
    }

    // -- table rendering ---------------------------------------------------
    /* columns: [{ label, get(row) -> string, cell(row) -> Node (optional) }] */
    function renderTable(table, columns, rows, emptyMessage) {
        clear(table);
        var head = el('thead');
        var headRow = el('tr');
        columns.forEach(function (column) {
            headRow.appendChild(el('th', null, column.label));
        });
        head.appendChild(headRow);
        table.appendChild(head);

        var body = el('tbody');
        if (!rows || !rows.length) {
            var emptyRow = el('tr');
            var emptyCell = el('td', 'admin-empty', emptyMessage || 'No data recorded yet.');
            emptyCell.colSpan = columns.length;
            emptyRow.appendChild(emptyCell);
            body.appendChild(emptyRow);
        } else {
            rows.forEach(function (row) {
                var tr = el('tr');
                columns.forEach(function (column) {
                    if (column.cell) {
                        var td = el('td', column.className || null);
                        td.appendChild(column.cell(row));
                        tr.appendChild(td);
                    } else {
                        tr.appendChild(el('td', column.className || null, column.get(row)));
                    }
                });
                body.appendChild(tr);
            });
        }
        table.appendChild(body);
    }

    function badge(text, tone) {
        return el('span', 'admin-badge is-' + (tone || 'muted'), text);
    }

    function statusTone(status) {
        var code = Number(status || 0);
        if (code >= 500) { return 'critical'; }
        if (code >= 400) { return 'error'; }
        if (code >= 300) { return 'warn'; }
        return 'ok';
    }

    function levelTone(level) {
        return {
            DEBUG: 'muted',
            INFO: 'info',
            WARNING: 'warn',
            ERROR: 'error',
            CRITICAL: 'critical'
        }[level] || 'muted';
    }

    // -- KPI cards ---------------------------------------------------------
    function kpi(title, value, note, tone) {
        var card = el('div', 'admin-card admin-kpi' + (tone ? ' is-' + tone : ''));
        card.appendChild(el('h2', null, title));
        card.appendChild(el('div', 'admin-kpi-value', value));
        if (note) { card.appendChild(el('div', 'admin-kpi-note', note)); }
        return card;
    }

    // -- charts ------------------------------------------------------------
    var PALETTE = ['#4da3ff', '#43c78a', '#f0b429', '#f2665e', '#a78bfa', '#22d3ee', '#fb923c', '#d6336c'];

    function chartDefaults() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: {
                legend: { labels: { color: '#93a4b8', boxWidth: 12, font: { size: 11 } } },
                tooltip: { intersect: false, mode: 'index' }
            },
            scales: {
                x: { ticks: { color: '#93a4b8', maxRotation: 0, autoSkip: true }, grid: { color: '#2b3849' } },
                y: { beginAtZero: true, ticks: { color: '#93a4b8' }, grid: { color: '#2b3849' } }
            }
        };
    }

    function drawChart(id, type, labels, datasets, optionOverrides) {
        var canvas = byId(id);
        if (!canvas || typeof Chart === 'undefined') { return; }
        var options = chartDefaults();
        if (type === 'doughnut') { delete options.scales; }
        if (optionOverrides) {
            Object.keys(optionOverrides).forEach(function (key) { options[key] = optionOverrides[key]; });
        }
        if (state.charts[id]) {
            state.charts[id].data.labels = labels;
            state.charts[id].data.datasets = datasets;
            state.charts[id].update();
            return;
        }
        state.charts[id] = new Chart(canvas, {
            type: type,
            data: { labels: labels, datasets: datasets },
            options: options
        });
    }

    function bars(label, data, colorIndex) {
        return {
            label: label,
            data: data,
            backgroundColor: PALETTE[colorIndex % PALETTE.length] + 'cc',
            borderColor: PALETTE[colorIndex % PALETTE.length],
            borderWidth: 1
        };
    }

    function line(label, data, colorIndex) {
        return {
            label: label,
            data: data,
            borderColor: PALETTE[colorIndex % PALETTE.length],
            backgroundColor: PALETTE[colorIndex % PALETTE.length] + '33',
            borderWidth: 2,
            fill: true,
            tension: 0.25,
            pointRadius: 0
        };
    }

    // -- overview ----------------------------------------------------------
    function renderOverview(report) {
        var totals = report.totals;
        var uptime = report.uptime || {};
        var grid = byId('kpi-grid');
        clear(grid);
        grid.appendChild(kpi('Uptime', uptime.process_human || 'n/a',
            uptime.host_human && uptime.host_human !== 'unavailable' ? 'host up ' + uptime.host_human : 'portal process'));
        grid.appendChild(kpi('Active now', number((report.live || {}).active_clients),
            'client addresses in the last 5 minutes', 'ok'));
        grid.appendChild(kpi('Unique visitors', number(totals.unique_clients),
            report.window_label));
        grid.appendChild(kpi('Requests', number(totals.requests), report.window_label));
        grid.appendChild(kpi('Error rate', totals.error_rate + '%',
            number(totals.errors) + ' errors, ' + number(totals.server_errors) + ' server-side',
            totals.error_rate >= 5 ? 'error' : (totals.error_rate >= 1 ? 'warn' : 'ok')));
        grid.appendChild(kpi('Response time p95', ms(totals.p95),
            'average ' + ms(totals.average_ms) + ' - p50 ' + ms(totals.p50) + ' - p99 ' + ms(totals.p99)));
        grid.appendChild(kpi('Sessions', number(totals.sessions), report.window_label));
        grid.appendChild(kpi('Server time spent', seconds(totals.total_seconds),
            'total processing in this window'));

        var traffic = report.traffic || { points: [] };
        var labels = traffic.points.map(function (point) { return point.bucket; });
        drawChart('traffic-chart', 'line', labels, [
            line('Events', traffic.points.map(function (p) { return p.events; }), 0),
            line('Unique visitors', traffic.points.map(function (p) { return p.unique_clients; }), 1),
            line('Errors', traffic.points.map(function (p) { return p.errors; }), 3)
        ]);

        var months = report.unique_clients_by_month || [];
        drawChart('monthly-chart', 'bar', months.map(function (m) { return m.month; }), [
            bars('Unique visitors', months.map(function (m) { return m.unique_clients; }), 1),
            bars('Sessions', months.map(function (m) { return m.sessions; }), 0)
        ]);

        var tools = (report.tools || []).slice(0, 12);
        drawChart('service-chart', 'bar', tools.map(function (t) { return t.tool_name; }), [
            bars('Requests', tools.map(function (t) { return t.requests; }), 0),
            bars('Errors', tools.map(function (t) { return t.errors; }), 3)
        ]);

        var hours = report.hour_profile || [];
        drawChart('hour-chart', 'bar', hours.map(function (h) { return h.hour; }), [
            bars('Events', hours.map(function (h) { return h.events; }), 2)
        ]);

        renderTable(byId('status-table'), [
            { label: 'Status', cell: function (row) { return badge(row.status_code, statusTone(row.status_code)); } },
            { label: 'Responses', get: function (row) { return number(row.responses); } }
        ], report.status_codes, 'No responses recorded in this window.');

        var pathColumns = [
            { label: 'Path', className: 'admin-mono is-wrap', get: function (row) { return row.path; } },
            { label: 'Requests', get: function (row) { return number(row.requests); } },
            { label: 'Errors', get: function (row) { return number(row.errors); } },
            { label: 'Average', get: function (row) { return ms(row.average_ms); } },
            { label: 'Slowest', get: function (row) { return ms(row.slowest_ms); } }
        ];
        renderTable(byId('busiest-table'), pathColumns, (report.endpoints || {}).busiest,
            'No requests recorded in this window.');
        renderTable(byId('slowest-table'), pathColumns, (report.endpoints || {}).slowest,
            'Not enough samples yet.');
    }

    // -- services ----------------------------------------------------------
    function renderServices(report) {
        var tools = report.tools || [];
        var labels = tools.map(function (t) { return t.tool_name; });
        drawChart('timing-chart', 'bar', labels, [
            bars('Average ms', tools.map(function (t) { return t.average_ms; }), 0),
            bars('p95 ms', tools.map(function (t) { return t.p95; }), 2),
            bars('p99 ms', tools.map(function (t) { return t.p99; }), 3)
        ]);
        drawChart('time-spent-chart', 'bar', labels, [
            bars('Seconds of server time', tools.map(function (t) { return t.total_seconds; }), 1)
        ]);

        renderTable(byId('services-table'), [
            { label: 'Service', get: function (r) { return r.tool_name; } },
            { label: 'Requests', get: function (r) { return number(r.requests); } },
            { label: 'Opens', get: function (r) { return number(r.opens); } },
            { label: 'Sessions', get: function (r) { return number(r.sessions); } },
            { label: 'Unique visitors', get: function (r) { return number(r.unique_clients); } },
            { label: 'Errors', cell: function (r) {
                return badge(number(r.errors) + ' (' + r.error_rate + '%)',
                    r.error_rate >= 5 ? 'error' : (r.error_rate >= 1 ? 'warn' : 'ok'));
            } },
            { label: 'Average', get: function (r) { return ms(r.average_ms); } },
            { label: 'p50', get: function (r) { return ms(r.p50); } },
            { label: 'p90', get: function (r) { return ms(r.p90); } },
            { label: 'p95', get: function (r) { return ms(r.p95); } },
            { label: 'p99', get: function (r) { return ms(r.p99); } },
            { label: 'Slowest', get: function (r) { return ms(r.slowest_ms); } },
            { label: 'Total time', get: function (r) { return seconds(r.total_seconds); } },
            { label: 'Last used', get: function (r) { return r.last_used_at || '-'; } }
        ], tools, 'No service activity recorded in this window.');
    }

    // -- visitors ----------------------------------------------------------
    function renderVisitors(report) {
        var grid = byId('visitor-kpis');
        clear(grid);
        (report.unique_clients_by_window || []).forEach(function (entry) {
            grid.appendChild(kpi('Unique visitors, ' + entry.label,
                number(entry.unique_clients), number(entry.sessions) + ' sessions'));
        });

        renderTable(byId('monthly-table'), [
            { label: 'Month', get: function (r) { return r.month; } },
            { label: 'Unique visitors', get: function (r) { return number(r.unique_clients); } },
            { label: 'Sessions', get: function (r) { return number(r.sessions); } },
            { label: 'Requests', get: function (r) { return number(r.requests); } },
            { label: 'Events', get: function (r) { return number(r.events); } },
            { label: 'Server time', get: function (r) { return seconds(r.total_seconds); } }
        ], report.unique_clients_by_month, 'No monthly history yet.');

        var browsers = report.browsers || [];
        drawChart('browser-chart', 'doughnut', browsers.map(function (b) { return b.browser_family; }), [{
            data: browsers.map(function (b) { return b.sessions; }),
            backgroundColor: PALETTE,
            borderColor: '#161f2b',
            borderWidth: 2
        }]);

        var buckets = (report.sessions || {}).duration_buckets || [];
        drawChart('session-chart', 'bar', buckets.map(function (b) { return b.bucket; }), [
            bars('Sessions', buckets.map(function (b) { return b.sessions; }), 4)
        ]);

        renderTable(byId('browser-version-table'), [
            { label: 'Browser', get: function (r) { return r.browser_family; } },
            { label: 'Major version', get: function (r) { return r.browser_major_version; } },
            { label: 'Sessions', get: function (r) { return number(r.sessions); } }
        ], report.browser_versions, 'No version data recorded yet.');

        renderTable(byId('sessions-table'), [
            { label: 'Started', get: function (r) { return r.started_at; } },
            { label: 'Last seen', get: function (r) { return r.last_seen_at; } },
            { label: 'Duration', get: function (r) { return ms(r.duration_ms); } },
            { label: 'Browser', get: function (r) {
                return (r.browser_family || 'Unknown') + (r.browser_major_version ? ' ' + r.browser_major_version : '');
            } },
            { label: 'Last service', get: function (r) { return r.last_tool_name || 'Portal'; } }
        ], (report.sessions || {}).recent_sessions, 'No sessions recorded yet.');
    }

    // -- live --------------------------------------------------------------
    function renderLive(snapshot) {
        var grid = byId('live-kpis');
        clear(grid);
        var uptime = snapshot.uptime || {};
        grid.appendChild(kpi('Active clients', number(snapshot.active_clients),
            'distinct addresses in the last ' + Math.round(snapshot.window_seconds / 60) + ' minutes', 'ok'));
        grid.appendChild(kpi('Requests in window', number(snapshot.active_requests),
            'served to those clients'));
        grid.appendChild(kpi('Services in use', number((snapshot.services || []).length),
            'with at least one active client'));
        grid.appendChild(kpi('Uptime', uptime.process_human || 'n/a', 'since the last restart'));

        var windowNode = byId('live-window');
        if (windowNode) { windowNode.textContent = String(Math.round(snapshot.window_seconds / 60)); }

        renderTable(byId('live-services-table'), [
            { label: 'Service', get: function (r) { return r.service; } },
            { label: 'Clients', get: function (r) { return number(r.clients); } },
            { label: 'Requests', get: function (r) { return number(r.requests); } },
            { label: 'Errors', get: function (r) { return number(r.errors); } },
            { label: 'Average', get: function (r) { return ms(r.average_ms); } },
            { label: 'Last activity', get: function (r) { return seconds(r.idle_seconds) + ' ago'; } },
            { label: 'Addresses', className: 'admin-mono is-wrap', get: function (r) { return r.addresses.join(', '); } }
        ], snapshot.services, 'No service is being used right now.');

        renderTable(byId('live-clients-table'), [
            { label: 'Address', className: 'admin-mono', get: function (r) { return r.ip; } },
            { label: 'Using', get: function (r) { return r.current_service; } },
            { label: 'All services', get: function (r) {
                return r.services.map(function (s) { return s.service; }).join(', ');
            } },
            { label: 'Requests', get: function (r) { return number(r.requests); } },
            { label: 'Errors', get: function (r) { return number(r.errors); } },
            { label: 'Average', get: function (r) { return ms(r.average_ms); } },
            { label: 'Last status', cell: function (r) { return badge(r.last_status, statusTone(r.last_status)); } },
            { label: 'Last path', className: 'admin-mono is-wrap', get: function (r) { return r.last_path; } },
            { label: 'Browser', get: function (r) { return r.browser; } },
            { label: 'Idle', get: function (r) { return seconds(r.idle_seconds); } },
            { label: 'Active for', get: function (r) { return seconds(r.session_seconds); } }
        ], snapshot.clients, 'No clients are active right now.');

        var chip = byId('uptime-chip');
        if (chip) {
            clear(chip);
            chip.appendChild(el('span', 'admin-live-dot'));
            chip.appendChild(document.createTextNode(
                'uptime ' + (uptime.process_human || 'n/a') + ' - ' + number(snapshot.active_clients) + ' active'));
        }
    }

    // -- logs --------------------------------------------------------------
    function renderLogs(payload) {
        var counts = payload.counts || {};
        var countsNode = byId('log-counts');
        clear(countsNode);
        ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'].forEach(function (level) {
            if (!counts[level]) { return; }
            var chip = badge(level + ' ' + number(counts[level]), levelTone(level));
            chip.style.marginRight = '0.35rem';
            countsNode.appendChild(chip);
        });

        var source = byId('log-source');
        source.textContent = payload.exists
            ? payload.path + ' - ' + number(payload.matched_records) + ' of ' +
              number(payload.total_records) + ' records match' +
              (payload.truncated ? ' (reading the most recent 2 MB of the file)' : '')
            : 'No log file found at ' + payload.path;

        renderTable(byId('log-table'), [
            { label: 'Time', className: 'admin-mono', get: function (r) { return r.timestamp || '-'; } },
            { label: 'Level', cell: function (r) { return badge(r.level, levelTone(r.level)); } },
            { label: 'Message', className: 'is-wrap', cell: function (r) {
                var holder = document.createDocumentFragment();
                holder.appendChild(document.createTextNode(r.message));
                if (r.detail) { holder.appendChild(el('span', 'admin-log-detail', r.detail)); }
                return holder;
            } }
        ], payload.records, payload.exists ? 'No records match this filter.' : 'The log file has not been created yet.');
    }

    // -- diagnostics -------------------------------------------------------
    function definitionCard(title, pairs) {
        var card = el('div', 'admin-card');
        card.appendChild(el('h2', null, title));
        var list = el('dl', 'admin-definition');
        pairs.forEach(function (pair) {
            list.appendChild(el('dt', null, pair[0]));
            var dd = el('dd');
            if (pair[1] instanceof Node) { dd.appendChild(pair[1]); } else { dd.textContent = String(pair[1]); }
            list.appendChild(dd);
        });
        card.appendChild(list);
        return card;
    }

    function meter(percent) {
        var holder = el('div', 'admin-meter');
        var fill = el('span');
        fill.style.width = Math.min(100, Math.max(0, Number(percent || 0))) + '%';
        if (percent >= 90) { fill.className = 'is-error'; } else if (percent >= 75) { fill.className = 'is-warn'; }
        holder.appendChild(fill);
        return holder;
    }

    function renderDiagnostics(payload) {
        var grid = byId('diagnostics-grid');
        clear(grid);
        var host = payload.host || {};
        var app = payload.application || {};
        var uptime = payload.uptime || {};

        grid.appendChild(definitionCard('Host', [
            ['Hostname', host.hostname],
            ['Platform', host.platform],
            ['Python', host.python],
            ['CPU cores', host.cpu_count],
            ['CPU load', host.cpu_percent === null || host.cpu_percent === undefined
                ? 'unavailable' : host.cpu_percent + '%'],
            ['Load average', host.load_average ? host.load_average.join(', ') : 'unavailable'],
            ['Memory', host.memory ? host.memory.used_human + ' of ' + host.memory.total_human +
                ' (' + host.memory.percent + '%)' : 'unavailable'],
            ['Process memory', host.process_memory_human || 'unavailable'],
            ['Threads', host.threads === null || host.threads === undefined ? 'unavailable' : host.threads],
            ['Process id', host.pid]
        ]));

        grid.appendChild(definitionCard('Application', [
            ['Version', app.version],
            ['Uptime', uptime.process_human],
            ['Host uptime', uptime.host_human],
            ['Bind address', app.bind],
            ['Config file', app.config_path],
            ['Working directory', app.working_directory],
            ['Debug mode', app.debug ? 'ON - not for production' : 'off'],
            ['Analytics', app.analytics_enabled ? 'enabled' : 'disabled'],
            ['Email notifications', app.email_enabled ? 'enabled' : 'disabled'],
            ['Log directory', app.log_directory],
            ['Blueprints', (app.blueprints || []).join(', ')],
            ['Routes', app.route_count]
        ]));

        var storage = payload.storage || {};
        grid.appendChild(definitionCard('Analytics storage', [
            ['Database', storage.path],
            ['Size', storage.size_bytes ? (storage.size_bytes / 1048576).toFixed(2) + ' MB' : '0 MB'],
            ['Events', number(storage.analytics_events)],
            ['Sessions', number(storage.analytics_sessions)],
            ['Feedback entries', number(storage.feedback_submissions)],
            ['First event', storage.first_event_at || '-'],
            ['Latest event', storage.last_event_at || '-']
        ]));

        var dependencies = el('div', 'admin-card');
        dependencies.appendChild(el('h2', null, 'Dependencies'));
        var depTable = el('table', 'admin-table');
        renderTable(depTable, [
            { label: 'Service', get: function (r) { return r.name; } },
            { label: 'State', cell: function (r) {
                return badge(r.healthy ? 'reachable' : 'unreachable', r.healthy ? 'ok' : 'error');
            } },
            { label: 'Detail', className: 'is-wrap', get: function (r) { return r.detail; } },
            { label: 'Checked in', get: function (r) { return r.checked_in_ms + ' ms'; } }
        ], payload.dependencies, 'No dependency checks configured.');
        dependencies.appendChild(depTable);
        grid.appendChild(dependencies);

        var disks = el('div', 'admin-card');
        disks.appendChild(el('h2', null, 'Disk usage'));
        (payload.disks || []).forEach(function (disk) {
            var row = el('div');
            row.style.marginBottom = '0.75rem';
            row.appendChild(el('div', 'admin-mono', disk.path));
            row.appendChild(el('div', 'admin-kpi-note',
                disk.free_human + ' free of ' + disk.total_human + ' (' + disk.percent + '% used)'));
            row.appendChild(meter(disk.percent));
            disks.appendChild(row);
        });
        grid.appendChild(disks);

        var catalog = el('div', 'admin-card');
        catalog.appendChild(el('h2', null, 'Catalog services'));
        var catalogTable = el('table', 'admin-table');
        renderTable(catalogTable, [
            { label: 'Service', get: function (r) { return r.name; } },
            { label: 'State', cell: function (r) { return badge(r.state, r.state === 'active' ? 'ok' : 'muted'); } },
            { label: 'Hosted', get: function (r) { return r.internal ? 'in this process' : 'separate service'; } },
            { label: 'Address', className: 'admin-mono is-wrap', get: function (r) { return r.href; } }
        ], payload.catalog, 'No catalog entries.');
        catalog.appendChild(catalogTable);
        grid.appendChild(catalog);

        renderTable(byId('routes-table'), [
            { label: 'Route', className: 'admin-mono', get: function (r) { return r; } }
        ], app.routes, 'No routes registered.');
    }

    // -- feedback ----------------------------------------------------------
    function renderFeedback(payload) {
        renderTable(byId('feedback-table'), [
            { label: 'Reference', get: function (r) { return '#' + r.id; } },
            { label: 'Received', get: function (r) { return r.created_at; } },
            { label: 'Type', get: function (r) { return String(r.kind || '').replace('_', ' '); } },
            { label: 'Service', get: function (r) { return r.tool_name; } },
            { label: 'Name', get: function (r) { return r.name; } },
            { label: 'Email', get: function (r) { return r.email; } },
            { label: 'Message', className: 'is-wrap', get: function (r) { return r.message; } },
            { label: 'Acknowledgement', get: function (r) { return r.acknowledgement_email_status; } }
        ], payload.feedback, 'No feedback has been submitted yet.');
    }

    // -- loading -----------------------------------------------------------
    function analyticsQuery() {
        return '?window=' + encodeURIComponent(state.window) + '&months=' + encodeURIComponent(state.months);
    }

    function loadAnalytics() {
        return fetchJson('/admin/api/overview' + analyticsQuery())
            .then(function (report) {
                showError('');
                renderOverview(report);
                renderServices(report);
                renderVisitors(report);
                var link = byId('export-link');
                if (link) { link.href = '/admin/api/export' + analyticsQuery(); }
            })
            .catch(function (error) { showError('Could not load analytics: ' + error.message); });
    }

    function loadLive() {
        return fetchJson('/admin/api/live')
            .then(function (snapshot) { renderLive(snapshot); })
            .catch(function (error) { showError('Could not load live activity: ' + error.message); });
    }

    function loadLogs() {
        var query = '?level=' + encodeURIComponent(byId('log-level').value) +
            '&search=' + encodeURIComponent(byId('log-search').value) +
            '&limit=' + encodeURIComponent(byId('log-limit').value);
        return fetchJson('/admin/api/logs' + query)
            .then(function (payload) { renderLogs(payload); })
            .catch(function (error) { showError('Could not load logs: ' + error.message); });
    }

    function loadDiagnostics() {
        return fetchJson('/admin/api/diagnostics')
            .then(function (payload) { renderDiagnostics(payload); })
            .catch(function (error) { showError('Could not load diagnostics: ' + error.message); });
    }

    function loadFeedback() {
        return fetchJson('/admin/api/feedback')
            .then(function (payload) { renderFeedback(payload); })
            .catch(function (error) { showError('Could not load feedback: ' + error.message); });
    }

    function loadPanel(panel) {
        if (panel === 'logs') { return loadLogs(); }
        if (panel === 'diagnostics') { return loadDiagnostics(); }
        if (panel === 'feedback') { return loadFeedback(); }
        if (panel === 'live') { return loadLive(); }
        return loadAnalytics();
    }

    // -- wiring ------------------------------------------------------------
    function selectPanel(name) {
        state.activePanel = name;
        document.querySelectorAll('.admin-tab').forEach(function (tab) {
            tab.setAttribute('aria-selected', String(tab.dataset.panel === name));
        });
        document.querySelectorAll('.admin-panel').forEach(function (panel) {
            panel.hidden = panel.id !== 'panel-' + name;
        });
        loadPanel(name);
    }

    function startTimers() {
        stopTimers();
        if (!state.autoRefresh) { return; }
        // The live panel is the only thing that changes second to second, so it
        // polls often and everything else stays on a lazy minute timer.
        state.timers.live = window.setInterval(loadLive, LIVE_REFRESH_MS);
        state.timers.analytics = window.setInterval(function () {
            if (state.activePanel === 'logs') { loadLogs(); } else { loadAnalytics(); }
        }, ANALYTICS_REFRESH_MS);
    }

    function stopTimers() {
        Object.keys(state.timers).forEach(function (key) {
            window.clearInterval(state.timers[key]);
            delete state.timers[key];
        });
    }

    function init() {
        document.querySelectorAll('.admin-tab').forEach(function (tab) {
            tab.addEventListener('click', function () { selectPanel(tab.dataset.panel); });
        });

        byId('window-select').addEventListener('change', function (event) {
            state.window = event.target.value;
            loadAnalytics();
        });
        byId('months-select').addEventListener('change', function (event) {
            state.months = event.target.value;
            loadAnalytics();
        });
        byId('refresh-button').addEventListener('click', function () {
            loadLive();
            loadPanel(state.activePanel);
        });
        byId('autorefresh-toggle').addEventListener('change', function (event) {
            state.autoRefresh = event.target.checked;
            startTimers();
        });

        byId('log-refresh').addEventListener('click', loadLogs);
        byId('log-level').addEventListener('change', loadLogs);
        byId('log-limit').addEventListener('change', loadLogs);
        var searchTimer = null;
        byId('log-search').addEventListener('input', function () {
            window.clearTimeout(searchTimer);
            searchTimer = window.setTimeout(loadLogs, 350);
        });

        byId('metrics-button').addEventListener('click', function () {
            fetchJson('/admin/api/metrics').then(function (payload) {
                var pre = byId('metrics-pre');
                pre.textContent = payload.metrics;
                pre.hidden = false;
            }).catch(function (error) { showError('Could not load metrics: ' + error.message); });
        });

        state.window = byId('window-select').value;
        state.months = byId('months-select').value;
        selectPanel('overview');
        loadLive();
        startTimers();

        // Polling a hidden tab wastes server time and the operator's battery.
        document.addEventListener('visibilitychange', function () {
            if (document.hidden) { stopTimers(); } else { startTimers(); loadLive(); }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
}());
