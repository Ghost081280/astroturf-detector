/**
 * ASTROTURF DETECTOR - Frontend Application
 */

(function() {
    'use strict';

    const CONFIG = {
        dataPath: 'data/',
        refreshInterval: 300000,
        animationDuration: 400
    };

    const state = {
        memory: null,
        alerts: [],
        timeline: [],
        stats: { events: 0, alerts: 0, orgs: 0 },
        filters: { timeRange: 365, showJobs: true, showOrgs: true, showEvents: true },
        lastScan: null
    };

    // ============================================
    // DATA LOADING
    // ============================================

    async function loadData() {
        try {
            const [memory, alerts] = await Promise.all([
                fetchJSON('memory.json'),
                fetchJSON('alerts.json')
            ]);

            state.memory = memory;
            state.alerts = alerts.alerts || [];
            state.timeline = memory.timeline || [];
            state.stats = memory.stats || state.stats;
            state.lastScan = memory.lastScan || new Date().toISOString();

            renderAll();
        } catch (error) {
            console.error('Error loading data:', error);
            renderEmptyStates();
        }
    }

    async function fetchJSON(filename) {
        const response = await fetch(CONFIG.dataPath + filename);
        if (!response.ok) throw new Error(`Failed to load ${filename}`);
        return response.json();
    }

    // ============================================
    // RENDERING FUNCTIONS
    // ============================================

    function renderAll() {
        renderStats();
        renderGeographicActivity();
        renderJobMonitor();
        renderOrganizations();
        renderTimeline();
        renderAlerts();
        renderConfidence();
        updateLastScanTime();
    }

    function renderStats() {
        animateCounter('stat-events', state.stats.events || 0);
        animateCounter('stat-alerts', state.stats.alerts || 0);
        animateCounter('stat-orgs', state.stats.orgs || 0);
    }

    function animateCounter(elementId, targetValue) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const duration = CONFIG.animationDuration;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = easeOutQuart(progress);
            const current = Math.floor(targetValue * eased);
            element.textContent = formatNumber(current);
            if (progress < 1) requestAnimationFrame(update);
        }
        requestAnimationFrame(update);
    }

    function renderGeographicActivity() {
        const container = document.getElementById('activity-map');
        if (!container) return;

        const cities = state.memory?.jobPostingPatterns?.cities || {};
        const cityList = Object.entries(cities).filter(([name]) => name !== 'Unknown');

        if (cityList.length === 0) {
            container.innerHTML = `
                <div class="map-placeholder">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
                        <circle cx="12" cy="9" r="2.5"/>
                    </svg>
                    <span>No geographic data yet</span>
                </div>
            `;
            return;
        }

        const maxCount = Math.max(...cityList.map(([, count]) => count));
        
        container.innerHTML = `
            <div class="geo-grid">
                ${cityList.sort((a, b) => b[1] - a[1]).map(([city, count]) => {
                    const intensity = Math.round((count / maxCount) * 100);
                    return `
                        <div class="geo-item">
                            <div class="geo-bar" style="width: ${intensity}%"></div>
                            <span class="geo-city">${escapeHtml(city)}</span>
                            <span class="geo-count">${count}</span>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    function renderJobMonitor() {
        const container = document.getElementById('job-chart');
        if (!container) return;

        const keywords = state.memory?.jobPostingPatterns?.keywords || {};
        const keywordList = Object.entries(keywords);

        if (keywordList.length === 0) {
            container.innerHTML = `
                <div class="chart-placeholder">
                    <span>No job posting data yet</span>
                </div>
            `;
            document.getElementById('job-count').textContent = '0';
            document.getElementById('job-trend').textContent = '--';
            return;
        }

        const total = keywordList.reduce((sum, [, count]) => sum + count, 0);
        const maxCount = Math.max(...keywordList.map(([, count]) => count));

        container.innerHTML = `
            <div class="keyword-chart">
                ${keywordList.sort((a, b) => b[1] - a[1]).slice(0, 6).map(([keyword, count]) => {
                    const width = Math.round((count / maxCount) * 100);
                    return `
                        <div class="keyword-row">
                            <span class="keyword-name">${escapeHtml(keyword)}</span>
                            <div class="keyword-bar-container">
                                <div class="keyword-bar" style="width: ${width}%"></div>
                            </div>
                            <span class="keyword-count">${count}</span>
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        document.getElementById('job-count').textContent = formatNumber(total);
        document.getElementById('job-trend').textContent = '+' + formatNumber(total);
    }

    function renderOrganizations() {
        const container = document.getElementById('org-list');
        if (!container) return;

        const orgs = state.memory?.flaggedOrganizations || [];
        const knownPatterns = state.memory?.knownAstroturfPatterns?.threeWordNames || [];

        // If no flagged orgs, show known patterns as watchlist
        const displayList = orgs.length > 0 ? orgs : knownPatterns.map((name, i) => ({
            name: name,
            state: 'TX',
            type: 'Watchlist',
            riskScore: 75
        }));

        if (displayList.length === 0) {
            container.innerHTML = `
                <div class="loading-indicator">
                    <span>No flagged organizations detected</span>
                </div>
            `;
            return;
        }

        container.innerHTML = displayList.slice(0, 8).map(org => `
            <div class="org-item">
                <div class="org-indicator ${getSeverityClass(org.riskScore || 50)}"></div>
                <div class="org-details">
                    <div class="org-name">${escapeHtml(org.name)}</div>
                    <div class="org-meta">${escapeHtml(org.state || 'Unknown')} | ${escapeHtml(org.type || '501(c)(4)')}</div>
                </div>
                <div class="org-score">${org.riskScore || 50}%</div>
            </div>
        `).join('');
    }

    function renderTimeline() {
        const container = document.getElementById('timeline-events');
        const chartContainer = document.getElementById('timeline-chart');
        if (!container) return;

        const events = filterTimelineEvents();

        if (events.length === 0) {
            container.innerHTML = `
                <div class="loading-indicator">
                    <span>No events in selected time range</span>
                </div>
            `;
            if (chartContainer) {
                chartContainer.parentElement.innerHTML = `
                    <div class="chart-placeholder">
                        <span>No timeline data to display</span>
                    </div>
                `;
            }
            return;
        }

        container.innerHTML = events.slice(0, 10).map(event => {
            const date = new Date(event.date);
            return `
                <div class="timeline-event">
                    <div class="event-date">
                        <span class="event-day">${date.getDate()}</span>
                        <span class="event-month">${getMonthAbbr(date.getMonth())}</span>
                    </div>
                    <div class="event-content">
                        <div class="event-title">${escapeHtml(event.title)}</div>
                        <div class="event-description">${escapeHtml(event.description)}</div>
                        <div class="event-tags">
                            ${(event.tags || []).map(tag => `<span class="event-tag">${escapeHtml(tag)}</span>`).join('')}
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        renderTimelineChart(events);
    }

    function renderTimelineChart(events) {
        const canvas = document.getElementById('timeline-chart');
        if (!canvas || !canvas.getContext) return;

        const ctx = canvas.getContext('2d');
        const rect = canvas.parentElement.getBoundingClientRect();
        
        canvas.width = rect.width - 32;
        canvas.height = rect.height - 32;

        const grouped = groupEventsByDate(events);
        const dates = Object.keys(grouped).sort();
        const maxCount = Math.max(...Object.values(grouped).map(g => g.total), 1);

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (dates.length === 0) return;

        const padding = 20;
        const chartWidth = canvas.width - padding * 2;
        const chartHeight = canvas.height - padding * 2;
        const barWidth = Math.max(Math.min(chartWidth / dates.length - 4, 30), 8);

        dates.forEach((date, index) => {
            const x = padding + (chartWidth / dates.length) * index + (chartWidth / dates.length - barWidth) / 2;
            const data = grouped[date];
            let yOffset = canvas.height - padding;

            if (state.filters.showJobs && data.jobs > 0) {
                const height = (data.jobs / maxCount) * chartHeight;
                ctx.fillStyle = '#3b82f6';
                ctx.fillRect(x, yOffset - height, barWidth, height);
                yOffset -= height;
            }

            if (state.filters.showOrgs && data.orgs > 0) {
                const height = (data.orgs / maxCount) * chartHeight;
                ctx.fillStyle = '#eab308';
                ctx.fillRect(x, yOffset - height, barWidth, height);
                yOffset -= height;
            }

            if (state.filters.showEvents && data.events > 0) {
                const height = (data.events / maxCount) * chartHeight;
                ctx.fillStyle = '#ef4444';
                ctx.fillRect(x, yOffset - height, barWidth, height);
            }
        });
    }

    function renderAlerts() {
        const container = document.getElementById('alerts-grid');
        if (!container) return;

        const alerts = state.alerts;

        if (alerts.length === 0) {
            container.innerHTML = `
                <div class="loading-indicator">
                    <span>No active alerts</span>
                </div>
            `;
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
                        ${(alert.factors || []).map(factor => `
                            <div class="alert-factor">
                                <svg class="factor-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="20 6 9 17 4 12"/>
                                </svg>
                                <span class="factor-label">${escapeHtml(factor.name)}</span>
                                <span class="factor-value">${escapeHtml(String(factor.value))}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="alert-footer">
                    <span class="alert-confidence">Confidence: <span>${alert.confidence || 0}%</span></span>
                    ${alert.link ? `<a href="${escapeHtml(alert.link)}" class="alert-link" target="_blank" rel="noopener">View Source</a>` : ''}
                </div>
            </div>
        `).join('');
    }

    function renderConfidence() {
        const arc = document.getElementById('confidence-arc');
        const percent = document.getElementById('confidence-percent');
        const desc = document.getElementById('confidence-desc');
        
        if (!arc || !percent) return;

        const confidence = state.memory?.systemConfidence || 0;
        const circumference = 2 * Math.PI * 45;
        const dashLength = (confidence / 100) * circumference;

        arc.style.strokeDasharray = `${dashLength} ${circumference}`;
        percent.textContent = `${confidence}%`;

        if (desc) {
            if (confidence >= 70) {
                desc.textContent = 'High confidence in current detections. Patterns are consistent with known astroturf activity.';
            } else if (confidence >= 40) {
                desc.textContent = 'Moderate confidence. Some indicators present but patterns are not definitive.';
            } else {
                desc.textContent = 'Low confidence. Insufficient data or unclear patterns detected.';
            }
        }
    }

    function updateLastScanTime() {
        const element = document.getElementById('last-scan-time');
        if (!element || !state.lastScan) return;
        element.textContent = formatRelativeTime(state.lastScan);
    }

    function renderEmptyStates() {
        const els = ['stat-events', 'stat-alerts', 'stat-orgs'];
        els.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.textContent = '0';
        });
        const confEl = document.getElementById('confidence-percent');
        if (confEl) confEl.textContent = '--';
    }

    // ============================================
    // FILTERING
    // ============================================

    function filterTimelineEvents() {
        const now = new Date();
        const cutoff = new Date(now - state.filters.timeRange * 24 * 60 * 60 * 1000);
        
        return state.timeline.filter(event => {
            const eventDate = new Date(event.date);
            if (eventDate < cutoff) return false;
            if (event.type === 'job' && !state.filters.showJobs) return false;
            if (event.type === 'org' && !state.filters.showOrgs) return false;
            if (event.type === 'event' && !state.filters.showEvents) return false;
            return true;
        });
    }

    function groupEventsByDate(events) {
        const grouped = {};
        events.forEach(event => {
            const dateKey = event.date.split('T')[0];
            if (!grouped[dateKey]) {
                grouped[dateKey] = { jobs: 0, orgs: 0, events: 0, total: 0 };
            }
            if (event.type === 'job') grouped[dateKey].jobs++;
            else if (event.type === 'org') grouped[dateKey].orgs++;
            else grouped[dateKey].events++;
            grouped[dateKey].total++;
        });
        return grouped;
    }

    // ============================================
    // EVENT HANDLERS
    // ============================================

    function setupEventListeners() {
        document.querySelectorAll('.range-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                state.filters.timeRange = parseInt(btn.dataset.range, 10);
                renderTimeline();
            });
        });

        // Set 1 Year as default active
        const yearBtn = document.querySelector('.range-btn[data-range="365"]');
        if (yearBtn) {
            document.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
            yearBtn.classList.add('active');
        }

        document.getElementById('filter-jobs')?.addEventListener('change', (e) => {
            state.filters.showJobs = e.target.checked;
            renderTimeline();
        });

        document.getElementById('filter-orgs')?.addEventListener('change', (e) => {
            state.filters.showOrgs = e.target.checked;
            renderTimeline();
        });

        document.getElementById('filter-events')?.addEventListener('change', (e) => {
            state.filters.showEvents = e.target.checked;
            renderTimeline();
        });

        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        });

        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                const events = filterTimelineEvents();
                renderTimelineChart(events);
            }, 250);
        });
    }

    // ============================================
    // UTILITY FUNCTIONS
    // ============================================

    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function formatNumber(num) {
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }

    function formatRelativeTime(timestamp) {
        const now = new Date();
        const date = new Date(timestamp);
        const diff = now - date;
        
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }

    function getMonthAbbr(month) {
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        return months[month];
    }

    function getSeverityClass(score) {
        if (score >= 70) return 'high';
        if (score >= 40) return 'medium';
        return 'low';
    }

    function easeOutQuart(x) {
        return 1 - Math.pow(1 - x, 4);
    }

    // ============================================
    // INITIALIZATION
    // ============================================

    function init() {
        setupEventListeners();
        loadData();
        setInterval(loadData, CONFIG.refreshInterval);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
