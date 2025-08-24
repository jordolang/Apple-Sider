// Apple Sider - JavaScript Application

class AppleSider {
    constructor() {
        this.websocket = null;
        this.autoScroll = true;
        this.uploadedLibrary = null;
        this.currentStatus = null;
        this.progressInterval = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadSettings();
        this.connectWebSocket();
        this.addConsoleLine('🍎 Apple Sider Ready - Upload your Library.xml to begin', 'welcome');
    }
    
    setupEventListeners() {
        // File upload
        const fileInput = document.getElementById('fileInput');
        const uploadZone = document.getElementById('uploadZone');
        
        fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        
        // Drag and drop
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });
        
        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });
        
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0 && files[0].name.endsWith('.xml')) {
                this.processFile(files[0]);
            }
        });
        
        uploadZone.addEventListener('click', () => {
            fileInput.click();
        });
        
        // Download control
        document.getElementById('startDownload').addEventListener('click', () => this.startDownload());
        document.getElementById('pauseBtn').addEventListener('click', () => this.pauseDownload());
        document.getElementById('retryBtn').addEventListener('click', () => this.retryFailed());
        document.getElementById('clearBtn').addEventListener('click', () => this.clearQueue());
        
        // Settings
        document.getElementById('downloadLocation').addEventListener('change', () => this.saveSettings());
        document.getElementById('folderStructure').addEventListener('change', () => this.saveSettings());
        document.getElementById('concurrentDownloads').addEventListener('change', () => this.saveSettings());
        document.getElementById('metadataSource').addEventListener('change', () => this.saveSettings());
    }
    
    handleFileUpload(event) {
        const file = event.target.files[0];
        if (file && file.name.endsWith('.xml')) {
            this.processFile(file);
        } else {
            this.showError('Please select a valid XML file');
        }
    }
    
    async processFile(file) {
        this.showLoading(true);
        this.addConsoleLine(`📁 Processing ${file.name}...`, 'info');
        
        try {
            const formData = new FormData();
            formData.append('library', file);
            
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.uploadedLibrary = result;
                this.showLibraryInfo(result);
                this.addConsoleLine(`✅ Successfully parsed ${result.valid_tracks} valid tracks`, 'success');
            } else {
                this.showError(result.error);
                this.addConsoleLine(`❌ Error: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showError(`Failed to process file: ${error.message}`);
            this.addConsoleLine(`💥 Error: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    showLibraryInfo(data) {
        document.getElementById('totalTracks').textContent = data.total_tracks;
        document.getElementById('validTracks').textContent = data.valid_tracks;
        document.getElementById('estimatedHours').textContent = data.estimated_hours;
        
        document.getElementById('uploadSection').style.display = 'none';
        document.getElementById('libraryInfo').style.display = 'block';
    }
    
    async startDownload() {
        if (!this.uploadedLibrary) {
            this.showError('Please upload a library file first');
            return;
        }
        
        this.addConsoleLine('🚀 Starting download process...', 'info');
        
        try {
            const response = await fetch('/api/start-download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    library_data: this.uploadedLibrary
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                document.getElementById('libraryInfo').style.display = 'none';
                document.getElementById('progressSection').style.display = 'block';
                this.startProgressMonitoring();
                this.addConsoleLine(`✅ Download started - ${result.queued_count} tracks queued`, 'success');
            } else {
                this.showError(result.error);
                this.addConsoleLine(`❌ Failed to start: ${result.error}`, 'error');
            }
        } catch (error) {
            this.showError(`Failed to start download: ${error.message}`);
            this.addConsoleLine(`💥 Error: ${error.message}`, 'error');
        }
    }
    
    async pauseDownload() {
        try {
            const response = await fetch('/api/pause-download', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                this.addConsoleLine('⏸️ Downloads paused', 'warning');
                document.getElementById('pauseBtn').textContent = '▶️ Resume';
            }
        } catch (error) {
            this.addConsoleLine(`💥 Error pausing: ${error.message}`, 'error');
        }
    }
    
    async retryFailed() {
        try {
            const response = await fetch('/api/retry-failed', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                this.addConsoleLine(`🔄 Retrying ${result.retried_count} failed downloads`, 'info');
            }
        } catch (error) {
            this.addConsoleLine(`💥 Error retrying: ${error.message}`, 'error');
        }
    }
    
    async clearQueue() {
        if (!confirm('Are you sure you want to clear the entire download queue?')) {
            return;
        }
        
        try {
            const response = await fetch('/api/clear-queue', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                this.addConsoleLine('🗑️ Download queue cleared', 'info');
                this.resetInterface();
            }
        } catch (error) {
            this.addConsoleLine(`💥 Error clearing queue: ${error.message}`, 'error');
        }
    }
    
    startProgressMonitoring() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
        
        this.progressInterval = setInterval(() => {
            this.updateProgress();
        }, 2000);
        
        // Initial update
        this.updateProgress();
    }
    
    async updateProgress() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            
            this.currentStatus = status;
            this.updateProgressDisplay(status);
            
            // Stop monitoring if complete
            if (status.queued === 0 && status.active === 0 && status.total_tasks > 0) {
                clearInterval(this.progressInterval);
                this.addConsoleLine('🎉 All downloads completed!', 'success');
            }
        } catch (error) {
            console.error('Failed to update progress:', error);
        }
    }
    
    updateProgressDisplay(status) {
        document.getElementById('progressFill').style.width = `${status.progress_percent}%`;
        document.getElementById('progressText').textContent = `${status.progress_percent}%`;
        
        document.getElementById('completedCount').textContent = status.completed;
        document.getElementById('activeCount').textContent = status.active;
        document.getElementById('queuedCount').textContent = status.queued;
        document.getElementById('failedCount').textContent = status.failed;
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            console.log('WebSocket connected');
        };
        
        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.addConsoleLine(data.message, data.level);
        };
        
        this.websocket.onclose = () => {
            console.log('WebSocket disconnected');
            // Attempt to reconnect after 5 seconds
            setTimeout(() => {
                this.connectWebSocket();
            }, 5000);
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    addConsoleLine(message, level = 'info') {
        const console = document.getElementById('console');
        const line = document.createElement('div');
        line.className = `console-line ${level}`;
        line.textContent = `${new Date().toLocaleTimeString()} ${message}`;
        
        console.appendChild(line);
        
        // Keep only last 1000 lines
        const lines = console.children;
        if (lines.length > 1000) {
            console.removeChild(lines[0]);
        }
        
        // Auto-scroll if enabled
        if (this.autoScroll) {
            console.scrollTop = console.scrollHeight;
        }
    }
    
    loadSettings() {
        const settings = JSON.parse(localStorage.getItem('appleSiderSettings') || '{}');
        
        if (settings.downloadLocation) {
            document.getElementById('downloadLocation').value = settings.downloadLocation;
        }
        if (settings.folderStructure) {
            document.getElementById('folderStructure').value = settings.folderStructure;
        }
        if (settings.concurrentDownloads) {
            document.getElementById('concurrentDownloads').value = settings.concurrentDownloads;
        }
        if (settings.metadataSource) {
            document.getElementById('metadataSource').value = settings.metadataSource;
        }
    }
    
    saveSettings() {
        const settings = {
            downloadLocation: document.getElementById('downloadLocation').value,
            folderStructure: document.getElementById('folderStructure').value,
            concurrentDownloads: parseInt(document.getElementById('concurrentDownloads').value),
            metadataSource: document.getElementById('metadataSource').value
        };
        
        localStorage.setItem('appleSiderSettings', JSON.stringify(settings));
        
        // Send to server
        fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        }).catch(error => {
            console.error('Failed to save settings to server:', error);
        });
        
        this.addConsoleLine('⚙️ Settings saved', 'info');
    }
    
    resetSettings() {
        if (confirm('Reset all settings to defaults?')) {
            localStorage.removeItem('appleSiderSettings');
            document.getElementById('downloadLocation').value = '~/Music/Apple-Sider';
            document.getElementById('folderStructure').value = 'flat';
            document.getElementById('concurrentDownloads').value = 3;
            document.getElementById('metadataSource').value = 'all';
            this.saveSettings();
        }
    }
    
    resetInterface() {
        this.uploadedLibrary = null;
        document.getElementById('uploadSection').style.display = 'block';
        document.getElementById('libraryInfo').style.display = 'none';
        document.getElementById('progressSection').style.display = 'none';
        
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
    }
    
    showError(message) {
        alert(`Error: ${message}`);
    }
    
    showLoading(show) {
        document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
    }
}

// Global functions for HTML onclick handlers
function toggleSettings() {
    const content = document.getElementById('settingsContent');
    const toggle = document.getElementById('settingsToggle');
    
    content.classList.toggle('open');
    toggle.classList.toggle('open');
}

function clearConsole() {
    const console = document.getElementById('console');
    console.innerHTML = '';
    app.addConsoleLine('🧹 Console cleared', 'info');
}

function toggleAutoScroll() {
    app.autoScroll = !app.autoScroll;
    document.getElementById('autoScrollStatus').textContent = app.autoScroll ? 'ON' : 'OFF';
    app.addConsoleLine(`📜 Auto-scroll ${app.autoScroll ? 'enabled' : 'disabled'}`, 'info');
}

function saveSettings() {
    app.saveSettings();
}

function resetSettings() {
    app.resetSettings();
}

// Initialize the application
const app = new AppleSider();
