// Defect Tracker Application
class DefectTracker {
    constructor() {
        this.defects = this.loadDefects();
        this.currentEditId = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.renderDefects();
        this.updateStats();
    }

    setupEventListeners() {
        // Add defect button
        document.getElementById('addDefectBtn').addEventListener('click', () => this.openModal());

        // Modal close
        document.querySelector('.close').addEventListener('click', () => this.closeModal());
        document.getElementById('cancelBtn').addEventListener('click', () => this.closeModal());
        
        // Click outside modal to close
        document.getElementById('defectModal').addEventListener('click', (e) => {
            if (e.target.id === 'defectModal') {
                this.closeModal();
            }
        });

        // Form submit
        document.getElementById('defectForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveDefect();
        });

        // Filters
        document.getElementById('statusFilter').addEventListener('change', () => this.renderDefects());
        document.getElementById('severityFilter').addEventListener('change', () => this.renderDefects());
        document.getElementById('searchInput').addEventListener('input', () => this.renderDefects());
    }

    loadDefects() {
        const stored = localStorage.getItem('blendDefects');
        return stored ? JSON.parse(stored) : [];
    }

    saveDefects() {
        localStorage.setItem('blendDefects', JSON.stringify(this.defects));
    }

    openModal(defectId = null) {
        const modal = document.getElementById('defectModal');
        const form = document.getElementById('defectForm');
        const modalTitle = document.getElementById('modalTitle');
        
        this.currentEditId = defectId;
        
        if (defectId) {
            modalTitle.textContent = 'Edit Defect';
            const defect = this.defects.find(d => d.id === defectId);
            if (defect) {
                document.getElementById('defectId').value = defect.id;
                document.getElementById('defectTitle').value = defect.title;
                document.getElementById('defectSeverity').value = defect.severity;
                document.getElementById('defectStatus').value = defect.status;
                document.getElementById('defectAssignee').value = defect.assignee || '';
                document.getElementById('defectEnvironment').value = defect.environment || 'production';
                document.getElementById('defectDescription').value = defect.description;
                document.getElementById('defectSteps').value = defect.steps || '';
                document.getElementById('defectUrl').value = defect.url || '';
            }
        } else {
            modalTitle.textContent = 'Add New Defect';
            form.reset();
            document.getElementById('defectId').value = '';
            document.getElementById('defectEnvironment').value = 'production';
        }
        
        modal.classList.add('show');
    }

    closeModal() {
        const modal = document.getElementById('defectModal');
        modal.classList.remove('show');
        this.currentEditId = null;
        document.getElementById('defectForm').reset();
    }

    saveDefect() {
        const formData = {
            id: document.getElementById('defectId').value || this.generateId(),
            title: document.getElementById('defectTitle').value.trim(),
            severity: document.getElementById('defectSeverity').value,
            status: document.getElementById('defectStatus').value,
            assignee: document.getElementById('defectAssignee').value.trim(),
            environment: document.getElementById('defectEnvironment').value,
            description: document.getElementById('defectDescription').value.trim(),
            steps: document.getElementById('defectSteps').value.trim(),
            url: document.getElementById('defectUrl').value.trim(),
            createdAt: this.currentEditId 
                ? this.defects.find(d => d.id === this.currentEditId)?.createdAt || new Date().toISOString()
                : new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };

        if (this.currentEditId) {
            const index = this.defects.findIndex(d => d.id === this.currentEditId);
            if (index !== -1) {
                this.defects[index] = formData;
            }
        } else {
            this.defects.unshift(formData);
        }

        this.saveDefects();
        this.renderDefects();
        this.updateStats();
        this.closeModal();
    }

    deleteDefect(id) {
        if (confirm('Are you sure you want to delete this defect?')) {
            this.defects = this.defects.filter(d => d.id !== id);
            this.saveDefects();
            this.renderDefects();
            this.updateStats();
        }
    }

    generateId() {
        return 'DEF-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    }

    getFilteredDefects() {
        const statusFilter = document.getElementById('statusFilter').value;
        const severityFilter = document.getElementById('severityFilter').value;
        const searchQuery = document.getElementById('searchInput').value.toLowerCase().trim();

        return this.defects.filter(defect => {
            const matchesStatus = statusFilter === 'all' || defect.status === statusFilter;
            const matchesSeverity = severityFilter === 'all' || defect.severity === severityFilter;
            const matchesSearch = searchQuery === '' || 
                defect.title.toLowerCase().includes(searchQuery) ||
                defect.description.toLowerCase().includes(searchQuery) ||
                (defect.assignee && defect.assignee.toLowerCase().includes(searchQuery)) ||
                (defect.url && defect.url.toLowerCase().includes(searchQuery));

            return matchesStatus && matchesSeverity && matchesSearch;
        });
    }

    renderDefects() {
        const defectsList = document.getElementById('defectsList');
        const filteredDefects = this.getFilteredDefects();

        if (filteredDefects.length === 0) {
            defectsList.innerHTML = `
                <div class="empty-state">
                    <h3>No defects found</h3>
                    <p>${this.defects.length === 0 ? 'Click "Add New Defect" to start tracking defects.' : 'Try adjusting your filters or search query.'}</p>
                </div>
            `;
            return;
        }

        defectsList.innerHTML = filteredDefects.map(defect => this.renderDefectCard(defect)).join('');
        
        // Attach event listeners to action buttons
        filteredDefects.forEach(defect => {
            const editBtn = document.querySelector(`[data-edit-id="${defect.id}"]`);
            const deleteBtn = document.querySelector(`[data-delete-id="${defect.id}"]`);
            
            if (editBtn) {
                editBtn.addEventListener('click', () => this.openModal(defect.id));
            }
            if (deleteBtn) {
                deleteBtn.addEventListener('click', () => this.deleteDefect(defect.id));
            }
        });
    }

    renderDefectCard(defect) {
        const createdDate = new Date(defect.createdAt).toLocaleDateString();
        const updatedDate = new Date(defect.updatedAt).toLocaleDateString();
        const isUpdated = defect.createdAt !== defect.updatedAt;

        return `
            <div class="defect-card ${defect.severity}">
                <div class="defect-header">
                    <div class="defect-title">${this.escapeHtml(defect.title)}</div>
                    <div class="defect-badges">
                        <span class="badge badge-severity-${defect.severity}">${defect.severity}</span>
                        <span class="badge badge-status-${defect.status}">${defect.status.replace('-', ' ')}</span>
                    </div>
                </div>
                
                <div class="defect-description">${this.escapeHtml(defect.description)}</div>
                
                ${defect.steps ? `<div class="defect-description" style="margin-top: 10px;"><strong>Steps to Reproduce:</strong><br>${this.formatSteps(defect.steps)}</div>` : ''}
                
                <div class="defect-meta">
                    <div class="meta-item">
                        <strong>ID:</strong> ${defect.id}
                    </div>
                    <div class="meta-item">
                        <strong>Environment:</strong> ${defect.environment || 'production'}
                    </div>
                    ${defect.assignee ? `<div class="meta-item"><strong>Assignee:</strong> ${this.escapeHtml(defect.assignee)}</div>` : ''}
                    ${defect.url ? `<div class="meta-item"><strong>URL:</strong> <code>${this.escapeHtml(defect.url)}</code></div>` : ''}
                    <div class="meta-item">
                        <strong>Created:</strong> ${createdDate}
                    </div>
                    ${isUpdated ? `<div class="meta-item"><strong>Updated:</strong> ${updatedDate}</div>` : ''}
                </div>
                
                <div class="defect-actions">
                    <button class="btn btn-edit" data-edit-id="${defect.id}">Edit</button>
                    <button class="btn btn-danger" data-delete-id="${defect.id}">Delete</button>
                </div>
            </div>
        `;
    }

    formatSteps(steps) {
        return steps.split('\n').map(step => step.trim()).filter(step => step).join('<br>');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    updateStats() {
        const total = this.defects.length;
        const critical = this.defects.filter(d => d.severity === 'critical').length;
        const open = this.defects.filter(d => d.status === 'open').length;
        const resolved = this.defects.filter(d => d.status === 'resolved' || d.status === 'closed').length;

        document.getElementById('totalDefects').textContent = total;
        document.getElementById('criticalDefects').textContent = critical;
        document.getElementById('openDefects').textContent = open;
        document.getElementById('resolvedDefects').textContent = resolved;
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DefectTracker();
});
