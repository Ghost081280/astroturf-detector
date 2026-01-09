// Astroturf Detector v2.1 - Frontend Application

const ALL_STATES = ['AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY','DC'];

// Known services with documentation
const KNOWN_SERVICES = [
    {
        name: "Crowds on Demand",
        type: "Founded 2012 by Adam Swart",
        description: "The largest known paid crowd company. Claims \"tens of thousands\" of contractors nationwide. Reported 400% increase in requests in 2025.",
        locations: ["Los Angeles", "New York", "Washington DC", "Dallas", "Phoenix"],
        pricing: "$60 to attend | $200 speaking roles | $800+ lead roles",
        url: "https://crowdsondemand.com/",
        probability: 95,
        evidence: "Documented in Entergy case, Dallas astroturf network, multiple news investigations"
    },
    {
        name: "Demand Protest",
        type: "Strategic Crowd Mobilization",
        description: "\"When your strategy demands paid protest, we organize and bring it to life.\" Promises \"absolute discretion\" for clients.",
        locations: ["Nationwide"],
        pricing: "Custom quotes | NDA required",
        url: "https://www.demandprotest.com/",
        probability: 90,
        evidence: "Self-advertised service, openly markets paid protest organization"
    },
    {
        name: "The Hawthorn Group",
        type: "PR Firm - Virginia",
        description: "Major PR firm that subcontracted Crowds on Demand for the Entergy scandal. Billed $55,000 for recruiting paid supporters at council meetings.",
        locations: ["Alexandria, VA", "New Orleans"],
        pricing: "Corporate PR rates",
        url: null,
        probability: 88,
        evidence: "Documented in Entergy New Orleans case, $5M fine"
    },
    {
        name: "Advantage Inc.",
        type: "Event Staffing / Brand Ambassadors",
        description: "Event staffing company linked to providing \"supporters\" for political events and corporate campaigns under the guise of brand ambassadors.",
        locations: ["Multiple Markets"],
        pricing: "$15-25/hour for attendees",
        url: null,
        probability: 65,
        evidence: "Investigative journalism reports linking to political events"
    },
    {
        name: "Gotham Government Relations",
        type: "Lobbying Firm - New York",
        description: "Lobbying firm known for organizing \"grassroots\" campaigns funded by corporate clients with direct financial interests in the outcomes.",
        locations: ["New York", "Albany"],
        pricing: "Retainer-based",
        url: null,
        probability: 70,
        evidence: "Corporate lobbying records, campaign finance disclosures"
    },
    {
        name: "Crowds for Rent",
        type: "Event Staffing",
        description: "Provides paid attendees for rallies, grand openings, and political events. Advertises \"enthusiastic supporters\" who will cheer, hold signs, and create energy.",
        locations: ["Florida", "Texas", "California"],
        pricing: "$50-100 per attendee",
        url: null,
        probability: 75,
        evidence: "Online advertisements, event coordination records"
    }
];

let currentRange = 7; // Start at 7 days
let allTimelineEvents = [];
let allNewsItems = [];
let allAlerts = [];
let allConnections = [];
let timelineExpanded = false;
let newsExpanded = false;
let alertsExpanded = false;

// Mobile menu
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
        
        overlay.addEventListener('click', closeMenu);
        nav.querySelectorAll('.nav-link').forEach(link => link.addEventListener('click', closeMenu));
    }
    
    function closeMenu() {
        menuBtn.classList.remove('active');
        nav.classList.remove('active');
        overlay.classList.remove('active');
        document.body.classList.remove('menu-open');
    }
}

