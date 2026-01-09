// Astroturf Detector v2.0 - Frontend Application

const ALL_STATES = ['AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY','DC'];
const HIGH_ACTIVITY = ['TX','CA','FL','NY','PA','OH','GA','NC','MI','AZ','WA','CO','VA','NJ','IL','DC'];

let currentRange = 90;
let allTimelineEvents = [];
let allNewsItems = [];
let allAlerts = [];
let timelineExpanded = false;
let newsExpanded = false;
let alertsExpanded = false;

// Mobile menu functionality
function initMobileMenu() {
    const menuBtn = document.getElementById('mobile-menu-btn');
    const nav = document.getElementById('main-nav');
    const overlay = document.getElementById('mobile-nav-overlay');
    
    if (menuBtn && nav && overlay) {
        menuBtn.addEventListener('click', () => {
            menuBtn.classList.toggle('active');
            nav.classList.toggle('active');
            overlay.classList.toggle('active');
            document.body.classList.toggle('menu-open');
        });
        
        overlay.addEventListener('click', () => {
            menuBtn.classList.remove('active');
            nav.classList.remove('active');
            overlay.classList.remove('active');
            document.body.classList.remove('menu-open');
        });
        
        // Close menu when clicking a link
        nav.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                menuBtn.classList.remove('active');
                nav.classList.remove('active');
                overlay.classList.remove('active');
                document.body.classList.remove('menu-open');
            });
        });
    }
}

