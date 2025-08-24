// Apple Sider - Enhanced UI JavaScript
// ================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🍎 Apple Sider v2.0 - Enhanced UI Loaded');
    
    // Initialize theme system
    initializeTheme();
    
    // Initialize upload zone
    initializeUploadZone();
    
    // Initialize console
    initializeConsole();
    
    // Initialize settings
    initializeSettings();
    
    // Add welcome message to console
    addConsoleMessage('Apple Sider Enhanced UI initialized successfully! 🚀', 'success');
});

// Theme System
// ============
function initializeTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const savedTheme = localStorage.getItem('theme') || 'light';
    
    // Apply saved theme
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeToggle(savedTheme);
    
    // Theme toggle event
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeToggle(newTheme);
            
            addConsoleMessage(`Theme switched to ${newTheme} mode`, 'info');
        });
    }
}

function updateThemeToggle(theme) {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.setAttribute('aria-checked', theme === 'dark');
        themeToggle.setAttribute('aria-label', `Switch to ${theme === 'light' ? 'dark' : 'light'} mode`);
    }
}

// Upload Zone
// ===========
function initializeUploadZone() {
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    
    if (!uploadZone || !fileInput) return;
    
    // Click to browse
    if (browseBtn) {
        browseBtn.addEventListener('click', function() {
            fileInput.click();
        });
    }
    
    uploadZone.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Drag and drop
    uploadZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });
    
    uploadZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
    });
    
    uploadZone.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });
    
    // File input change
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
}

function handleFileSelect(file) {
    addConsoleMessage(`File selected: ${file.name} (${formatFileSize(file.size)})`, 'info');
    
    if (!file.name.toLowerCase().endsWith('.xml')) {
        addConsoleMessage('Warning: Please select a valid XML file (Library.xml)', 'warning');
        return;
    }
    
    // Show file info
    showLibraryInfo(file);
    
    // Auto-upload or prepare for processing
    uploadFile(file);
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    addConsoleMessage('Uploading file...', 'info');
    showLoadingOverlay('Uploading Library.xml', 'Please wait while we process your file...');
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        hideLoadingOverlay();
        
        if (data.success) {
            addConsoleMessage(`✅ ${data.message}`, 'success');
            // Process the library data here
            processLibraryData(data);
        } else {
            addConsoleMessage(`❌ Upload failed: ${data.error}`, 'error');
        }
    })
    .catch(error => {
        hideLoadingOverlay();
        console.error('Upload error:', error);
        addConsoleMessage(`❌ Upload failed: ${error.message}`, 'error');
    });
}

// Console System
// ==============
function initializeConsole() {
    const clearBtn = document.getElementById('clear-console');
    const downloadBtn = document.getElementById('download-logs');
    
    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            clearConsole();
        });
    }
    
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function() {
            downloadConsoleLogs();
        });
    }
}

function addConsoleMessage(message, type = 'info') {
    const console = document.getElementById('console');
    if (!console) return;
    
    const timestamp = new Date().toLocaleTimeString();
    const line = document.createElement('div');
    line.className = `console-line ${type}`;
    line.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${message}`;
    
    console.appendChild(line);
    console.scrollTop = console.scrollHeight;
}

function clearConsole() {
    const console = document.getElementById('console');
    if (console) {
        console.innerHTML = '';
        addConsoleMessage('Console cleared', 'info');
    }
}

function downloadConsoleLogs() {
    const console = document.getElementById('console');
    if (!console) return;
    
    const logs = Array.from(console.children).map(line => line.textContent).join('\n');
    const blob = new Blob([logs], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `apple-sider-logs-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    addConsoleMessage('Logs downloaded', 'info');
}

// Settings System
// ===============
function initializeSettings() {
    const settingsForm = document.getElementById('settings-form');
    const applyBtn = document.getElementById('apply-settings');
    const resetBtn = document.getElementById('reset-settings');
    
    if (applyBtn) {
        applyBtn.addEventListener('click', function() {
            applySettings();
        });
    }
    
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            resetSettings();
        });
    }
    
    // Load saved settings
    loadSettings();
}

