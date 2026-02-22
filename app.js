/**
 * SIR Voter Search — Kerala Electoral Roll Lookup
 * ================================================
 * Client-side fuzzy search with Fuse.js for voter details.
 * Supports English, Malayalam, and Voter ID searching.
 */

// ─── State ───────────────────────────────────────────────────────────────────
let votersData = [];
let fuse = null;
let debounceTimer = null;

// ─── DOM Elements ────────────────────────────────────────────────────────────
const searchInput = document.getElementById('search-input');
const clearBtn = document.getElementById('clear-btn');
const resultsSection = document.getElementById('results-section');
const resultsGrid = document.getElementById('results-grid');
const resultsTitle = document.getElementById('results-title');
const resultsCount = document.getElementById('results-count');
const emptyState = document.getElementById('empty-state');
const loadingState = document.getElementById('loading-state');
const totalRecords = document.getElementById('total-records');
const totalRecordsDisplay = document.getElementById('total-records-display');
const totalWardsDisplay = document.getElementById('total-wards-display');
const heroSection = document.getElementById('hero-section');

// ─── Initialize ──────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);

async function init() {
    await loadData();
    setupEventListeners();
    animateOnLoad();
}

// ─── Load Data ───────────────────────────────────────────────────────────────
async function loadData() {
    try {
        showLoading(true);

        const response = await fetch('./voters_data.json');
        if (!response.ok) throw new Error('Failed to load voter data');

        const data = await response.json();
        votersData = data.voters || [];
        const metadata = data.metadata || {};

        // Update record count
        const count = votersData.length;
        if (totalRecords) totalRecords.textContent = count;
        if (totalRecordsDisplay) totalRecordsDisplay.textContent = count.toLocaleString();

        // Update wards count
        if (totalWardsDisplay && metadata.pdfs_processed) {
            totalWardsDisplay.textContent = metadata.pdfs_processed.length;
        }

        // Initialize Fuse.js with configurable keys and thresholds
        fuse = new Fuse(votersData, {
            keys: [
                { name: 'voter_id', weight: 2.0 },
                { name: 'name_en', weight: 1.5 },
                { name: 'name_ml', weight: 1.5 },
                { name: 'relative_name_en', weight: 0.8 },
                { name: 'relative_name_ml', weight: 0.8 },
                { name: 'house_number', weight: 0.6 },
            ],
            threshold: 0.4,          // Slightly more fuzzy for better coverage
            distance: 1000,          // Larger distance to find records across the dataset
            minMatchCharLength: 2,   // Min chars to start matching
            includeScore: true,
            includeMatches: true,
            ignoreLocation: true,    // Don't care where in the string the match is
            useExtendedSearch: true, // Enable powerful extended search (e.g. "Muhammed | Abdulla")
            findAllMatches: true,
        });

        showLoading(false);
        console.log(`✓ Loaded ${votersData.length} voter records`);

    } catch (error) {
        console.error('Error loading data:', error);
        showLoading(false);
        showEmpty();
    }
}

// ─── Event Listeners ─────────────────────────────────────────────────────────
function setupEventListeners() {
    // Search input with debounce
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        clearBtn.style.display = query ? 'flex' : 'none';

        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            performSearch(query);
        }, 200);
    });

    // Clear button
    clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        clearBtn.style.display = 'none';
        hideResults();
        searchInput.focus();
    });

    // Keyboard shortcut: Escape to clear
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            searchInput.value = '';
            clearBtn.style.display = 'none';
            hideResults();
        }
    });

    // Hint chips
    document.querySelectorAll('.hint-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const query = chip.dataset.query;
            searchInput.value = query;
            clearBtn.style.display = 'flex';
            performSearch(query);
            searchInput.focus();
        });
    });

    // Global keyboard shortcut: "/" to focus search
    document.addEventListener('keydown', (e) => {
        if (e.key === '/' && document.activeElement !== searchInput) {
            e.preventDefault();
            searchInput.focus();
        }
    });
}

// ─── Search Logic ────────────────────────────────────────────────────────────
function performSearch(query) {
    if (!query || query.length < 2) {
        hideResults();
        return;
    }

    if (!fuse) return;

    // Check if query looks like a voter ID (alphanumeric starting with letters)
    const isVoterIdSearch = /^[A-Za-z]{2,3}\d/.test(query);

    let results;

    if (isVoterIdSearch) {
        // For voter ID, do exact prefix matching first
        const upperQuery = query.toUpperCase();
        const exactMatches = votersData.filter(v =>
            v.voter_id && v.voter_id.toUpperCase().startsWith(upperQuery)
        );

        if (exactMatches.length > 0) {
            results = exactMatches.map(item => ({
                item,
                score: 0,
                matches: [{ key: 'voter_id', value: item.voter_id }]
            }));
        } else {
            // Fall back to fuzzy search
            results = fuse.search(query, { limit: 100 });
        }
    } else {
        // Name search (English or Malayalam) — use fuzzy search
        results = fuse.search(query, { limit: 100 });
    }

    if (results.length > 0) {
        showResults(results, query);
    } else {
        showEmpty();
    }
}

