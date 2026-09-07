document.addEventListener('DOMContentLoaded', () => {
    fetchFacts();
    fetchRelationships();
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

    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        uploadStatus.textContent = data.message;
        uploadStatus.style.color = 'var(--success)';
        // Poll for new facts after a few seconds
        setTimeout(() => {
            fetchFacts();
            fetchRelationships();
        }, 5000);
    })
    .catch(error => {
        uploadStatus.textContent = `Error uploading ${file.name}`;
        uploadStatus.style.color = 'var(--danger)';
        console.error('Error:', error);
    });
}

function fetchFacts() {
    fetch('/api/facts')
    .then(res => res.json())
    .then(data => {
        const tbody = document.getElementById('facts-body');
        tbody.innerHTML = '';
        
        data.forEach(fact => {
            const tr = document.createElement('tr');
            
            // Format Value / Time
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
            tbody.appendChild(tr);
        });
    })
    .catch(err => console.error("Error fetching facts:", err));
}

function fetchRelationships() {
    fetch('/api/relationships')
    .then(res => res.json())
    .then(data => {
        const container = document.getElementById('relationships-container');
        container.innerHTML = '';
        
        data.forEach(rel => {
            const card = document.createElement('div');
            card.className = 'relationship-card';
            
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
            container.appendChild(card);
        });
    })
    .catch(err => console.error("Error fetching relationships:", err));
}
