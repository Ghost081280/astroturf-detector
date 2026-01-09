// Astroturf Detector v2.0 - Frontend Application

const ALL_STATES = ['AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY','DC'];
const HIGH_ACTIVITY = ['TX','CA','FL','NY','PA','OH','GA','NC','MI','AZ','WA','CO','VA','NJ','IL','DC'];

let currentRange = 90;
let allTimelineEvents = [];

// Initialize states grid
function initStatesGrid() {
    const grid = document.getElementById('states-grid');
    if (grid) {
        grid.innerHTML = ALL_STATES.map(s => 
            '<div class="state-badge ' + (HIGH_ACTIVITY.includes(s) ? 'high-activity' : '') + '">' + s + '</div>'
        ).join('');
    }
}

// Parse date safely
function parseDate(d) {
    if (!d) return new Date(0);
    try {
        return new Date(d);
    } catch {
        return new Date(0);
    }
}

// Format relative time
function formatRelativeTime(d) {
    const now = new Date();
    const date = parseDate(d);
    const ms = now - date;
    const m = Math.floor(ms / 60000);
    const h = Math.floor(ms / 3600000);
    const dy = Math.floor(ms / 86400000);
    
    if (m < 1) return 'Just now';
    if (m < 60) return m + 'm ago';
    if (h < 24) return h + 'h ago';
    if (dy < 7) return dy + 'd ago';
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// Escape HTML to prevent XSS
function escapeHtml(s) {
    if (!s) return '';
    return s.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
}

// Render timeline with date filtering
function renderTimeline(days) {
    const container = document.getElementById('timeline-events');
    const badge = document.getElementById('timeline-count');
    
    if (!container || !badge) return;
    
    let filtered;
    if (days === 'all') {
        filtered = allTimelineEvents;
    } else {
        const cutoff = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
        filtered = allTimelineEvents.filter(e => {
            const eventDate = parseDate(e.date || e.timestamp);
            return eventDate >= cutoff;
        });
    }
    
    filtered.sort((a, b) => parseDate(b.date || b.timestamp) - parseDate(a.date || a.timestamp));
    badge.textContent = filtered.length + ' events';
    
    if (!filtered.length) {
        container.innerHTML = '<div class="empty-state"><p>No events in ' + 
            (days === 'all' ? 'timeline' : 'last ' + days + ' days') + '</p></div>';
        return;
    }
    
    container.innerHTML = filtered.slice(0, 20).map(e => {
        const d = parseDate(e.date || e.timestamp);
        const dayNum = d.getDate();
        const month = d.toLocaleString('en', { month: 'short' });
        const title = escapeHtml(e.title || 'Event');
        const desc = escapeHtml(e.description || '');
        const url = e.sourceUrl ? escapeHtml(e.sourceUrl) : '';
        const type = e.type || 'event';
        const tags = (e.tags || []).slice(0, 2);
        
        return '<div class="timeline-event">' +
            '<div class="event-date">' +
                '<span class="event-day">' + dayNum + '</span>' +
                '<span class="event-month">' + month + '</span>' +
            '</div>' +
            '<div class="event-content">' +
                '<div class="event-title">' + title + 
                    (url ? ' <a href="' + url + '" target="_blank" class="event-source-link">↗</a>' : '') +
                '</div>' +
                '<p class="event-description">' + desc + '</p>' +
                '<div class="event-tags">' +
                    '<span class="event-tag">' + type + '</span>' +
                    tags.map(t => '<span class="event-tag">' + escapeHtml(t) + '</span>').join('') +
                '</div>' +
            '</div>' +
        '</div>';
    }).join('');
}

// Render stats
function renderStats(memory, alertsData) {
    const stats = memory.stats || {};
    
    const statEvents = document.getElementById('stat-events');
    const statAlerts = document.getElementById('stat-alerts');
    const statOrgs = document.getElementById('stat-orgs');
    const statNews = document.getElementById('stat-news');
    
    if (statEvents) statEvents.textContent = memory.timeline?.length || stats.events || 0;
    if (statAlerts) statAlerts.textContent = alertsData.alerts?.length || stats.alerts || 0;
    if (statOrgs) statOrgs.textContent = memory.flaggedOrganizations?.length || stats.orgs || 0;
    if (statNews) statNews.textContent = memory.recentNews?.length || stats.newsArticles || 0;
    
    // Last scan time
    const lastScanEl = document.getElementById('last-scan-time');
    if (lastScanEl && memory.lastScan) {
        lastScanEl.textContent = formatRelativeTime(memory.lastScan);
    }
}

// Render confidence meter
function renderConfidence(memory) {
    const conf = memory.systemConfidence || 50;
    
    const percentEl = document.getElementById('confidence-percent');
    const arcEl = document.getElementById('confidence-arc');
    const descEl = document.getElementById('confidence-desc');
    const factorsEl = document.getElementById('confidence-factors');
    
    if (percentEl) percentEl.textContent = conf + '%';
    if (arcEl) arcEl.style.strokeDasharray = (conf * 2.83) + ' 283';
    
    const notes = memory.agentNotes || [];
    if (descEl && notes[0]?.summary) {
        descEl.textContent = notes[0].summary.substring(0, 150) + '...';
    }
    
    const factors = memory.confidenceFactors || [];
    if (factorsEl && factors.length) {
        factorsEl.innerHTML = factors.slice(0, 3).map(f =>
            '<div class="confidence-factor">' +
                '<span class="factor-name">' + escapeHtml(f.factor) + '</span>' +
                '<span class="factor-score">' + f.score + '%</span>' +
            '</div>'
        ).join('');
    }
}

// Render news feed
function renderNews(memory) {
    const container = document.getElementById('news-feed');
    if (!container) return;
    
    const news = memory.recentNews || [];
    
    if (news.length) {
        container.innerHTML = news.slice(0, 12).map(a =>
            '<div class="news-item">' +
                '<a href="' + escapeHtml(a.url || '#') + '" target="_blank" class="news-title">' + 
                    escapeHtml(a.title || 'Untitled') + 
                '</a>' +
                '<div class="news-meta">' +
                    '<span>' + escapeHtml(a.publisher || a.source || '') + '</span>' +
                    '<span>' + escapeHtml(a.location || '') + '</span>' +
                    '<span class="news-relevance">' + (a.relevance_score || 0) + '%</span>' +
                '</div>' +
            '</div>'
        ).join('');
    } else {
        container.innerHTML = '<div class="empty-state"><p>No news yet</p></div>';
    }
}

// Render job list
function renderJobs(memory) {
    const container = document.getElementById('job-list');
    const countEl = document.getElementById('job-count');
    if (!container) return;
    
    const jobs = memory.jobPostings || [];
    const jobCount = memory.jobPostingPatterns?.totalJobs || jobs.length || 0;
    
    if (countEl) countEl.textContent = jobCount;
    
    if (jobs.length) {
        container.innerHTML = jobs.slice(0, 8).map(j => {
            const s = j.suspicion_score || 0;
            const sc = s >= 50 ? '' : s >= 25 ? 'medium' : 'low';
            return '<a href="' + escapeHtml(j.url || '#') + '" target="_blank" class="job-item">' +
                '<span class="job-title">' + escapeHtml((j.title || '').substring(0, 45)) + '...</span>' +
                '<span class="job-location">' + escapeHtml(j.city || '') + ' ' + escapeHtml(j.state || '') + '</span>' +
                '<span class="job-score ' + sc + '">' + s + '%</span>' +
            '</a>';
        }).join('');
    } else {
        const kw = memory.jobPostingPatterns?.keywords || {};
        if (Object.keys(kw).length) {
            container.innerHTML = 
                '<div style="padding:12px;font-size:.8rem;color:var(--color-text-secondary)">' +
                '<p>Monitoring keywords:</p>' +
                Object.entries(kw).slice(0, 6).map(([k, v]) =>
                    '<div class="job-item">' +
                        '<span class="job-title">"' + escapeHtml(k) + '"</span>' +
                        '<span class="job-score low">' + v + '</span>' +
                    '</div>'
                ).join('') +
                '</div>';
        } else {
            container.innerHTML = '<div class="empty-state"><p>No jobs tracked</p></div>';
        }
    }
}

// Render organizations list
function renderOrganizations(memory) {
    const container = document.getElementById('org-list');
    if (!container) return;
    
    const orgs = memory.flaggedOrganizations || [];
    
    if (orgs.length) {
        container.innerHTML = orgs.slice(0, 8).map(o => {
            const s = o.risk_score || 0;
            const rc = s >= 60 ? 'high' : s >= 40 ? 'medium' : 'low';
            return '<a href="' + escapeHtml(o.sourceUrl || '#') + '" target="_blank" class="org-item">' +
                '<div class="org-indicator ' + rc + '"></div>' +
                '<div class="org-details">' +
                    '<div class="org-name">' + escapeHtml(o.name || 'Unknown') + '</div>' +
                    '<div class="org-meta">' + escapeHtml(o.state || '') + 
                        (o.city ? ' | ' + escapeHtml(o.city) : '') + 
                    '</div>' +
                '</div>' +
                '<div class="org-score">' + s + '%</div>' +
            '</a>';
        }).join('');
    } else {
        container.innerHTML = '<div class="empty-state"><p>No orgs flagged</p></div>';
    }
}

// Render alerts
function renderAlerts(alertsData) {
    const container = document.getElementById('alerts-grid');
    if (!container) return;
    
    const alerts = alertsData.alerts || [];
    
    if (alerts.length) {
        container.innerHTML = alerts.slice(0, 6).map(a => {
            const sev = a.severity || (a.confidence >= 80 ? 'high' : a.confidence >= 50 ? 'medium' : 'low');
            return '<div class="alert-card">' +
                '<div class="alert-header">' +
                    '<div class="alert-severity ' + sev + '"></div>' +
                    '<div class="alert-title">' + escapeHtml(a.title || 'Alert') + '</div>' +
                '</div>' +
                '<div class="alert-body">' +
                    '<p class="alert-description">' + escapeHtml((a.description || '').substring(0, 200)) + '...</p>' +
                    '<div class="alert-factors">' +
                        (a.factors || []).slice(0, 3).map(f =>
                            '<div class="alert-factor">' +
                                '<span class="factor-label">' + escapeHtml(f.name || '') + '</span>' +
                                '<span class="factor-value">' + escapeHtml(String(f.value || '')) + '</span>' +
                            '</div>'
                        ).join('') +
                    '</div>' +
                '</div>' +
                '<div class="alert-footer">' +
                    '<span class="alert-confidence">Confidence: ' + (a.confidence || 0) + '%</span>' +
                    '<span style="font-size:.75rem;color:var(--color-text-muted)">' + 
                        formatRelativeTime(a.timestamp) + 
                    '</span>' +
                '</div>' +
            '</div>';
        }).join('');
    } else {
        container.innerHTML = '<div class="empty-state"><p>No active alerts</p></div>';
    }
}

// Setup timeline range button handlers
function setupTimelineControls() {
    document.querySelectorAll('.range-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.range-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            const range = this.dataset.range;
            currentRange = range === 'all' ? 'all' : parseInt(range);
            renderTimeline(currentRange);
        });
    });
}

// Main initialization
async function init() {
    console.log('Astroturf Detector v2.0 initializing...');
    
    // Initialize states grid
    initStatesGrid();
    
    try {
        // Fetch data
        const [mRes, aRes] = await Promise.all([
            fetch('data/memory.json'),
            fetch('data/alerts.json')
        ]);
        
        const memory = mRes.ok ? await mRes.json() : {};
        const alertsData = aRes.ok ? await aRes.json() : { alerts: [] };
        
        // Render all sections
        renderStats(memory, alertsData);
        renderConfidence(memory);
        renderNews(memory);
        renderJobs(memory);
        renderOrganizations(memory);
        renderAlerts(alertsData);
        
        // Setup timeline
        allTimelineEvents = memory.timeline || [];
        renderTimeline(currentRange);
        setupTimelineControls();
        
        console.log('Astroturf Detector v2.0 loaded successfully');
        
    } catch (e) {
        console.error('Error loading data:', e);
    }
}

// Run on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
