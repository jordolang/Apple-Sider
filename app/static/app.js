/* ============================================================================
   Apple Sider - Next-Gen JavaScript Application
   Modern ES6+ with Advanced Animations & Features
   ============================================================================ */

class AppleSider {
    constructor() {
        // Core Properties
        this.websocket = null;
        this.autoScroll = true;
        this.uploadedLibrary = null;
        this.currentStatus = null;
        this.progressInterval = null;
        this.animationFrame = null;
        
        // Theme & UI State
        this.currentTheme = 'light';
        this.reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.isOnline = navigator.onLine;
        
        // Animation Controllers
        this.intersectionObserver = null;
        this.particleSystem = null;
        this.soundEnabled = false;
        
        // Keyboard Shortcuts
        this.shortcuts = new Map([
            ['KeyU', { action: 'focusUpload', ctrl: true, description: 'Focus upload area' }],
            ['KeyT', { action: 'toggleTheme', ctrl: true, description: 'Toggle theme' }],
            ['KeyS', { action: 'toggleSettings', ctrl: true, description: 'Toggle settings' }],
            ['KeyC', { action: 'clearConsole', ctrl: true, shift: true, description: 'Clear console' }],
            ['Escape', { action: 'closeFocus', description: 'Close focused element' }]
        ]);
        
        // Performance Metrics
        this.performanceMetrics = {
            uploadStart: null,
            uploadEnd: null,
            downloadStart: null,
            downloadEnd: null
        };
        
        // Initialize the application
        this.init();
    }
    
    /**
     * Initialize the application
     */
    async init() {
        try {
            // Detect system preferences
            this.detectSystemPreferences();
            
            // Initialize theme system
            this.initializeTheme();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Initialize animations
            if (!this.reducedMotion) {
                this.initializeAnimations();
                this.initializeParticleSystem();
            }
            
            // Setup observers
            this.setupIntersectionObserver();
            
            // Load user settings
            this.loadSettings();
            
            // Connect to WebSocket
            this.connectWebSocket();
            
            // Initialize keyboard shortcuts
            this.initializeKeyboardShortcuts();
            
            // Setup PWA features
            this.initializePWA();
            
            // Add welcome message
            this.addConsoleLine('🍎 Apple Sider Ready - Upload your Library.xml to begin', 'welcome');
            
            // Perform startup health check
            this.performHealthCheck();
            
        } catch (error) {
            console.error('Failed to initialize Apple Sider:', error);
            this.showNotification('Failed to initialize application', 'error');
        }
    }
    
    /**
     * Detect system preferences and capabilities
     */
    detectSystemPreferences() {
        // Detect color scheme preference
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)');
        this.currentTheme = prefersDark.matches ? 'dark' : 'light';
        
        // Listen for changes
        prefersDark.addEventListener('change', (e) => {
            if (!localStorage.getItem('apple-sider-theme-override')) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });
        
        // Detect reduced motion preference
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
        this.reducedMotion = prefersReducedMotion.matches;
        
        prefersReducedMotion.addEventListener('change', (e) => {
            this.reducedMotion = e.matches;
            if (e.matches && this.particleSystem) {
                this.particleSystem.destroy();
            }
        });
        