function applySettings() {
    const settings = getSettingsFromForm();
    localStorage.setItem('apple-sider-settings', JSON.stringify(settings));
    addConsoleMessage('Settings applied successfully', 'success');
}

function resetSettings() {
    localStorage.removeItem('apple-sider-settings');
    loadDefaultSettings();
    addConsoleMessage('Settings reset to defaults', 'info');
}

function loadSettings() {
    const savedSettings = localStorage.getItem('apple-sider-settings');
    if (savedSettings) {
        try {
            const settings = JSON.parse(savedSettings);
            applySettingsToForm(settings);
        } catch (e) {
            console.error('Failed to load settings:', e);
            loadDefaultSettings();
        }
    } else {
        loadDefaultSettings();
    }
}

function getSettingsFromForm() {
    return {
        outputFormat: document.getElementById('output-format')?.value || 'mp3',
        quality: document.getElementById('quality')?.value || 'high',
        targetDir: document.getElementById('target-dir')?.value || '',
        overwrite: document.getElementById('overwrite')?.checked || false
    };
}

function applySettingsToForm(settings) {
    if (document.getElementById('output-format')) {
        document.getElementById('output-format').value = settings.outputFormat || 'mp3';
    }
    if (document.getElementById('quality')) {
        document.getElementById('quality').value = settings.quality || 'high';
    }
    if (document.getElementById('target-dir')) {
        document.getElementById('target-dir').value = settings.targetDir || '';
    }
    if (document.getElementById('overwrite')) {
        document.getElementById('overwrite').checked = settings.overwrite || false;
    }
}

function loadDefaultSettings() {
    const defaults = {
        outputFormat: 'mp3',
        quality: 'high',
        targetDir: '',
        overwrite: false
    };
    applySettingsToForm(defaults);
}

// Library Processing
// ==================
function showLibraryInfo(file) {
    // This would parse the XML and show library statistics
    // For now, show mock data
    updateStats({
        tracks: '1,234',
        playlists: '45',
        genres: '67'
    });
    
    // Show the library info section
    const librarySection = document.getElementById('library-info');
    if (librarySection) {
        librarySection.style.display = 'block';
        librarySection.scrollIntoView({ behavior: 'smooth' });
    }
}

function updateStats(stats) {
    Object.keys(stats).forEach(key => {
        const element = document.getElementById(`stat-${key}`);
        if (element) {
            // Animate the number change
            animateNumber(element, 0, parseInt(stats[key].replace(',', '')), 1000);
        }
    });
}

function processLibraryData(data) {
    // This would handle the actual library processing
    addConsoleMessage('Processing library data...', 'info');
    
    // Show progress section
    const progressSection = document.getElementById('progress-section');
    if (progressSection) {
        progressSection.style.display = 'block';
        progressSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Simulate processing
    simulateProgress();
}

function simulateProgress() {
    let progress = 0;
    const progressBar = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    
    const interval = setInterval(() => {
        progress += Math.random() * 10;
        if (progress > 100) progress = 100;
        
        if (progressBar) {
            progressBar.style.width = progress + '%';
        }
        if (progressText) {
            progressText.textContent = Math.round(progress) + '%';
        }
        
        if (progress >= 100) {
            clearInterval(interval);
            addConsoleMessage('Processing completed! 🎉', 'success');
        }
    }, 200);
}

// Utility Functions
// =================
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function animateNumber(element, start, end, duration) {
    const startTime = performance.now();
    const change = end - start;
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const current = start + (change * easeOutCubic(progress));
        
        element.textContent = Math.round(current).toLocaleString();
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
}

function showLoadingOverlay(title, description) {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.querySelector('.loading-title').textContent = title;
        overlay.querySelector('.loading-description').textContent = description;
        overlay.style.display = 'flex';
    }
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

// Keyboard Shortcuts
// ==================
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to clear console
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        clearConsole();
    }
    
    // Ctrl/Cmd + T to toggle theme
    if ((e.ctrlKey || e.metaKey) && e.key === 't') {
        e.preventDefault();
        document.getElementById('theme-toggle')?.click();
    }
});
