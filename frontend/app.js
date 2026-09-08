let allFacts = [];
let allRelationships = [];
let isPolling = false;

document.addEventListener('DOMContentLoaded', () => {
    fetchData();
});

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
    Promise.all([
        fetch('/api/facts').then(res => res.json()),
        fetch('/api/relationships').then(res => res.json())
    ])
    .then(([facts, relationships]) => {
        if (forceRender || JSON.stringify(facts) !== JSON.stringify(allFacts) || 
            JSON.stringify(relationships) !== JSON.stringify(allRelationships)) {
            allFacts = facts;
            allRelationships = relationships;
            
            // Toggle Empty State
            const docsCount = new Set(facts.map(f => f.document)).size;
            document.getElementById('stat-docs').textContent = docsCount;
            document.getElementById('stat-facts').textContent = facts.length;
            document.getElementById('stat-rels').textContent = relationships.length;
            
            if (facts.length > 0) {
                document.getElementById('loading-state').style.display = 'none';
                document.getElementById('content-state').style.display = 'block';
            }
            
            renderUI();
        }
    })
    .catch(err => console.error("Error fetching data:", err));
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
    
    // Filter relationships based on query
    const filteredRels = allRelationships.filter(rel => 
        rel.fact1.statement.toLowerCase().includes(query) ||
        rel.fact2.statement.toLowerCase().includes(query) ||
        rel.explanation.toLowerCase().includes(query)
    );
    
    renderRelationshipsList(filteredRels);
}

function renderFactsList(groups) {
    const container = document.getElementById('facts-list');
    container.innerHTML = '';
    
    groups.forEach(group => {
        const item = document.createElement('div');
        item.className = 'fact-item';
        item.dataset.factIds = group.ids.join(',');
        
        let metaHtml = '';
        if (group.time_scope && group.time_scope !== 'Unknown') metaHtml += ` | ${group.time_scope}`;
        if (group.units) metaHtml += ` | ${group.units}`;
        
        let evidenceHtml = group.evidence.map(e => `
            <div class="evidence-block" data-fact-id="${e.id}">
                <div class="evidence-quote">"${e.quote}"</div>
                <div class="evidence-meta">
                    <span class="evidence-doc">${e.document}</span>
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
    
    relationships.forEach(rel => {
        const card = document.createElement('div');
        
        let layoutClass = 'layout-unrelated';
        if (rel.relationship_type.includes('Corroboration')) layoutClass = 'layout-corroboration';
        if (rel.relationship_type.includes('Contradiction')) layoutClass = 'layout-contradiction';
        if (rel.relationship_type.includes('Contextual')) layoutClass = 'layout-contextual';
        
        card.className = `relationship-card ${layoutClass}`;
        card.dataset.fact1Id = rel.fact1.id;
        card.dataset.fact2Id = rel.fact2.id;
        
        card.innerHTML = `
            <div class="rel-header">
                <span class="rel-type">${rel.relationship_type}</span>
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