        // Detect network status
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.showNotification('Connection restored', 'success');
        });
        
        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.showNotification('Connection lost - working offline', 'warning');
        });
    }
    
    /**
     * Initialize theme system
     */
    initializeTheme() {
        // Check for saved theme preference
        const savedTheme = localStorage.getItem('apple-sider-theme');
        if (savedTheme) {
            this.currentTheme = savedTheme;
        }
        
        this.setTheme(this.currentTheme);
        
        // Setup theme toggle button
        const themeToggle = document.getElementById('themeToggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
    }
    
    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        // File upload with enhanced drag & drop
        this.setupFileUpload();
        
        // Download controls with improved UX
        this.setupDownloadControls();
        
        // Settings with real-time validation
        this.setupSettings();
        
        // Console controls
        this.setupConsoleControls();
        
        // Window events
        this.setupWindowEvents();
    }
    
    /**
     * Setup enhanced file upload with visual feedback
     */
    setupFileUpload() {
        const fileInput = document.getElementById('fileInput');
        const uploadZone = document.getElementById('uploadZone');
        
        if (!fileInput || !uploadZone) return;
        
        // File input change
        fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        
        // Enhanced drag and drop
        let dragCounter = 0;
        
        uploadZone.addEventListener('dragenter', (e) => {
            e.preventDefault();
            dragCounter++;
            uploadZone.classList.add('dragover');
            this.animateUploadZone('dragenter');
        });
        
        uploadZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dragCounter--;
            if (dragCounter === 0) {
                uploadZone.classList.remove('dragover');
                this.animateUploadZone('dragleave');
            }
        });
        
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
        });
        
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dragCounter = 0;
            uploadZone.classList.remove('dragover');
            
            const files = Array.from(e.dataTransfer.files);
            this.handleFileDrop(files);
        });
        
        // Click to upload
        uploadZone.addEventListener('click', () => {
            this.triggerFileInput();
        });
        
        // Keyboard accessibility
        uploadZone.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.triggerFileInput();
            }
        });
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
            formData.append('file', file);
            
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.uploadedLibrary = result;
                this.showLibraryInfo(result);
                this.addConsoleLine(`✅ Successfully parsed ${result.data.tracks} tracks`, 'success');
            } else {
                this.showError(result.error || 'Unknown error occurred');
                this.addConsoleLine(`❌ Error: ${result.error || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            this.showError(`Failed to process file: ${error.message}`);
            this.addConsoleLine(`💥 Error: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }
    
    showLibraryInfo(result) {
        // Use the correct data structure from Flask response
        const tracks = result.data.tracks || 0;
        const artists = result.data.artists || 0;
        const estimatedHours = Math.ceil(tracks / 100); // Rough estimate: 100 tracks per hour
        
        document.getElementById('totalTracks').textContent = tracks;
        document.getElementById('validTracks').textContent = tracks; // For now, assume all tracks are valid
        document.getElementById('estimatedHours').textContent = estimatedHours;
        
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
    
    // Add missing methods that are referenced but not implemented
    triggerFileInput() {
        document.getElementById('fileInput').click();
    }
    
    handleFileDrop(files) {
        if (files.length > 0) {
            const file = files[0];
            if (file.name.endsWith('.xml')) {
                this.processFile(file);
            } else {
                this.showError('Please drop a valid XML file');
            }
        }
    }
    
    animateUploadZone(action) {
        // Simple animation placeholder - can be enhanced later
        const zone = document.getElementById('uploadZone');
        if (action === 'dragenter') {
            zone.style.transform = 'scale(1.02)';
        } else {
            zone.style.transform = 'scale(1)';
        }
    }
    
    performHealthCheck() {
        // Check if the backend is responding
        fetch('/health')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'healthy') {
                    this.addConsoleLine('✅ Backend health check passed', 'success');
                } else {
                    this.addConsoleLine('⚠️ Backend health check failed', 'warning');
                }
            })
            .catch(error => {
                this.addConsoleLine('❌ Could not connect to backend', 'error');
            });
    }
    
    showNotification(message, type) {
        // Simple notification system
        console.log(`[${type.toUpperCase()}] ${message}`);
        this.addConsoleLine(`📢 ${message}`, type);
    }
    
    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        localStorage.setItem('apple-sider-theme', theme);
    }
    
    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
        this.addConsoleLine(`🎨 Theme switched to ${newTheme}`, 'info');
    }
    
    initializeAnimations() {
        // Placeholder for animations
        this.addConsoleLine('🎬 Animations initialized', 'info');
    }
    
    adjustUIForScreenSize() {
        // Responsive UI adjustments
        const width = window.innerWidth;
        if (width < 768) {
            document.body.classList.add('mobile');
        } else {
            document.body.classList.remove('mobile');
        }
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Set up download control buttons and progress tracking
     */
    setupDownloadControls() {
        // Download control buttons
        const startDownloadBtn = document.getElementById('startDownload');
        const pauseBtn = document.getElementById('pauseBtn');
        const retryBtn = document.getElementById('retryBtn');
        const clearBtn = document.getElementById('clearBtn');
        
        if (startDownloadBtn) {
            startDownloadBtn.addEventListener('click', () => this.startDownload());
        }
        
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => {
                const isPaused = pauseBtn.getAttribute('aria-pressed') === 'true';
                pauseBtn.setAttribute('aria-pressed', !isPaused);
                
                if (isPaused) {
                    // Resume downloads
                    this.resumeDownload();
                    pauseBtn.querySelector('.button-text').textContent = 'Pause';
                    pauseBtn.querySelector('.button-icon').textContent = '⏸️';
                } else {
                    // Pause downloads
                    this.pauseDownload();
                    pauseBtn.querySelector('.button-text').textContent = 'Resume';
                    pauseBtn.querySelector('.button-icon').textContent = '▶️';
                }
            });
        }
        
        if (retryBtn) {
            retryBtn.addEventListener('click', () => {
                this.retryFailed();
            });
        }
        
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearQueue();
            });
        }
    }
    
    /**
     * Setup settings controls with improved interactions
     */
    setupSettings() {
        // Settings fields with real-time validation
        const downloadLocation = document.getElementById('downloadLocation');
        const folderStructure = document.getElementById('folderStructure');
        const concurrentDownloads = document.getElementById('concurrentDownloads');
        const metadataSource = document.getElementById('metadataSource');
        
        // Settings details/summary toggle behavior
        const settingsToggle = document.getElementById('settingsToggle');
        if (settingsToggle) {
            settingsToggle.addEventListener('click', () => {
                const details = settingsToggle.closest('details');
                if (details) {
                    // Update aria-expanded attribute
                    const isExpanded = details.hasAttribute('open');
                    settingsToggle.setAttribute('aria-expanded', !isExpanded);
                    
                    // Play animation/sound
                    if (!this.reducedMotion) {
                        this.animateSettingsToggle(!isExpanded);
                    }
                    
                    if (this.soundEnabled) {
                        this.playSoundEffect('toggle');
                    }
                }
            });
        }
        
        // Input validation and autosave
        if (downloadLocation) {
            downloadLocation.addEventListener('input', (e) => this.validatePathInput(e.target));
            downloadLocation.addEventListener('change', () => this.saveSettings());
        }
        
        if (folderStructure) {
            folderStructure.addEventListener('change', () => {
                this.saveSettings();
                this.showStructurePreview(folderStructure.value);
            });
        }
        
        if (concurrentDownloads) {
            // Validate numeric input with min/max
            concurrentDownloads.addEventListener('input', (e) => {
                const value = parseInt(e.target.value);
                if (isNaN(value) || value < 1) {
                    e.target.value = 1;
                } else if (value > 10) {
                    e.target.value = 10;
                }
            });
            concurrentDownloads.addEventListener('change', () => this.saveSettings());
        }
        
        if (metadataSource) {
            metadataSource.addEventListener('change', () => this.saveSettings());
        }
        
        // Save and reset buttons
        const saveSettingsBtn = document.getElementById('saveSettingsBtn');
        const resetSettingsBtn = document.getElementById('resetSettingsBtn');
        
        if (saveSettingsBtn) {
            saveSettingsBtn.addEventListener('click', () => this.saveSettings());
        }
        
        if (resetSettingsBtn) {
            resetSettingsBtn.addEventListener('click', () => this.resetSettings());
        }
    }
    
    /**
     * Setup console controls with enhanced functionality
     */
    setupConsoleControls() {
        const clearConsoleBtn = document.getElementById('clearConsoleBtn');
        const toggleAutoScrollBtn = document.getElementById('toggleAutoScrollBtn');
        const consoleOutput = document.getElementById('console');
        
        if (clearConsoleBtn) {
            clearConsoleBtn.addEventListener('click', () => this.clearConsole());
        }
        
        if (toggleAutoScrollBtn) {
            toggleAutoScrollBtn.addEventListener('click', () => this.toggleAutoScroll());
        }
        
        // Make console searchable with Ctrl+F support
        if (consoleOutput) {
            // Enable text selection
            consoleOutput.addEventListener('mousedown', (e) => {
                // Allow text selection when holding shift
                if (e.shiftKey) {
                    e.stopPropagation();
                }
            });
            
            // Double-click to copy line
            consoleOutput.addEventListener('dblclick', (e) => {
                const line = e.target.closest('.console-line');
                if (line) {
                    this.copyToClipboard(line.textContent);
                    this.showNotification('Line copied to clipboard', 'info');
                }
            });
        }
    }
    
    /**
     * Setup global window event listeners
     */
    setupWindowEvents() {
        // Listen for before unload to warn about active downloads
        window.addEventListener('beforeunload', (e) => {
            if (this.currentStatus && (this.currentStatus.active > 0 || this.currentStatus.queued > 0)) {
                // Show warning before leaving page
                const message = 'Downloads are still in progress. Are you sure you want to leave?';
                e.returnValue = message;
                return message;
            }
        });
        
        // Listen for visibility change to pause updates when tab is inactive
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                // Reduce update frequency when tab is not visible
                if (this.progressInterval) {
                    clearInterval(this.progressInterval);
                    this.progressInterval = setInterval(() => this.updateProgress(), 10000); // Update every 10s
                }
            } else {
                // Resume normal update frequency when tab is visible again
                if (this.progressInterval) {
                    clearInterval(this.progressInterval);
                    this.progressInterval = setInterval(() => this.updateProgress(), 2000); // Update every 2s
                }
                this.updateProgress(); // Immediate update when returning to tab
            }
        });
        
        // Listen for resize events to reposition elements
        window.addEventListener('resize', this.debounce(() => {
            // Adjust UI based on screen size
            this.adjustUIForScreenSize();
        }, 250));
        
        // Initial UI adjustment
        this.adjustUIForScreenSize();
    }
    
    /**
     * Set up the Intersection Observer for scroll animations
     */
    setupIntersectionObserver() {
        if (!window.IntersectionObserver || this.reducedMotion) return;
        
        this.intersectionObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Apply animation based on data-aos attribute
                    const el = entry.target;
                    const animation = el.dataset.aos;
                    const delay = el.dataset.aosDelay || 0;
                    
                    if (animation) {
                        setTimeout(() => {
                            el.style.opacity = '1';
                            el.style.transform = 'translateY(0)';
                            el.style.transition = `opacity 0.6s ease, transform 0.6s ease`;
                        }, delay);
                        
                        // Unobserve after animating
                        this.intersectionObserver.unobserve(el);
                    }
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });
        
        // Observe elements with data-aos attribute
        document.querySelectorAll('[data-aos]').forEach(el => {
            el.style.opacity = '0';
            
            // Set initial transform based on animation type
            const animation = el.dataset.aos;
            if (animation === 'fade-in') {
                el.style.transform = 'translateY(0)';
            } else if (animation === 'slide-up') {
                el.style.transform = 'translateY(30px)';
            } else if (animation === 'slide-down') {
                el.style.transform = 'translateY(-30px)';
            } else if (animation === 'slide-left') {
                el.style.transform = 'translateX(30px)';
            } else if (animation === 'slide-right') {
                el.style.transform = 'translateX(-30px)';
            }
            
            this.intersectionObserver.observe(el);
        });
    }
    
    /**
     * Initialize keyboard shortcuts
     */
    initializeKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Don't handle shortcuts when focus is in input elements
            if (e.target.matches('input, textarea, select')) return;
            
            this.shortcuts.forEach((shortcut, key) => {
                const ctrlMatch = shortcut.ctrl ? e.ctrlKey : true;
                const shiftMatch = shortcut.shift ? e.shiftKey : true;
                const altMatch = shortcut.alt ? e.altKey : true;
                
                if (e.code === key && ctrlMatch && shiftMatch && altMatch) {
                    e.preventDefault();
                    
                    // Execute the shortcut action
                    switch (shortcut.action) {
                        case 'focusUpload':
                            this.focusElement('uploadZone');
                            break;
                        case 'toggleTheme':
                            this.toggleTheme();
                            break;
                        case 'toggleSettings':
                            this.toggleSettings();
                            break;
                        case 'clearConsole':
                            this.clearConsole();
                            break;
                        case 'closeFocus':
                            this.handleEscapeKey();
                            break;
                    }
                }
            });
        });
    }
    
    /**
     * Initialize basic PWA features
     */
    initializePWA() {
        // Check if the browser supports service workers
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/service-worker.js').then(registration => {
                    console.log('ServiceWorker registration successful with scope: ', registration.scope);
                }).catch(error => {
                    console.log('ServiceWorker registration failed: ', error);
                });
            });
        }
        
        // Listen for beforeinstallprompt event
        window.addEventListener('beforeinstallprompt', (e) => {
            // Prevent Chrome 67 and earlier from automatically showing the prompt
            e.preventDefault();
            // Store the event so it can be triggered later
            this.deferredPrompt = e;
            // Show the install button or other UI element
            this.showInstallPrompt();
        });
    }
    
    /**
     * Initialize the particle system for visual effects
     */
    initializeParticleSystem() {
        // Skip if reduced motion is enabled
        if (this.reducedMotion) return;
        
        // Initialize particle systems for animations
        this.particleSystem = {
            particles: [],
            canvas: null,
            ctx: null,
            initialized: false,
            targetElement: null,
            
            init: (targetId) => {
                // Create canvas dynamically
                const target = document.getElementById(targetId);
                if (!target) return false;
                
                this.particleSystem.targetElement = target;
                
                const canvas = document.createElement('canvas');
                canvas.className = 'particle-canvas';
                canvas.style.position = 'absolute';
                canvas.style.top = '0';
                canvas.style.left = '0';
                canvas.style.width = '100%';
                canvas.style.height = '100%';
                canvas.style.pointerEvents = 'none';
                canvas.style.zIndex = '1';
                
                // Position the target element relatively if it's not already
                const targetPosition = getComputedStyle(target).position;
                if (targetPosition === 'static') {
                    target.style.position = 'relative';
                }
                
                target.appendChild(canvas);
                
                this.particleSystem.canvas = canvas;
                this.particleSystem.ctx = canvas.getContext('2d');
                
                // Set canvas size to match target
                this.particleSystem.resize();
                
                // Listen for resize events
                window.addEventListener('resize', () => this.particleSystem.resize());
                
                this.particleSystem.initialized = true;
                return true;
            },
            
            resize: () => {
                if (!this.particleSystem.canvas || !this.particleSystem.targetElement) return;
                
                const target = this.particleSystem.targetElement;
                const rect = target.getBoundingClientRect();
                
                this.particleSystem.canvas.width = rect.width;
                this.particleSystem.canvas.height = rect.height;
            },
            
            animate: () => {
                if (!this.particleSystem.initialized) return;
                
                const ctx = this.particleSystem.ctx;
                const canvas = this.particleSystem.canvas;
                
                // Clear canvas
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                // Update and draw particles
                for (let i = 0; i < this.particleSystem.particles.length; i++) {
                    const particle = this.particleSystem.particles[i];
                    
                    // Update position
                    particle.x += particle.vx;
                    particle.y += particle.vy;
                    
                    // Update opacity/size based on lifespan
                    particle.life -= particle.decay;
                    
                    if (particle.life <= 0) {
                        // Remove dead particles
                        this.particleSystem.particles.splice(i, 1);
                        i--;
                        continue;
                    }
                    
                    // Draw particle
                    ctx.globalAlpha = particle.life;
                    ctx.fillStyle = particle.color;
                    
                    if (particle.type === 'circle') {
                        ctx.beginPath();
                        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
                        ctx.fill();
                    } else if (particle.type === 'star') {
                        this.drawStar(ctx, particle.x, particle.y, 5, particle.size, particle.size / 2);
                    } else if (particle.type === 'triangle') {
                        this.drawPolygon(ctx, particle.x, particle.y, 3, particle.size);
                    } else if (particle.type === 'square') {
                        ctx.fillRect(
                            particle.x - particle.size / 2,
                            particle.y - particle.size / 2,
                            particle.size,
                            particle.size
                        );
                    }
                }
                
                // Continue animation if particles exist
                if (this.particleSystem.particles.length > 0) {
                    requestAnimationFrame(() => this.particleSystem.animate());
                }
            },
            
            emit: (config) => {
                if (!this.particleSystem.initialized) return;
                
                const defaults = {
                    x: this.particleSystem.canvas.width / 2,
                    y: this.particleSystem.canvas.height / 2,
                    count: 20,
                    speed: 2,
                    size: 5,
                    colors: ['#667eea', '#764ba2', '#f093fb', '#f5576c'],
                    types: ['circle', 'star', 'triangle', 'square'],
                    spread: 360,
                    direction: 0,
                    gravity: 0.05,
                    life: 1,
                    decay: 0.02
                };
                
                const options = { ...defaults, ...config };
                
                // Create particles
                for (let i = 0; i < options.count; i++) {
                    // Calculate angle based on spread and direction
                    const angle = (options.direction - options.spread / 2) + 
                        Math.random() * options.spread;
                    
                    // Calculate velocity based on angle and speed
                    const rad = angle * Math.PI / 180;
                    const speed = options.speed * (0.5 + Math.random() * 0.5);
                    
                    this.particleSystem.particles.push({
                        x: options.x,
                        y: options.y,
                        vx: Math.cos(rad) * speed,
                        vy: Math.sin(rad) * speed,
                        gravity: options.gravity * (0.5 + Math.random()),
                        size: options.size * (0.5 + Math.random()),
                        color: options.colors[Math.floor(Math.random() * options.colors.length)],
                        type: options.types[Math.floor(Math.random() * options.types.length)],
                        life: options.life * (0.8 + Math.random() * 0.4),
                        decay: options.decay * (0.8 + Math.random() * 0.4)
                    });
                }
                
                // Start animation if not already running
                if (this.particleSystem.particles.length > 0 && !this.animationFrame) {
                    this.animationFrame = requestAnimationFrame(() => this.particleSystem.animate());
                }
            },
            
            destroy: () => {
                if (this.particleSystem.canvas && this.particleSystem.targetElement) {
                    this.particleSystem.targetElement.removeChild(this.particleSystem.canvas);
                }
                
                this.particleSystem.particles = [];
                this.particleSystem.initialized = false;
                
                if (this.animationFrame) {
                    cancelAnimationFrame(this.animationFrame);
                    this.animationFrame = null;
                }
            }
        };
    }
    
    // Console methods
    clearConsole() {
        const console = document.getElementById('console');
        if (console) {
            console.innerHTML = '';
            this.addConsoleLine('🧹 Console cleared', 'info');
        }
    }
    
    toggleAutoScroll() {
        this.autoScroll = !this.autoScroll;
        const status = document.getElementById('autoScrollStatus');
        if (status) {
            status.textContent = this.autoScroll ? 'ON' : 'OFF';
        }
        this.addConsoleLine(`📜 Auto-scroll ${this.autoScroll ? 'enabled' : 'disabled'}`, 'info');
    }
    
    // Utility methods
    copyToClipboard(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).catch(err => {
                console.error('Failed to copy text: ', err);
            });
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
            } catch (err) {
                console.error('Failed to copy text: ', err);
            }
            document.body.removeChild(textArea);
        }
    }
    
    // Global functions for HTML onclick handlers
    toggleSettings() {
        const details = document.querySelector('.settings-details');
        if (details) {
            details.toggleAttribute('open');
            const isOpen = details.hasAttribute('open');
            document.getElementById('settingsToggle').setAttribute('aria-expanded', isOpen);
        }
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