// Initialize states grid with tooltip context
function initStatesGrid() {
    const grid = document.getElementById('states-grid');
    if (grid) {
        grid.innerHTML = ALL_STATES.map(s => {
            const isHighActivity = HIGH_ACTIVITY.includes(s);
            const tooltip = isHighActivity ? 'Priority: High political spending & activity' : 'Standard monitoring';
            return '<div class="state-badge ' + (isHighActivity ? 'high-activity' : '') + '" title="' + tooltip + '">' + s + '</div>';
        }).join('');
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

// Get icon SVG based on type (no emojis)
function getTypeIcon(type) {
    const icons = {
        'news': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="item-icon"><path d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2"/></svg>',
        'job_posting': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="item-icon"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>',
        'organization': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="item-icon"><path d="M3 21h18M9 8h1M9 12h1M9 16h1M14 8h1M14 12h1M14 16h1M5 21V5a2 2 0 012-2h10a2 2 0 012 2v16"/></svg>',
        'default': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="item-icon"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>'
    };
    return icons[type] || icons['default'];
}

// Render timeline with COMPACT items and see more
function renderTimeline(days) {
    const container = document.getElementById('timeline-events');
    const badge = document.getElementById('timeline-count');
    const seeMoreBtn = document.getElementById('timeline-see-more');
    
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
        if (seeMoreBtn) seeMoreBtn.style.display = 'none';
        return;
    }
    
    const limit = timelineExpanded ? filtered.length : 8;
    const displayItems = filtered.slice(0, limit);
    
    container.innerHTML = displayItems.map(e => {
        const title = escapeHtml(e.title || 'Event');
        const url = e.sourceUrl ? escapeHtml(e.sourceUrl) : '';
        const type = e.type || 'default';
        
        return '<div class="timeline-event-compact">' +
            getTypeIcon(type) +
            '<span class="event-title-compact">' + title.substring(0, 55) + (title.length > 55 ? '...' : '') + '</span>' +
            '<span class="event-time-compact">' + formatRelativeTime(e.date || e.timestamp) + '</span>' +
            (url ? '<a href="' + url + '" target="_blank" class="event-link-compact" aria-label="View source"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3"/></svg></a>' : '') +
        '</div>';
    }).join('');
    
    // Show/hide see more button
    if (seeMoreBtn) {
        if (filtered.length > 8) {
            seeMoreBtn.style.display = 'flex';
            seeMoreBtn.innerHTML = timelineExpanded ? 
                '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="18 15 12 9 6 15"/></svg> Show Less' :
                '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="6 9 12 15 18 9"/></svg> Show ' + (filtered.length - 8) + ' More Events';
        } else {
            seeMoreBtn.style.display = 'none';
        }
    }
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
    
    const lastScanEl = document.getElementById('last-scan-time');
    if (lastScanEl && memory.lastScan) {
        lastScanEl.textContent = formatRelativeTime(memory.lastScan);
    }
}

// Render confidence meter - FULL AI analysis
function renderConfidence(memory) {
    const conf = memory.systemConfidence || 50;
    
    const percentEl = document.getElementById('confidence-percent');
    const arcEl = document.getElementById('confidence-arc');
    const descEl = document.getElementById('confidence-desc');
    const factorsEl = document.getElementById('confidence-factors');
    
    if (percentEl) percentEl.textContent = conf + '%';
    if (arcEl) arcEl.style.strokeDasharray = (conf * 2.83) + ' 283';
    
    const notes = memory.agentNotes || [];
    if (descEl && notes.length > 0) {
        const latestNote = notes[0];
        const summary = latestNote.summary || 'Awaiting analysis...';
        const timestamp = latestNote.timestamp ? formatRelativeTime(latestNote.timestamp) : '';
        descEl.innerHTML = '<strong>Latest Analysis' + (timestamp ? ' (' + timestamp + ')' : '') + ':</strong><br>' + escapeHtml(summary);
    }
    
    const factors = memory.confidenceFactors || [];
    if (factorsEl && factors.length) {
        factorsEl.innerHTML = factors.map(f =>
            '<div class="confidence-factor">' +
                '<span class="factor-name">' + escapeHtml(f.factor) + '</span>' +
                '<span class="factor-score">' + f.score + '%</span>' +
            '</div>'
        ).join('');
    }
}

// Render news feed with see more
function renderNews(memory) {
    const container = document.getElementById('news-feed');
    const seeMoreBtn = document.getElementById('news-see-more');
    if (!container) return;
    
    allNewsItems = memory.recentNews || [];
    
    if (allNewsItems.length) {
        const limit = newsExpanded ? allNewsItems.length : 6;
        const displayItems = allNewsItems.slice(0, limit);
        
        container.innerHTML = displayItems.map(a => {
            const source = a.source === 'duckduckgo' ? 'DuckDuckGo' : (a.publisher || a.source || 'Google News');
            const sourceClass = a.source === 'duckduckgo' ? 'source-ddg' : 'source-google';
            return '<div class="news-item">' +
                '<a href="' + escapeHtml(a.url || '#') + '" target="_blank" class="news-title">' + 
                    escapeHtml(a.title || 'Untitled') + 
                '</a>' +
                '<div class="news-meta">' +
                    '<span class="news-source ' + sourceClass + '">' + escapeHtml(source) + '</span>' +
                    '<span class="news-relevance">' + (a.relevance_score || 0) + '% relevant</span>' +
                '</div>' +
            '</div>';
        }).join('');
        
        if (seeMoreBtn) {
            if (allNewsItems.length > 6) {
                seeMoreBtn.style.display = 'flex';
                seeMoreBtn.innerHTML = newsExpanded ?
                    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="18 15 12 9 6 15"/></svg> Show Less' :
                    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="6 9 12 15 18 9"/></svg> Show ' + (allNewsItems.length - 6) + ' More Articles';
            } else {
                seeMoreBtn.style.display = 'none';
            }
        }
    } else {
        container.innerHTML = '<div class="empty-state"><p>No news articles found</p></div>';
        if (seeMoreBtn) seeMoreBtn.style.display = 'none';
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
        container.innerHTML = jobs.slice(0, 6).map(j => {
            const s = j.suspicion_score || 0;
            const sc = s >= 50 ? 'high' : s >= 25 ? 'medium' : 'low';
            return '<a href="' + escapeHtml(j.url || '#') + '" target="_blank" class="job-item">' +
                '<span class="job-title">' + escapeHtml((j.title || '').substring(0, 40)) + (j.title && j.title.length > 40 ? '...' : '') + '</span>' +
                '<span class="job-location">' + escapeHtml(j.city || 'US') + '</span>' +
                '<span class="job-score ' + sc + '">' + s + '%</span>' +
            '</a>';
        }).join('');
    } else {
        container.innerHTML = '<div class="empty-state"><p>No suspicious jobs found</p></div>';
    }
}

// Render organizations list
function renderOrganizations(memory) {
    const container = document.getElementById('org-list');
    if (!container) return;
    
    const orgs = memory.flaggedOrganizations || [];
    
    if (orgs.length) {
        container.innerHTML = orgs.slice(0, 6).map(o => {
            const s = o.risk_score || 0;
            const rc = s >= 60 ? 'high' : s >= 40 ? 'medium' : 'low';
            return '<a href="' + escapeHtml(o.sourceUrl || '#') + '" target="_blank" class="org-item">' +
                '<div class="org-indicator ' + rc + '"></div>' +
                '<div class="org-details">' +
                    '<div class="org-name">' + escapeHtml((o.name || 'Unknown').substring(0, 35)) + '</div>' +
                    '<div class="org-meta">' + escapeHtml(o.state || '') + 
                        (o.city ? ' · ' + escapeHtml(o.city) : '') + 
                    '</div>' +
                '</div>' +
                '<div class="org-score">' + s + '%</div>' +
            '</a>';
        }).join('');
    } else {
        container.innerHTML = '<div class="empty-state"><p>No organizations flagged</p></div>';
    }
}

// Render alerts - cleaned up with see more
function renderAlerts(alertsData) {
    const container = document.getElementById('alerts-grid');
    const seeMoreBtn = document.getElementById('alerts-see-more');
    if (!container) return;
    
    allAlerts = alertsData.alerts || [];
    
    if (allAlerts.length) {
        const limit = alertsExpanded ? allAlerts.length : 4;
        const displayItems = allAlerts.slice(0, limit);
        
        container.innerHTML = displayItems.map(a => {
            const conf = a.confidence || 50;
            const sev = conf >= 70 ? 'high' : conf >= 50 ? 'medium' : 'low';
            const title = a.title || 'Alert';
            
            return '<div class="alert-card-clean">' +
                '<div class="alert-header-clean">' +
                    '<span class="alert-severity-dot ' + sev + '"></span>' +
                    '<span class="alert-title-clean">' + escapeHtml(title.substring(0, 80)) + '</span>' +
                '</div>' +
                '<div class="alert-footer-clean">' +
                    '<span class="alert-confidence-clean">' + conf + '% confidence</span>' +
                    '<span class="alert-time-clean">' + formatRelativeTime(a.timestamp) + '</span>' +
                '</div>' +
            '</div>';
        }).join('');
        
        if (seeMoreBtn) {
            if (allAlerts.length > 4) {
                seeMoreBtn.style.display = 'flex';
                seeMoreBtn.innerHTML = alertsExpanded ?
                    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="18 15 12 9 6 15"/></svg> Show Less' :
                    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="6 9 12 15 18 9"/></svg> Show ' + (allAlerts.length - 4) + ' More Alerts';
            } else {
                seeMoreBtn.style.display = 'none';
            }
        }
    } else {
        container.innerHTML = '<div class="empty-state"><p>No active alerts</p></div>';
        if (seeMoreBtn) seeMoreBtn.style.display = 'none';
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
            timelineExpanded = false;
            renderTimeline(currentRange);
        });
    });
}

