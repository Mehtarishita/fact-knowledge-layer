let allFacts = [];
let allRelationships = [];
let isPolling = false;

document.addEventListener('DOMContentLoaded', () => {
    fetchData();
});

function animateValue(obj, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * (end - start) + start);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// File Upload Logic
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const uploadStatus = document.getElementById('upload-status');

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => { dropZone.classList.remove('dragover'); });
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
});
fileInput.addEventListener('change', () => {
    if (fileInput.files.length) handleFiles(fileInput.files);
});

function handleFiles(files) {
    Array.from(files).forEach(file => uploadFile(file));
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    uploadStatus.textContent = `Uploading ${file.name}...`;
    uploadStatus.style.color = 'var(--text-primary)';

    fetch('/api/upload', { method: 'POST', body: formData })
    .then(response => response.json())
    .then(data => {
        uploadStatus.textContent = data.message;
        uploadStatus.style.color = 'var(--rel-corroboration)';
        if (!isPolling) startPolling();
    })
    .catch(error => {
        uploadStatus.textContent = `Error uploading ${file.name}`;
        uploadStatus.style.color = 'var(--rel-contradiction)';
        console.error('Error:', error);
    });
}

function startPolling() {
    isPolling = true;
    setInterval(() => fetchData(), 3000);
}

function fetchData(forceRender = false) {
    const syncBtn = document.getElementById('btn-sync');
    if (syncBtn) {
        syncBtn.classList.add('syncing');
        syncBtn.textContent = 'Syncing...';
    }

    Promise.all([
        fetch('/api/facts').then(res => res.json()),
        fetch('/api/relationships').then(res => res.json())
    ])
    .then(([facts, relationships]) => {
        if (syncBtn) {
            syncBtn.classList.remove('syncing');
            syncBtn.textContent = 'Sync Ledger';
            const now = new Date();
            document.getElementById('last-synced').textContent = `Last Synced: ${now.toLocaleTimeString()}`;
        }

        if (forceRender || JSON.stringify(facts) !== JSON.stringify(allFacts) || 
            JSON.stringify(relationships) !== JSON.stringify(allRelationships)) {
            
            const prevDocsCount = new Set(allFacts.map(f => f.document)).size;
            const newDocsCount = new Set(facts.map(f => f.document)).size;
            
            allFacts = facts;
            allRelationships = relationships;
            
            // Animate Stats if they changed
            if (forceRender || prevDocsCount !== newDocsCount) animateValue(document.getElementById('stat-docs'), prevDocsCount, newDocsCount, 800);
            animateValue(document.getElementById('stat-facts'), 0, facts.length, 800);
            animateValue(document.getElementById('stat-rels'), 0, relationships.length, 800);
            
            if (facts.length > 0) {
                document.getElementById('loading-state').style.display = 'none';
                document.getElementById('content-state').style.display = 'block';
            }
            
            renderUI();
        }
    })
    .catch(err => {
        console.error("Error fetching data:", err);
        if (syncBtn) {
            syncBtn.classList.remove('syncing');
            syncBtn.textContent = 'Sync Failed';
        }
    });
}

function handleSearch() {
    renderUI();
}

function renderUI() {
    const query = (document.getElementById('search-input').value || '').toLowerCase();
    
    // Filter facts
    const filteredFacts = allFacts.filter(f => 
        f.statement.toLowerCase().includes(query) || 
        f.document.toLowerCase().includes(query)
    );
    
    // Deduplicate facts by statement
    const groupedFacts = {};
    filteredFacts.forEach(f => {
        if (!groupedFacts[f.statement]) {
            groupedFacts[f.statement] = {
                ids: [],
                statement: f.statement,
                entities: f.entities,
                units: f.units,
                time_scope: f.time_scope,
                evidence: []
            };
        }
        groupedFacts[f.statement].ids.push(f.id);
        groupedFacts[f.statement].evidence.push({
            id: f.id,
            quote: f.evidence_quote,
            confidence: f.confidence,
            document: f.document,
            page: f.page_number
        });
    });

    renderFactsList(Object.values(groupedFacts));
    
    // Filter and Deduplicate relationships based on query
    const filteredRels = allRelationships.filter(rel => 
        rel.fact1.statement.toLowerCase().includes(query) ||
        rel.fact2.statement.toLowerCase().includes(query) ||
        rel.explanation.toLowerCase().includes(query)
    );

    const groupedRels = {};
    filteredRels.forEach(rel => {
        const key = [rel.fact1.statement, rel.fact2.statement].sort().join('|') + '|' + rel.relationship_type;
        if (!groupedRels[key]) {
            groupedRels[key] = { ...rel, count: 0 };
        }
        groupedRels[key].count += 1;
    });
    
    const uniqueRels = Object.values(groupedRels);
    renderRelationshipsList(uniqueRels);

    // Update Required Cases Checklist
    let seenCorroboration = false;
    let seenContradiction = false;
    let seenContextual = false;
    let seenFailure = false;

    uniqueRels.forEach(rel => {
        if (rel.relationship_type === 'Corroboration') seenCorroboration = true;
        if (rel.relationship_type === 'Contradiction') seenContradiction = true;
        if (rel.relationship_type === 'Contextual Reconciliation') seenContextual = true;
        if (rel.relationship_type === 'Extraction Failure') seenFailure = true;
    });

    const toggleCheck = (id, met) => {
        const el = document.getElementById(id);
        if (el) {
            if (met) {
                el.classList.add('met');
                el.querySelector('.case-icon').textContent = '✔';
            } else {
                el.classList.remove('met');
                el.querySelector('.case-icon').textContent = '◯';
            }
        }
    };

    toggleCheck('case-corroboration', seenCorroboration);
    toggleCheck('case-contradiction', seenContradiction);
    toggleCheck('case-contextual', seenContextual);
    toggleCheck('case-failure', seenFailure);
}

