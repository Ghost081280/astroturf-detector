/**
 * ASTROTURF DETECTOR - Frontend Application
 * United States Monitor
 */

(function() {
    'use strict';

    const CONFIG = { dataPath: 'data/', refreshInterval: 300000 };
    const state = { memory: null, alerts: [], lastScan: null };

    async function loadData() {
        try {
            const [memory, alerts] = await Promise.all([
                fetchJSON('memory.json'),
                fetchJSON('alerts.json')
            ]);
            state.memory = memory;
            state.alerts = alerts.alerts || [];
            state.lastScan = memory.lastScan;
            renderAll();
        } catch (error) {
            console.error('Error loading data:', error);
        }
    }

    async function fetchJSON(filename) {
        const response = await fetch(CONFIG.dataPath + filename);
        if (!response.ok) throw new Error(`Failed to load ${filename}`);
        return response.json();
    }

    function renderAll() {
        renderStats();
        renderLastScan();
        renderOrganizations();
        renderConfidence();
        renderGeographicHotspots();
        renderDataSources();
        renderNews();
        renderAlerts();
    }

    function renderStats() {
        const stats = state.memory?.stats || {};
        animateCounter('stat-events', stats.events || 0);
        animateCounter('stat-alerts', stats.alerts || 0);
        animateCounter('stat-orgs', stats.orgs || 0);
        animateCounter('stat-news', stats.newsArticles || 0);
    }

    function animateCounter(id, target) {
        const el = document.getElementById(id);
        if (!el) return;
        const duration = 400, start = performance.now();
        function update(now) {
            const progress = Math.min((now - start) / duration, 1);
            el.textContent = Math.floor(target * progress);
            if (progress < 1) requestAnimationFrame(update);
        }
        requestAnimationFrame(update);
    }

    function renderLastScan() {
        const el = document.getElementById('last-scan-time');
        if (!el || !state.lastScan) return;
        el.textContent = formatRelativeTime(state.lastScan);
    }

    function renderOrganizations() {
        const container = document.getElementById('org-list');
        if (!container) return;

        const orgs = state.memory?.flaggedOrganizations || [];
        
        if (orgs.length === 0) {
            container.innerHTML = '<div class="loading-indicator"><span>No flagged organizations yet</span></div>';
            return;
        }

        container.innerHTML = orgs.slice(0, 12).map(org => `
            <a href="${escapeHtml(org.sourceUrl || 'https://projects.propublica.org/nonprofits/')}" target="_blank" rel="noopener" class="org-item">
                <div class="org-indicator ${getSeverityClass(org.risk_score || 0)}"></div>
                <div class="org-details">
                    <div class="org-name">${escapeHtml(org.name)}</div>
                    <div class="org-meta">${escapeHtml(org.state || 'US')} • ${escapeHtml(org.city || 'Unknown')}</div>
                </div>
                <div class="org-score">${org.risk_score || 0}%</div>
                <span class="org-link-icon">↗</span>
            </a>
        `).join('');
    }

    function renderConfidence() {
        const arc = document.getElementById('confidence-arc');
        const percent = document.getElementById('confidence-percent');
        const desc = document.getElementById('confidence-desc');
        const factorsContainer = document.getElementById('confidence-factors');
        
        if (!arc || !percent) return;

        const confidence = state.memory?.systemConfidence || 0;
        const factors = state.memory?.confidenceFactors || [];
        const circumference = 2 * Math.PI * 45;
        const dashLength = (confidence / 100) * circumference;

        arc.style.strokeDasharray = `${dashLength} ${circumference}`;
        percent.textContent = `${confidence}%`;

        if (desc) {
            const notes = state.memory?.agentNotes || [];
            const summary = notes.length > 0 ? notes[0].summary : '';
            desc.textContent = summary || (confidence >= 70 
                ? 'High confidence - multiple indicators detected.'
                : confidence >= 40 
                    ? 'Moderate confidence - some patterns present.'
                    : 'Low confidence - gathering data.');
        }

        if (factorsContainer) {
            if (factors.length > 0) {
                factorsContainer.innerHTML = factors.slice(0, 4).map(f => `
                    <div class="confidence-factor">
                        <span class="factor-name">${escapeHtml(f.factor)}</span>
                        <span class="factor-score">${f.score}%</span>
                    </div>
                `).join('');
            } else {
                factorsContainer.innerHTML = `
                    <div class="confidence-factor">
                        <span class="factor-name">Data Freshness</span>
                        <span class="factor-score">Real-time</span>
                    </div>
                    <div class="confidence-factor">
                        <span class="factor-name">Sources Active</span>
                        <span class="factor-score">3/3</span>
                    </div>
                `;
            }
        }
    }

    function renderGeographicHotspots() {
        const container = document.getElementById('geo-hotspots');
        if (!container) return;

        const orgs = state.memory?.flaggedOrganizations || [];
        const stateCounts = {};
        orgs.forEach(org => {
            const st = org.state;
            if (st) stateCounts[st] = (stateCounts[st] || 0) + 1;
        });

        const sorted = Object.entries(stateCounts).sort((a, b) => b[1] - a[1]);

        if (sorted.length === 0) {
            container.innerHTML = '<div class="loading-indicator"><span>Run a scan to see geographic data</span></div>';
            return;
        }

        container.innerHTML = sorted.slice(0, 10).map(([st, count]) => `
            <div class="geo-state">
                <span class="state-abbr">${escapeHtml(st)}</span>
                <span class="state-count">${count} org${count > 1 ? 's' : ''}</span>
            </div>
        `).join('');
    }

    function renderDataSources() {
        const container = document.getElementById('data-sources');
        if (!container) return;

        const sources = state.memory?.dataSources || {};
        const sourceList = [
            { key: 'propublica', name: 'ProPublica Nonprofit Explorer', url: 'https://projects.propublica.org/nonprofits/', desc: '501(c)(4) tax filings' },
            { key: 'fec', name: 'FEC Campaign Finance', url: 'https://www.fec.gov/', desc: 'Independent expenditures' },
            { key: 'googleNews', name: 'Google News RSS', url: 'https://news.google.com/', desc: 'Real-time news' }
        ];

        container.innerHTML = sourceList.map(src => {
            const data = sources[src.key] || {};
            const isActive = data.status === 'active';
            const lastCall = data.lastCall ? formatRelativeTime(data.lastCall) : 'Never';
            return `
                <a href="${src.url}" target="_blank" rel="noopener" class="data-source-item">
                    <div class="source-info">
                        <div class="source-status ${isActive ? 'active' : 'inactive'}"></div>
                        <div>
                            <div class="source-name">${src.name}</div>
                            <div class="source-desc">${src.desc}</div>
                        </div>
                    </div>
                    <div class="source-time">${lastCall}</div>
                </a>
            `;
        }).join('');
    }

    function renderNews() {
        const container = document.getElementById('news-feed');
        if (!container) return;

        const news = state.memory?.recentNews || [];
        
        if (news.length === 0) {
            container.innerHTML = '<div class="loading-indicator"><span>No news articles yet - run a scan</span></div>';
            return;
        }

        container.innerHTML = news.slice(0, 12).map(article => `
            <a href="${escapeHtml(article.url || '#')}" target="_blank" rel="noopener" class="news-item">
                <div class="news-title">${escapeHtml(article.title || 'Untitled')}</div>
                <div class="news-meta">
                    <span class="news-publisher">${escapeHtml(article.publisher || 'Unknown')}</span>
                    <span class="news-date">${formatRelativeTime(article.date)}</span>
                </div>
                ${article.location ? `<span class="news-location">📍 ${escapeHtml(article.location)}</span>` : ''}
            </a>
        `).join('');
    }

    function renderAlerts() {
        const container = document.getElementById('alerts-grid');
        if (!container) return;

        const alerts = state.alerts;
        
        if (alerts.length === 0) {
            container.innerHTML = '<div class="loading-indicator"><span>No active alerts</span></div>';
            return;
        }

        container.innerHTML = alerts.slice(0, 6).map(alert => `
            <div class="alert-card">
                <div class="alert-header">
                    <div class="alert-severity ${alert.severity || 'medium'}"></div>
                    <div class="alert-title">${escapeHtml(alert.title)}</div>
                    <div class="alert-time">${formatRelativeTime(alert.timestamp)}</div>
                </div>
                <div class="alert-body">
                    <p class="alert-description">${escapeHtml(alert.description)}</p>
                    <div class="alert-factors">
                        ${(alert.factors || []).map(f => `
                            <div class="alert-factor">
                                <svg class="factor-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="20 6 9 17 4 12"/>
                                </svg>
                                <span class="factor-label">${escapeHtml(f.name)}</span>
                                <span class="factor-value">${escapeHtml(String(f.value))}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="alert-footer">
                    <span class="alert-confidence">Confidence: <span>${alert.confidence || 0}%</span></span>
                    <div class="alert-sources">
                        ${(alert.sources || []).slice(0, 2).map(src => `
                            <a href="${escapeHtml(src)}" target="_blank" rel="noopener" class="alert-source-link">Source ↗</a>
                        `).join('')}
                    </div>
                </div>
            </div>
        `).join('');
    }

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function formatRelativeTime(timestamp) {
        if (!timestamp) return 'Unknown';
        const now = new Date();
        const date = new Date(timestamp);
        const diff = now - date;
        const mins = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);
        if (mins < 1) return 'Just now';
        if (mins < 60) return `${mins}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }

    function getSeverityClass(score) {
        if (score >= 70) return 'high';
        if (score >= 40) return 'medium';
        return 'low';
    }

    function init() {
        loadData();
        setInterval(loadData, CONFIG.refreshInterval);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