// ─── Display Results ─────────────────────────────────────────────────────────
function showResults(results, query) {
    emptyState.style.display = 'none';
    resultsSection.style.display = 'block';

    resultsTitle.textContent = 'Search Results';
    resultsCount.textContent = `Found ${results.length} matching record${results.length !== 1 ? 's' : ''} for "${query}"`;

    resultsGrid.innerHTML = results.map((result, index) => {
        const voter = result.item;
        return createVoterCard(voter, index, query);
    }).join('');

    // Add copy event listeners to voter ID badges
    document.querySelectorAll('.voter-card-id').forEach(badge => {
        badge.addEventListener('click', () => {
            const id = badge.dataset.voterId;
            copyToClipboard(id);
        });
    });

    // Smooth scroll to results on mobile
    if (window.innerWidth <= 768) {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

function createVoterCard(voter, index, query) {
    const genderClass = voter.gender?.includes('Male') ? 'male' : 'female';
    const genderIcon = voter.gender?.includes('Male') ? '♂' : '♀';
    const genderLabel = voter.gender?.includes('Male') ? 'Male' : 'Female';

    const nameEn = highlightMatch(voter.name_en || '—', query);
    const relativeNameEn = highlightMatch(voter.relative_name_en || '—', query);
    const voterId = highlightMatch(voter.voter_id || '—', query);

    return `
        <div class="voter-card" style="animation-delay: ${index * 0.05}s" id="voter-${voter.voter_id}">
            <div class="voter-card-header">
                <div style="display: flex; align-items: center;">
                    ${voter.serial_no ? `<span class="serial-badge">${voter.serial_no}</span>` : ''}
                    <div class="voter-card-name">
                        <div class="name-en">${nameEn}</div>
                        <div class="name-ml">${highlightMatch(voter.name_ml || '', query)}</div>
                    </div>
                </div>
                <div class="voter-card-actions">
                    <div class="voter-card-id" data-voter-id="${voter.voter_id || ''}" title="Click to copy ID">
                        <span>${voterId}</span>
                        <svg class="copy-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                            <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
                        </svg>
                    </div>
                    <button class="share-btn" onclick="shareVoter('${voter.voter_id}')" title="Share Voter Details">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M4 12v8a2 2 0 002 2h12a2 2 0 002-2v-8"/>
                            <polyline points="16 6 12 2 8 6"/>
                            <line x1="12" y1="2" x2="12" y2="15"/>
                        </svg>
                    </button>
                </div>
            </div>
            <div class="voter-card-body">
                <div class="detail-item full-width">
                    <span class="detail-label">${voter.relation_type || "Relative's Name"}</span>
                    <span class="detail-value">
                        ${relativeNameEn}
                        ${voter.relative_name_ml ? `<span class="ml-sub">${highlightMatch(voter.relative_name_ml, query)}</span>` : ''}
                    </span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">House No / വീട്ടു നമ്പർ</span>
                    <span class="detail-value">${voter.house_number || '—'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Age / പ്രായം</span>
                    <span class="detail-value">
                        <span class="age-badge">🎂 ${voter.age || '—'} years</span>
                    </span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Gender / ലിംഗം</span>
                    <span class="detail-value">
                        <span class="gender-badge ${genderClass}">${genderIcon} ${genderLabel}</span>
                    </span>
                </div>
            </div>
        </div>
    `;
}

// ─── Share Voter ─────────────────────────────────────────────────────────────
function shareVoter(voterId) {
    const voter = votersData.find(v => v.voter_id === voterId);
    if (!voter) return;

    const text = `Voter Details:
Name: ${voter.name_en} (${voter.name_ml})
Voter ID: ${voter.voter_id}
House No: ${voter.house_number}
Age: ${voter.age}
Gender: ${voter.gender}
Search more at: SIR Voter Search`;

    if (navigator.share) {
        navigator.share({
            title: 'Voter Details',
            text: text,
            url: window.location.href
        }).catch(() => {
            copyToClipboard(text, "Voter details copied for sharing");
        });
    } else {
        copyToClipboard(text, "Voter details copied for sharing");
    }
}

// ─── Highlight matched text ──────────────────────────────────────────────────
function highlightMatch(text, query) {
    if (!text || !query || query.length < 2) return text;

    try {
        // Escape special regex characters in query
        const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(`(${escapedQuery})`, 'gi');
        return text.replace(regex, '<span class="highlight">$1</span>');
    } catch (e) {
        return text;
    }
}

// ─── UI State Helpers ────────────────────────────────────────────────────────
function hideResults() {
    resultsSection.style.display = 'none';
    emptyState.style.display = 'none';
}

function showEmpty() {
    resultsSection.style.display = 'none';
    emptyState.style.display = 'block';
}

function showLoading(show) {
    loadingState.style.display = show ? 'block' : 'none';
}

// ─── Copy to Clipboard ──────────────────────────────────────────────────────
function copyToClipboard(text, message) {
    if (!text) return;
    const successMsg = message || `Copied: ${text}`;

    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showToast(successMsg);
        }).catch(() => {
            fallbackCopy(text, successMsg);
        });
    } else {
        fallbackCopy(text, successMsg);
    }
}

function fallbackCopy(text, message) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
        document.execCommand('copy');
        showToast(message);
    } catch (e) {
        showToast('Copy failed');
    }
    document.body.removeChild(textarea);
}

// ─── Toast Notification ──────────────────────────────────────────────────────
function showToast(message) {
    // Remove existing toast
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });

    // Animate out after 2s
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

// ─── Load Animation ──────────────────────────────────────────────────────────
function animateOnLoad() {
    // Focus search input after animations complete
    setTimeout(() => {
        searchInput.focus();
    }, 800);
}