// Parse date
function parseDate(d) {
    if (!d) return new Date(0);
    try { return new Date(d); } catch { return new Date(0); }
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

// Escape HTML
function escapeHtml(s) {
    if (!s) return '';
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Get icon SVG
function getTypeIcon(type) {
    const icons = {
        'news': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="item-icon"><path d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2"/></svg>',
        'job_posting': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="item-icon"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>',
        'organization': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="item-icon"><path d="M3 21h18M9 8h1M9 12h1M9 16h1M14 8h1M14 12h1M14 16h1M5 21V5a2 2 0 012-2h10a2 2 0 012 2v16"/></svg>',
        'default': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="item-icon"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>'
    };
    return icons[type] || icons['default'];
}

// Initialize states grid with dynamic activity levels
function initStatesGrid(memory) {
    const grid = document.getElementById('states-grid');
    const analysisEl = document.getElementById('heatmap-analysis');
    if (!grid) return;
    
    // Calculate activity per state from data
    const stateActivity = {};
    ALL_STATES.forEach(s => stateActivity[s] = 0);
    
    // Count jobs per state
    (memory.jobPostings || []).forEach(j => {
        const state = j.state || '';
        if (state && stateActivity[state] !== undefined) {
            stateActivity[state] += j.suspicion_score || 0;
        }
    });
    
    // Count orgs per state
    (memory.flaggedOrganizations || []).forEach(o => {
        const state = o.state || '';
        if (state && stateActivity[state] !== undefined) {
            stateActivity[state] += o.risk_score || 0;
        }
    });
    
    // Count news by location
    (memory.recentNews || []).forEach(n => {
        const loc = (n.location || '').toUpperCase();
        ALL_STATES.forEach(s => {
            if (loc.includes(s) || loc.includes(getStateName(s))) {
                stateActivity[s] += 20;
            }
        });
    });
    
    // Find high activity states
    const sorted = Object.entries(stateActivity).sort((a, b) => b[1] - a[1]);
    const highActivity = sorted.filter(([_, v]) => v > 100).map(([s]) => s);
    const mediumActivity = sorted.filter(([_, v]) => v > 50 && v <= 100).map(([s]) => s);
    
    grid.innerHTML = ALL_STATES.map(s => {
        let cls = 'state-badge';
        let tooltip = 'Standard monitoring';
        if (highActivity.includes(s)) {
            cls += ' high-activity';
            tooltip = `High activity: ${stateActivity[s]} points`;
        } else if (mediumActivity.includes(s)) {
            cls += ' medium-activity';
            tooltip = `Elevated activity: ${stateActivity[s]} points`;
        }
        return `<div class="${cls}" title="${tooltip}">${s}</div>`;
    }).join('');
    
    // Update analysis text
    if (analysisEl) {
        if (highActivity.length > 0) {
            analysisEl.innerHTML = `<strong>Current Hotspots:</strong> ${highActivity.join(', ')} showing elevated activity based on job postings, organization registrations, and news coverage from the last scan.`;
        } else if (mediumActivity.length > 0) {
            analysisEl.innerHTML = `<strong>Moderate Activity:</strong> ${mediumActivity.slice(0, 5).join(', ')} showing some activity. No major hotspots detected in the last scan.`;
        } else {
            analysisEl.innerHTML = `<strong>Status:</strong> No significant hotspots detected. Monitoring all 50 states + DC for suspicious patterns.`;
        }
    }
}

function getStateName(abbr) {
    const names = {CA:'California',TX:'Texas',FL:'Florida',NY:'New York',PA:'Pennsylvania',IL:'Illinois',OH:'Ohio',GA:'Georgia',NC:'North Carolina',MI:'Michigan'};
    return names[abbr] || '';
}

// Render stats
function renderStats(memory, alertsData) {
    const stats = memory.stats || {};
    document.getElementById('stat-events').textContent = memory.timeline?.length || stats.events || 0;
    document.getElementById('stat-alerts').textContent = alertsData.alerts?.length || stats.alerts || 0;
    document.getElementById('stat-orgs').textContent = memory.flaggedOrganizations?.length || stats.orgs || 0;
    document.getElementById('stat-news').textContent = memory.recentNews?.length || stats.newsArticles || 0;
    
    const lastScanEl = document.getElementById('last-scan-time');
    if (lastScanEl && memory.lastScan) {
        lastScanEl.textContent = formatRelativeTime(memory.lastScan);
    }
}

// Render confidence
function renderConfidence(memory) {
    const conf = memory.systemConfidence || 50;
    
    document.getElementById('confidence-percent').textContent = conf + '%';
    document.getElementById('confidence-arc').style.strokeDasharray = (conf * 2.83) + ' 283';
    
    const descEl = document.getElementById('confidence-desc');
    const notes = memory.agentNotes || [];
    if (descEl && notes.length > 0) {
        const latestNote = notes[0];
        const summary = latestNote.summary || 'Awaiting analysis...';
        const timestamp = latestNote.timestamp ? formatRelativeTime(latestNote.timestamp) : '';
        descEl.innerHTML = summary + (timestamp ? ` <em>(${timestamp})</em>` : '');
    }
    
    const factorsEl = document.getElementById('confidence-factors');
    const factors = memory.confidenceFactors || [];
    if (factorsEl && factors.length) {
        factorsEl.innerHTML = factors.slice(0, 3).map(f =>
            `<div class="confidence-factor"><span class="factor-name">${escapeHtml(f.factor)}</span><span class="factor-score">${f.score}%</span></div>`
        ).join('');
    }
}

// Render timeline
function renderTimeline(days) {
    const container = document.getElementById('timeline-events');
    const badge = document.getElementById('timeline-count');
    const seeMoreBtn = document.getElementById('timeline-see-more');
    if (!container) return;
    
    let filtered;
    if (days === 'all') {
        filtered = allTimelineEvents;
    } else {
        const cutoff = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
        filtered = allTimelineEvents.filter(e => parseDate(e.date || e.timestamp) >= cutoff);
    }
    
    filtered.sort((a, b) => parseDate(b.date || b.timestamp) - parseDate(a.date || a.timestamp));
    badge.textContent = filtered.length + ' events';
    
    if (!filtered.length) {
        container.innerHTML = '<div class="empty-state">No events in ' + (days === 'all' ? 'timeline' : 'last ' + days + ' days') + '</div>';
        if (seeMoreBtn) seeMoreBtn.style.display = 'none';
        return;
    }
    
    const limit = timelineExpanded ? filtered.length : 8;
    const displayItems = filtered.slice(0, limit);
    
    container.innerHTML = displayItems.map(e => {
        const title = escapeHtml(e.title || 'Event');
        const url = e.sourceUrl ? escapeHtml(e.sourceUrl) : '';
        const type = e.type || 'default';
        
        return `<div class="timeline-event-compact">
            ${getTypeIcon(type)}
            <span class="event-title-compact">${title.substring(0, 60)}${title.length > 60 ? '...' : ''}</span>
            <span class="event-time-compact">${formatRelativeTime(e.date || e.timestamp)}</span>
            ${url ? `<a href="${url}" target="_blank" class="event-link-compact" aria-label="View source"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3"/></svg></a>` : ''}
        </div>`;
    }).join('');
    
    if (seeMoreBtn) {
        if (filtered.length > 8) {
            seeMoreBtn.style.display = 'flex';
            seeMoreBtn.innerHTML = timelineExpanded ? 
                '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="18 15 12 9 6 15"/></svg> Show Less' :
                `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="6 9 12 15 18 9"/></svg> Show ${filtered.length - 8} More Events`;
        } else {
            seeMoreBtn.style.display = 'none';
        }
    }
}

// Render news - sorted by relevance, show top 10 from each source
function renderNews(memory) {
    const container = document.getElementById('news-feed');
    const seeMoreBtn = document.getElementById('news-see-more');
    if (!container) return;
    
    const news = memory.recentNews || [];
    
    // Separate by source and sort by relevance
    const googleNews = news.filter(n => n.source !== 'duckduckgo').sort((a, b) => (b.relevance_score || 0) - (a.relevance_score || 0)).slice(0, 10);
    const ddgNews = news.filter(n => n.source === 'duckduckgo').sort((a, b) => (b.relevance_score || 0) - (a.relevance_score || 0)).slice(0, 10);
    
    // Merge and sort by relevance
    allNewsItems = [...googleNews, ...ddgNews].sort((a, b) => (b.relevance_score || 0) - (a.relevance_score || 0));
    
    if (allNewsItems.length) {
        const limit = newsExpanded ? allNewsItems.length : 8;
        const displayItems = allNewsItems.slice(0, limit);
        
        container.innerHTML = displayItems.map(a => {
            const source = a.source === 'duckduckgo' ? 'DuckDuckGo' : 'Google';
            const sourceClass = a.source === 'duckduckgo' ? 'source-ddg' : 'source-google';
            return `<div class="news-item">
                <a href="${escapeHtml(a.url || '#')}" target="_blank" class="news-title">${escapeHtml(a.title || 'Untitled')}</a>
                <div class="news-meta">
                    <span class="news-source ${sourceClass}">${source}</span>
                    <span class="news-relevance">${a.relevance_score || 0}% relevant</span>
                    <span>${a.publisher || ''}</span>
                </div>
            </div>`;
        }).join('');
        
        if (seeMoreBtn) {
            seeMoreBtn.style.display = allNewsItems.length > 8 ? 'flex' : 'none';
            seeMoreBtn.innerHTML = newsExpanded ?
                '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="18 15 12 9 6 15"/></svg> Show Less' :
                `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="6 9 12 15 18 9"/></svg> Show ${allNewsItems.length - 8} More`;
        }
    } else {
        container.innerHTML = '<div class="empty-state">No news articles found</div>';
        if (seeMoreBtn) seeMoreBtn.style.display = 'none';
    }
}

// Render jobs
function renderJobs(memory) {
    const container = document.getElementById('job-list');
    const countEl = document.getElementById('job-count');
    if (!container) return;
    
    const jobs = memory.jobPostings || [];
    if (countEl) countEl.textContent = memory.jobPostingPatterns?.totalJobs || jobs.length || 0;
    
    if (jobs.length) {
        container.innerHTML = jobs.slice(0, 8).map(j => {
            const s = j.suspicion_score || 0;
            const sc = s >= 50 ? 'high' : s >= 25 ? 'medium' : 'low';
            return `<a href="${escapeHtml(j.url || '#')}" target="_blank" class="job-item">
                <span class="job-title">${escapeHtml((j.title || '').substring(0, 45))}${(j.title || '').length > 45 ? '...' : ''}</span>
                <span class="job-location">${escapeHtml(j.city || j.state || 'US')}</span>
                <span class="job-score ${sc}">${s}%</span>
            </a>`;
        }).join('');
    } else {
        container.innerHTML = '<div class="empty-state">No suspicious jobs found</div>';
    }
}

// Render organizations
function renderOrganizations(memory) {
    const container = document.getElementById('org-list');
    if (!container) return;
    
    const orgs = memory.flaggedOrganizations || [];
    
    if (orgs.length) {
        container.innerHTML = orgs.slice(0, 8).map(o => {
            const s = o.risk_score || 0;
            const rc = s >= 60 ? 'high' : s >= 40 ? 'medium' : 'low';
            const url = o.sourceUrl || o.url || '';
            const hasLink = url && url !== '#';
            
            if (hasLink) {
                return `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="org-item">
                    <div class="org-indicator ${rc}"></div>
                    <div class="org-details">
                        <div class="org-name">${escapeHtml((o.name || 'Unknown').substring(0, 40))}</div>
                        <div class="org-meta">${escapeHtml(o.state || '')}${o.first_file_date ? ' · Filed: ' + o.first_file_date : ''}</div>
                    </div>
                    <div class="org-score">${s}%</div>
                </a>`;
            } else {
                return `<div class="org-item">
                    <div class="org-indicator ${rc}"></div>
                    <div class="org-details">
                        <div class="org-name">${escapeHtml((o.name || 'Unknown').substring(0, 40))}</div>
                        <div class="org-meta">${escapeHtml(o.state || '')}${o.first_file_date ? ' · Filed: ' + o.first_file_date : ''}</div>
                    </div>
                    <div class="org-score">${s}%</div>
                </div>`;
            }
        }).join('');
    } else {
        container.innerHTML = '<div class="empty-state">No organizations flagged</div>';
    }
}

// Render services with probability scores
function renderServices() {
    const container = document.getElementById('services-grid');
    if (!container) return;
    
    container.innerHTML = KNOWN_SERVICES.map(s => `
        <div class="service-card">
            <span class="service-probability" title="${escapeHtml(s.evidence)}">${s.probability}%</span>
            <div class="service-header">
                <h4>${escapeHtml(s.name)}</h4>
                <span class="service-type">${escapeHtml(s.type)}</span>
            </div>
            <div class="service-body">
                <p>${escapeHtml(s.description)}</p>
                <div class="service-locations">
                    ${s.locations.map(l => `<span class="location-tag">${escapeHtml(l)}</span>`).join('')}
                </div>
                ${s.url ? `<a href="${escapeHtml(s.url)}" target="_blank" class="service-link">${new URL(s.url).hostname} →</a>` : '<span class="service-link">No public website</span>'}
                ${s.pricing ? `<div class="service-pricing">${escapeHtml(s.pricing)}</div>` : ''}
            </div>
        </div>
    `).join('');
}

// Render connections (Connect the Dots)
function renderConnections(memory) {
    const container = document.getElementById('connections-grid');
    if (!container) return;
    
    const connections = memory.connections || [];
    
    if (connections.length === 0) {
        // Generate connections from data if not provided by backend
        const generatedConnections = generateConnections(memory);
        allConnections = generatedConnections;
    } else {
        allConnections = connections;
    }
    
    if (allConnections.length) {
        container.innerHTML = allConnections.slice(0, 6).map(c => {
            const probClass = c.probability >= 70 ? 'high' : c.probability >= 50 ? 'medium' : 'low';
            return `<div class="connection-card">
                <div class="connection-header">
                    <div class="connection-type">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="6" cy="6" r="3"/><circle cx="18" cy="18" r="3"/><line x1="8.5" y1="8.5" x2="15.5" y2="15.5"/></svg>
                        ${escapeHtml(c.type || 'Pattern')}
                    </div>
                    <span class="connection-probability ${probClass}">${c.probability}%</span>
                </div>
                <div class="connection-details">${escapeHtml(c.description)}</div>
                <div class="connection-evidence">
                    ${(c.evidence || []).map(e => `<div class="evidence-item"><span class="evidence-label">${escapeHtml(e.type)}:</span> ${escapeHtml(e.detail)}</div>`).join('')}
                </div>
            </div>`;
        }).join('');
    } else {
        container.innerHTML = '<div class="empty-state">No significant connections detected in current data. Connections appear when the AI identifies correlations between jobs, news, and organizations.</div>';
    }
}

// Generate connections from data (client-side correlation)
function generateConnections(memory) {
    const connections = [];
    const jobs = memory.jobPostings || [];
    const news = memory.recentNews || [];
    const orgs = memory.flaggedOrganizations || [];
    
    // 1. Geographic correlation: Jobs + News in same location
    const newsLocations = new Set();
    news.forEach(n => {
        if (n.location) newsLocations.add(n.location.toLowerCase());
        // Extract city names from title
        const cities = ['dallas', 'los angeles', 'new york', 'chicago', 'houston', 'phoenix', 'philadelphia', 'san antonio', 'san diego', 'austin', 'portland', 'seattle', 'minneapolis'];
        cities.forEach(city => {
            if ((n.title || '').toLowerCase().includes(city)) newsLocations.add(city);
        });
    });
    
    const jobsNearNews = jobs.filter(j => {
        const city = (j.city || '').toLowerCase();
        return newsLocations.has(city);
    });
    
    if (jobsNearNews.length > 0) {
        connections.push({
            type: 'Geographic Match',
            description: `${jobsNearNews.length} suspicious job posting(s) found in cities with recent protest-related news coverage.`,
            probability: Math.min(60 + jobsNearNews.length * 5, 85),
            evidence: jobsNearNews.slice(0, 2).map(j => ({
                type: 'Job',
                detail: `${j.title?.substring(0, 40)} in ${j.city || 'Unknown'}`
            }))
        });
    }
    
    // 2. Organization naming patterns
    const suspiciousNames = orgs.filter(o => {
        const name = (o.name || '').toLowerCase();
        return name.includes('freedom') || name.includes('liberty') || name.includes('citizens for') || name.includes('americans for');
    });
    
    if (suspiciousNames.length >= 3) {
        connections.push({
            type: 'Naming Pattern',
            description: `${suspiciousNames.length} organizations using generic patriotic naming patterns commonly associated with astroturf groups.`,
            probability: Math.min(55 + suspiciousNames.length * 3, 80),
            evidence: suspiciousNames.slice(0, 3).map(o => ({
                type: 'Org',
                detail: o.name?.substring(0, 45)
            }))
        });
    }
    
    // 3. Recent formation + high activity
    const recentOrgs = orgs.filter(o => {
        if (!o.first_file_date) return false;
        const filed = new Date(o.first_file_date);
        const sixMonthsAgo = new Date();
        sixMonthsAgo.setMonth(sixMonthsAgo.getMonth() - 6);
        return filed > sixMonthsAgo && (o.risk_score || 0) >= 70;
    });
    
    if (recentOrgs.length > 0) {
        connections.push({
            type: 'New High-Risk Orgs',
            description: `${recentOrgs.length} high-risk organization(s) filed within the last 6 months, suggesting possible rapid mobilization.`,
            probability: Math.min(50 + recentOrgs.length * 10, 75),
            evidence: recentOrgs.slice(0, 2).map(o => ({
                type: 'Filed',
                detail: `${o.name?.substring(0, 35)} (${o.first_file_date})`
            }))
        });
    }
    
    // 4. News clustering
    const paidProtestNews = news.filter(n => 
        (n.title || '').toLowerCase().includes('paid') || 
        (n.query || '').includes('paid')
    );
    
    if (paidProtestNews.length >= 3) {
        connections.push({
            type: 'News Cluster',
            description: `${paidProtestNews.length} news articles specifically mentioning "paid" protesters or actors in recent coverage.`,
            probability: Math.min(45 + paidProtestNews.length * 5, 70),
            evidence: paidProtestNews.slice(0, 2).map(n => ({
                type: 'News',
                detail: n.title?.substring(0, 50)
            }))
        });
    }
    
    // Sort by probability
    connections.sort((a, b) => b.probability - a.probability);
    
    return connections;
}

// Render alerts - full text, no truncation
function renderAlerts(alertsData) {
    const container = document.getElementById('alerts-grid');
    const seeMoreBtn = document.getElementById('alerts-see-more');
    if (!container) return;
    
    allAlerts = alertsData.alerts || [];
    
    if (allAlerts.length) {
        const limit = alertsExpanded ? allAlerts.length : 6;
        const displayItems = allAlerts.slice(0, limit);
        
        container.innerHTML = displayItems.map(a => {
            const conf = a.confidence || 50;
            const sev = conf >= 70 ? 'high' : conf >= 50 ? 'medium' : 'low';
            const title = a.title || 'Alert';
            const desc = a.description || a.details || '';
            const sources = a.sources || a.triggers || [];
            
            return `<div class="alert-card">
                <div class="alert-header">
                    <span class="alert-severity ${sev}"></span>
                    <span class="alert-title">${escapeHtml(title)}</span>
                </div>
                ${desc ? `<div class="alert-body">${escapeHtml(desc)}</div>` : ''}
                ${sources.length ? `<div class="alert-sources">${sources.slice(0, 4).map(s => `<span class="alert-source-btn">${escapeHtml(typeof s === 'string' ? s : s.type || 'Source')}</span>`).join('')}</div>` : ''}
                <div class="alert-footer">
                    <span class="alert-confidence">${conf}% confidence</span>
                    <span class="alert-time">${formatRelativeTime(a.timestamp)}</span>
                </div>
            </div>`;
        }).join('');
        
        if (seeMoreBtn) {
            seeMoreBtn.style.display = allAlerts.length > 6 ? 'flex' : 'none';
            seeMoreBtn.innerHTML = alertsExpanded ?
                '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="18 15 12 9 6 15"/></svg> Show Less' :
                `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="6 9 12 15 18 9"/></svg> Show ${allAlerts.length - 6} More Alerts`;
        }
    } else {
        container.innerHTML = '<div class="empty-state">No active alerts. Alerts are generated when our AI detects suspicious patterns across jobs, organizations, and news.</div>';
        if (seeMoreBtn) seeMoreBtn.style.display = 'none';
    }
}

// Setup controls
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

function setupSeeMoreButtons() {
    document.getElementById('timeline-see-more')?.addEventListener('click', () => {
        timelineExpanded = !timelineExpanded;
        renderTimeline(currentRange);
    });
    
    document.getElementById('news-see-more')?.addEventListener('click', () => {
        newsExpanded = !newsExpanded;
        renderNews({ recentNews: allNewsItems });
    });
    
    document.getElementById('alerts-see-more')?.addEventListener('click', () => {
        alertsExpanded = !alertsExpanded;
        renderAlerts({ alerts: allAlerts });
    });
}

// Main init
async function init() {
    console.log('Astroturf Detector v2.1 initializing...');
    
    initMobileMenu();
    renderServices(); // Static services with probability scores
    
    try {
        const [mRes, aRes] = await Promise.all([
            fetch('data/memory.json'),
            fetch('data/alerts.json')
        ]);
        
        const memory = mRes.ok ? await mRes.json() : {};
        const alertsData = aRes.ok ? await aRes.json() : { alerts: [] };
        
        initStatesGrid(memory);
        renderStats(memory, alertsData);
        renderConfidence(memory);
        renderNews(memory);
        renderJobs(memory);
        renderOrganizations(memory);
        renderAlerts(alertsData);
        renderConnections(memory);
        
        allTimelineEvents = memory.timeline || [];
        renderTimeline(currentRange);
        setupTimelineControls();
        setupSeeMoreButtons();
        
        console.log('Astroturf Detector v2.1 loaded successfully');
        
    } catch (e) {
        console.error('Error loading data:', e);
        // Show empty states
        document.querySelectorAll('.loading-indicator').forEach(el => {
            el.innerHTML = '<span>Data unavailable</span>';
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