function renderFactsList(groups) {
    const container = document.getElementById('facts-list');
    container.innerHTML = '';
    
    groups.forEach((group, index) => {
        const item = document.createElement('div');
        item.className = 'fact-item animate-in';
        item.style.animationDelay = `${index * 0.05}s`;
        item.dataset.factIds = group.ids.join(',');
        
        let metaHtml = '';
        if (group.time_scope && group.time_scope !== 'Unknown') metaHtml += ` | ${group.time_scope}`;
        if (group.units) metaHtml += ` | ${group.units}`;
        
        let evidenceHtml = group.evidence.map(e => `
            <div class="evidence-block" data-fact-id="${e.id}">
                <div class="evidence-quote">"${e.quote}"</div>
                <div class="evidence-meta">
                    <span class="evidence-doc" style="cursor:pointer; text-decoration:underline; title="Clicking would jump to PDF view">${e.document}</span>
                    <span>Page ${e.page}</span>
                    <span>Confidence: ${(e.confidence * 100).toFixed(0)}%</span>
                </div>
            </div>
        `).join('');

        item.innerHTML = `
            <div class="fact-claim">${group.statement} <span style="font-size:0.8rem; font-weight:normal; color:var(--text-secondary)">${metaHtml}</span></div>
            <div class="fact-evidence-group">
                ${evidenceHtml}
            </div>
        `;
        
        item.addEventListener('mouseenter', () => {
            document.querySelectorAll('.relationship-card').forEach(card => {
                const c1 = parseInt(card.dataset.fact1Id);
                const c2 = parseInt(card.dataset.fact2Id);
                if (group.ids.includes(c1) || group.ids.includes(c2)) {
                    card.classList.add('highlight');
                }
            });
        });
        item.addEventListener('mouseleave', () => {
            document.querySelectorAll('.relationship-card.highlight').forEach(card => card.classList.remove('highlight'));
        });
        
        container.appendChild(item);
    });
}

function renderRelationshipsList(relationships) {
    const container = document.getElementById('relationships-container');
    container.innerHTML = '';
    
    relationships.forEach((rel, index) => {
        const card = document.createElement('div');
        
        let layoutClass = 'layout-unrelated';
        if (rel.relationship_type.includes('Corroboration')) layoutClass = 'layout-corroboration';
        if (rel.relationship_type.includes('Contradiction')) layoutClass = 'layout-contradiction';
        if (rel.relationship_type.includes('Contextual')) layoutClass = 'layout-contextual';
        if (rel.relationship_type.includes('Failure')) layoutClass = 'layout-failure';
        
        card.className = `relationship-card animate-in ${layoutClass}`;
        card.style.animationDelay = `${index * 0.08}s`;
        card.dataset.fact1Id = rel.fact1.id;
        card.dataset.fact2Id = rel.fact2.id;
        
        let countBadge = '';
        if (rel.count > 1) {
            countBadge = `<span style="background:var(--text-secondary); color:white; font-size:0.7rem; padding:0.15rem 0.4rem; border-radius:12px; margin-left:1rem;">Seen in ${rel.count} document pairs</span>`;
        }

        card.innerHTML = `
            <div class="rel-header">
                <div>
                    <span class="rel-type">${rel.relationship_type}</span>
                    ${countBadge}
                </div>
                <span class="rel-reasoning">${rel.explanation}</span>
            </div>
            <div class="rel-body">
                <div class="fact-box">
                    <div class="fact-box-statement">${rel.fact1.statement}</div>
                    <div class="fact-box-meta">${rel.fact1.document}</div>
                </div>
                <div class="fact-box">
                    <div class="fact-box-statement">${rel.fact2.statement}</div>
                    <div class="fact-box-meta">${rel.fact2.document}</div>
                </div>
            </div>
        `;
        
        card.addEventListener('mouseenter', () => {
            document.querySelectorAll('.fact-item').forEach(item => {
                const ids = item.dataset.factIds.split(',').map(Number);
                if (ids.includes(rel.fact1.id) || ids.includes(rel.fact2.id)) {
                    item.classList.add('highlight');
                }
            });
        });
        card.addEventListener('mouseleave', () => {
            document.querySelectorAll('.fact-item.highlight').forEach(item => item.classList.remove('highlight'));
        });
        
        container.appendChild(card);
    });
}

window.fetchData = fetchData;
window.handleSearch = handleSearch;