// Setup see more buttons
function setupSeeMoreButtons() {
    const timelineSeeMore = document.getElementById('timeline-see-more');
    const newsSeeMore = document.getElementById('news-see-more');
    const alertsSeeMore = document.getElementById('alerts-see-more');
    
    if (timelineSeeMore) {
        timelineSeeMore.addEventListener('click', () => {
            timelineExpanded = !timelineExpanded;
            renderTimeline(currentRange);
        });
    }
    
    if (newsSeeMore) {
        newsSeeMore.addEventListener('click', () => {
            newsExpanded = !newsExpanded;
            renderNews({ recentNews: allNewsItems });
        });
    }
    
    if (alertsSeeMore) {
        alertsSeeMore.addEventListener('click', () => {
            alertsExpanded = !alertsExpanded;
            renderAlerts({ alerts: allAlerts });
        });
    }
}

// Main initialization
async function init() {
    console.log('Astroturf Detector v2.0 initializing...');
    
    initMobileMenu();
    initStatesGrid();
    
    try {
        const [mRes, aRes] = await Promise.all([
            fetch('data/memory.json'),
            fetch('data/alerts.json')
        ]);
        
        const memory = mRes.ok ? await mRes.json() : {};
        const alertsData = aRes.ok ? await aRes.json() : { alerts: [] };
        
        renderStats(memory, alertsData);
        renderConfidence(memory);
        renderNews(memory);
        renderJobs(memory);
        renderOrganizations(memory);
        renderAlerts(alertsData);
        
        allTimelineEvents = memory.timeline || [];
        renderTimeline(currentRange);
        setupTimelineControls();
        setupSeeMoreButtons();
        
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
