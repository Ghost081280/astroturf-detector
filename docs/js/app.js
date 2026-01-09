/**
 * ASTROTURF DETECTOR - Frontend Application
 * United States Monitor
 */

(function() {
    'use strict';

    const CONFIG = {
        dataPath: 'data/',
        refreshInterval: 300000, // 5 minutes
        defaultTimeRange: 365
    };

    const state = {
        memory: null,
        alerts: [],
        timeRange: CONFIG.defaultTimeRange,
        filters: {
            jobs: true,
            orgs: true,
            events: true
        }
    };

    // Initialize
    async function init() {
        await loadData();
        setupEventListeners();
        setInterval(loadData, CONFIG.refreshInterval);
    }

    // Load data from JSON files
    async function loadData() {
        try {
            const [memoryRes, alertsRes] = await Promise.all([
                fetch(CONFIG.dataPath + 'memory.json'),
                fetch(CONFIG.dataPath + 'alerts.json')
            ]);

            if (memoryRes.ok) {
                state.memory = await memoryRes.json();
            }
            if (alertsRes.ok) {
                const alertsData = await alertsRes.json();
                state.alerts = alertsData.alerts || [];
            }

            renderAll();
        } catch (error) {
            console.error('Error loading data:', error);
        }
    }

    // Render all components
    function renderAll() {
        renderStats();
        renderLastScan();
        renderGeographicActivity();
        renderJobMonitor();
        renderOrganizations();
        renderConfidence();
        renderTimeline();
        renderAlerts();
    }

    // Render hero stats
    function renderStats() {
        const stats = state.memory?.stats || {};
        
        animateCounter('stat-events', stats.events || 0);
        animateCounter('stat-alerts', stats.alerts || 0);
        animateCounter('stat-orgs', stats.orgs || 0);
        animateCounter('stat-news', stats.newsArticles || 0);
    }

    // Animate counter
    function animateCounter(id, target) {
        const el = document.getElementById(id);
        if (!el) return;

        const duration = 1000;
        const start = performance.now();
        const startVal = parseInt(el.textContent) || 0;

        function update(currentTime) {
            const elapsed = currentTime - start;
            const progress = Math.min(elapsed / duration, 1);
            const easeProgress = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(startVal + (target - startVal) * easeProgress);
            el.textContent = current;

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }

        requestAnimationFrame(update);
    }

    // Render last scan time
    function renderLastScan() {
        const el = document.getElementById('last-scan-time');
        if (!el) return;

        const lastScan = state.memory?.lastScan;
        if (lastScan) {
            el.textContent = formatRelativeTime(lastScan);
        } else {
            el.textContent = 'Never';
        }
    }

    // Render geographic activity
    function renderGeographicActivity() {
        const container = document.getElementById('activity-map');
        if (!container) return;

        // Get geographic data from flagged organizations
        const orgs = state.memory?.flaggedOrganizations || [];
        const stateCounts = {};

        orgs.forEach(org => {
            const st = org.state;
            if (st) {
                stateCounts[st] = (stateCounts[st] || 0) + 1;
            }
        });

        // Also check jobPostingPatterns for cities
        const jobPatterns = state.memory?.jobPostingPatterns || {};
        const cities = jobPatterns.cities || {};

        // Combine into display data
        const hasStateData = Object.keys(stateCounts).length > 0;
        const hasCityData = Object.keys(cities).length > 0;

        if (!hasStateData && !hasCityData) {
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

        // Build display - prefer cities if available, otherwise states
        let displayData = [];
        
        if (hasCityData) {
            displayData = Object.entries(cities)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10);
        } else {
            displayData = Object.entries(stateCounts)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10);
        }

        const maxCount = Math.max(...displayData.map(d => d[1]));

        container.innerHTML = `
            <div class="geo-grid">
                ${displayData.map(([location, count]) => `
                    <div class="geo-item">
                        <div class="geo-bar" style="width: ${(count / maxCount) * 100}%"></div>
                        <span class="geo-city">${escapeHtml(location)}</span>
                        <span class="geo-count">${count}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // Render job monitor
    function renderJobMonitor() {
        const chartContainer = document.getElementById('job-chart');
        const countEl = document.getElementById('job-count');
        const trendEl = document.getElementById('job-trend');

        if (!chartContainer) return;

        const jobPatterns = state.memory?.jobPostingPatterns || {};
        const keywords = jobPatterns.keywords || {};
        const totalJobs = jobPatterns.totalJobs || 0;

        // Update metrics
        if (countEl) countEl.textContent = totalJobs;
        if (trendEl) {
            const trend = jobPatterns.weekOverWeekChange || 0;
            trendEl.textContent = trend >= 0 ? `+${trend}%` : `${trend}%`;
            trendEl.style.color = trend >= 0 ? 'var(--color-danger)' : 'var(--color-success)';
        }

        // Render keyword chart
        const keywordEntries = Object.entries(keywords).sort((a, b) => b[1] - a[1]).slice(0, 6);

        if (keywordEntries.length === 0) {
            chartContainer.innerHTML = `
                <div class="chart-placeholder">
                    <span>No job posting data yet</span>
                </div>
            `;
            return;
        }

        const maxKeywordCount = Math.max(...keywordEntries.map(k => k[1]));

        chartContainer.innerHTML = `
            <div class="keyword-chart">
                ${keywordEntries.map(([keyword, count]) => `
                    <div class="keyword-row">
                        <span class="keyword-name">${escapeHtml(keyword)}</span>
                        <div class="keyword-bar-container">
                            <div class="keyword-bar" style="width: ${(count / maxKeywordCount) * 100}%"></div>
                        </div>
                        <span class="keyword-count">${count}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // Render organizations
    function renderOrganizations() {
        const container = document.getElementById('org-list');
        if (!container) return;

        const orgs = state.memory?.flaggedOrganizations || [];

        if (orgs.length === 0) {
            // Check for watchlist patterns
            const watchlist = state.memory?.knownAstroturfPatterns?.threeWordNames || [];
            if (watchlist.length > 0) {
                container.innerHTML = watchlist.slice(0, 8).map(name => `
                    <div class="org-item">
                        <div class="org-indicator medium"></div>
                        <div class="org-details">
                            <div class="org-name">${escapeHtml(name)}</div>
                            <div class="org-meta">Watchlist Pattern</div>
                        </div>
                        <div class="org-score">--</div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = `
                    <div class="loading-indicator">
                        <span>No organizations flagged yet</span>
                    </div>
                `;
            }
            return;
        }

        container.innerHTML = orgs.slice(0, 10).map(org => {
            const riskClass = getRiskClass(org.risk_score || 0);
            const sourceUrl = org.sourceUrl || `https://projects.propublica.org/nonprofits/organizations/${org.ein || ''}`;
            
            return `
                <a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noopener" class="org-item">
                    <div class="org-indicator ${riskClass}"></div>
                    <div class="org-details">
                        <div class="org-name">${escapeHtml(org.name)}</div>
                        <div class="org-meta">${escapeHtml(org.state || 'Unknown')} • ${escapeHtml(org.city || 'Unknown')}</div>
                    </div>
                    <div class="org-score">${org.risk_score || 0}%</div>
                    <span class="org-link-icon">↗</span>
                </a>
            `;
        }).join('');
    }

    // Render confidence meter
    function renderConfidence() {
        const percentEl = document.getElementById('confidence-percent');
        const descEl = document.getElementById('confidence-desc');
        const arcEl = document.getElementById('confidence-arc');
        const factorsEl = document.getElementById('confidence-factors');

        if (!percentEl || !arcEl) return;

        const confidence = state.memory?.systemConfidence || 0;
        const factors = state.memory?.confidenceFactors || [];

        // Update percentage
        percentEl.textContent = `${confidence}%`;

        // Update arc
        const circumference = 2 * Math.PI * 45;
        const dashLength = (confidence / 100) * circumference;
        arcEl.style.strokeDasharray = `${dashLength} ${circumference}`;

        // Update description
        if (descEl) {
            const notes = state.memory?.agentNotes || [];
            const latestNote = notes.length > 0 ? notes[0] : null;
            
            if (latestNote && latestNote.summary) {
                descEl.textContent = latestNote.summary;
            } else if (confidence >= 70) {
                descEl.textContent = 'High confidence in current detections. Multiple corroborating indicators found.';
            } else if (confidence >= 40) {
                descEl.textContent = 'Moderate confidence. Some patterns detected but more data needed.';
            } else {
                descEl.textContent = 'Low confidence. Insufficient data for reliable detection.';
            }
        }

        // Update factors
        if (factorsEl) {
            if (factors.length > 0) {
                factorsEl.innerHTML = factors.slice(0, 4).map(f => `
                    <div class="confidence-factor">
                        <span class="factor-name">${escapeHtml(f.factor)}</span>
                        <span class="factor-score">${f.score}%</span>
                    </div>
                `).join('');
            } else {
                factorsEl.innerHTML = '';
            }
        }
    }

    // Render timeline
    function renderTimeline() {
        const container = document.getElementById('timeline-events');
        if (!container) return;

        const timeline = state.memory?.timeline || [];
        const now = new Date();
        const cutoffDate = new Date(now.getTime() - (state.timeRange * 24 * 60 * 60 * 1000));

        // Filter by time range and type
        const filteredEvents = timeline.filter(event => {
            const eventDate = new Date(event.date);
            if (eventDate < cutoffDate) return false;

            if (event.type === 'job' && !state.filters.jobs) return false;
            if (event.type === 'org' && !state.filters.orgs) return false;
            if (event.type === 'event' && !state.filters.events) return false;
            if (event.type === 'news' && !state.filters.events) return false;

            return true;
        });

        if (filteredEvents.length === 0) {
            container.innerHTML = `
                <div class="loading-indicator">
                    <span>No events in selected time range</span>
                </div>
            `;
            return;
        }

        container.innerHTML = filteredEvents.slice(0, 20).map(event => {
            const date = new Date(event.date);
            const day = date.getDate();
            const month = date.toLocaleString('en-US', { month: 'short' });
            const sourceUrl = event.sourceUrl || '';

            return `
                <div class="timeline-event">
                    <div class="event-date">
                        <span class="event-day">${day}</span>
                        <span class="event-month">${month}</span>
                    </div>
                    <div class="event-content">
                        <div class="event-title">
                            ${escapeHtml(event.title)}
                            ${sourceUrl ? `<a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noopener" class="event-source-link">↗</a>` : ''}
                        </div>
                        <p class="event-description">${escapeHtml(event.description || '')}</p>
                        <div class="event-tags">
                            ${(event.tags || []).map(tag => `
                                <span class="event-tag">${escapeHtml(tag)}</span>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // Render alerts
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
                    <div class="alert-sources">
                        ${(alert.sources || []).slice(0, 2).map(src => `
                            <a href="${escapeHtml(src)}" target="_blank" rel="noopener" class="alert-source-link">Source ↗</a>
                        `).join('')}
                    </div>
                </div>
            </div>
        `).join('');
    }

    // Setup event listeners
    function setupEventListeners() {
        // Time range buttons
        document.querySelectorAll('.range-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                state.timeRange = parseInt(btn.dataset.range);
                renderTimeline();
            });
        });

        // Filter toggles
        const filterJobs = document.getElementById('filter-jobs');
        const filterOrgs = document.getElementById('filter-orgs');
        const filterEvents = document.getElementById('filter-events');

        if (filterJobs) {
            filterJobs.addEventListener('change', () => {
                state.filters.jobs = filterJobs.checked;
                renderTimeline();
            });
        }

        if (filterOrgs) {
            filterOrgs.addEventListener('change', () => {
                state.filters.orgs = filterOrgs.checked;
                renderTimeline();
            });
        }

        if (filterEvents) {
            filterEvents.addEventListener('change', () => {
                state.filters.events = filterEvents.checked;
                renderTimeline();
            });
        }
    }

    // Utility functions
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
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }

    function getRiskClass(score) {
        if (score >= 70) return 'high';
        if (score >= 40) return 'medium';
        return 'low';
    }

    // Start the app
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
