let currentFacts = [];
let currentRelationships = [];
let isPolling = false;

document.addEventListener('DOMContentLoaded', () => {
    fetchData();
});

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const uploadStatus = document.getElementById('upload-status');

dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        handleFiles(e.dataTransfer.files);
    }
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
        handleFiles(fileInput.files);
    }
});

function handleFiles(files) {
    Array.from(files).forEach(file => {
        uploadFile(file);
    });
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    uploadStatus.textContent = `Uploading ${file.name}...`;
    uploadStatus.style.color = 'var(--text-primary)';

    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        uploadStatus.textContent = data.message;
        uploadStatus.style.color = 'var(--success)';
        if (!isPolling) {
            startPolling();
        }
    })
    .catch(error => {
        uploadStatus.textContent = `Error uploading ${file.name}`;
        uploadStatus.style.color = 'var(--danger)';
        console.error('Error:', error);
    });
}

function startPolling() {
    isPolling = true;
    const pollInterval = setInterval(() => {
        fetchData();
        // optionally stop polling after a certain time or when data stops changing
    }, 3000);
}

function fetchData() {
    Promise.all([
        fetch('/api/facts').then(res => res.json()),
        fetch('/api/relationships').then(res => res.json())
    ])
    .then(([facts, relationships]) => {
        if (JSON.stringify(facts) !== JSON.stringify(currentFacts) || 
            JSON.stringify(relationships) !== JSON.stringify(currentRelationships)) {
            currentFacts = facts;
            currentRelationships = relationships;
            renderFacts(facts);
            renderRelationships(relationships);
        }
    })
    .catch(err => console.error("Error fetching data:", err));
}

function renderFacts(facts) {
    const tbody = document.getElementById('facts-body');
    tbody.innerHTML = '';
    
    facts.forEach(fact => {
        const tr = document.createElement('tr');
        tr.className = 'fact-row';
        tr.dataset.factId = fact.id;
        
        let valTime = '';
        if (fact.units) valTime += `${fact.units} `;
        if (fact.time_scope) valTime += `(${fact.time_scope})`;
        
        tr.innerHTML = `
            <td><strong>${fact.statement}</strong><br><small style="color:var(--text-secondary)">Entities: ${fact.entities.join(', ')}</small></td>
            <td>${valTime}</td>
            <td>${fact.document} (pg ${fact.page_number})</td>
            <td>${(fact.confidence * 100).toFixed(0)}%</td>
            <td class="evidence-cell">"${fact.evidence_quote}"</td>
        `;
        
        // Add hover effects to highlight corresponding relationships
        tr.addEventListener('mouseenter', () => {
            document.querySelectorAll('.relationship-card').forEach(card => {
                if (card.dataset.fact1Id == fact.id || card.dataset.fact2Id == fact.id) {
                    card.classList.add('highlight');
                }
            });
        });
        tr.addEventListener('mouseleave', () => {
            document.querySelectorAll('.relationship-card.highlight').forEach(card => {
                card.classList.remove('highlight');
            });
        });
        
        tbody.appendChild(tr);
    });
}

function renderRelationships(relationships) {
    const container = document.getElementById('relationships-container');
    container.innerHTML = '';
    
    relationships.forEach(rel => {
        const card = document.createElement('div');
        card.className = 'relationship-card';
        card.dataset.fact1Id = rel.fact1.id;
        card.dataset.fact2Id = rel.fact2.id;
        
        let typeClass = 'unrelated';
        if (rel.relationship_type.includes('Corroboration')) typeClass = 'corroboration';
        if (rel.relationship_type.includes('Contradiction')) typeClass = 'contradiction';
        if (rel.relationship_type.includes('Contextual')) typeClass = 'contextual';
        
        card.innerHTML = `
            <span class="rel-type ${typeClass}">${rel.relationship_type}</span>
            
            <div class="fact-box">
                <div>${rel.fact1.statement}</div>
                <div class="doc-name">${rel.fact1.document}</div>
            </div>
            
            <div class="fact-box">
                <div>${rel.fact2.statement}</div>
                <div class="doc-name">${rel.fact2.document}</div>
            </div>
            
            <div class="explanation">
                <strong>Reasoning:</strong> ${rel.explanation}
            </div>
        `;
        
        // Add hover effects to highlight corresponding facts
        card.addEventListener('mouseenter', () => {
            document.querySelectorAll('.fact-row').forEach(row => {
                if (row.dataset.factId == rel.fact1.id || row.dataset.factId == rel.fact2.id) {
                    row.classList.add('highlight');
                }
            });
        });
        card.addEventListener('mouseleave', () => {
            document.querySelectorAll('.fact-row.highlight').forEach(row => {
                row.classList.remove('highlight');
            });
        });
        
        container.appendChild(card);
    });
}

// Ensure the refresh buttons use the new fetchData function
window.fetchFacts = fetchData;
window.fetchRelationships = fetchData;
