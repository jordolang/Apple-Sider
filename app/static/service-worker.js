/* ============================================================================
   Apple Sider Service Worker - PWA Offline Functionality
   ============================================================================ */

const CACHE_NAME = 'apple-sider-v1.0.0';
const STATIC_CACHE_NAME = 'apple-sider-static-v1.0.0';
const DYNAMIC_CACHE_NAME = 'apple-sider-dynamic-v1.0.0';

// Files to cache for offline functionality
const STATIC_FILES = [
  '/',
  '/style.css',
  '/app.js',
  '/assets/icon.svg',
  '/assets/manifest.json',
  // Add other static assets as needed
];

// Runtime caching strategies
const CACHE_STRATEGIES = {
  'cache-first': ['css', 'js', 'images', 'fonts'],
  'network-first': ['api', 'websocket'],
  'stale-while-revalidate': ['html']
};

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    Promise.all([
      // Cache static files
      caches.open(STATIC_CACHE_NAME).then((cache) => {
        console.log('Service Worker: Caching static files');
        return cache.addAll(STATIC_FILES);
      }),
      
      // Skip waiting to activate immediately
      self.skipWaiting()
    ])
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    Promise.all([
      // Clean up old caches
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE_NAME && 
                cacheName !== DYNAMIC_CACHE_NAME &&
                cacheName !== CACHE_NAME) {
              console.log('Service Worker: Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      }),
      
      // Take control of all clients immediately
      self.clients.claim()
    ])
  );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') {
    return;
  }
  
  // Skip Chrome extension requests
  if (event.request.url.startsWith('chrome-extension://')) {
    return;
  }
  
  // Skip WebSocket connections
  if (event.request.url.includes('/ws')) {
    return;
  }
  
  const url = new URL(event.request.url);
  const isAPIRequest = url.pathname.startsWith('/api/');
  const isAssetRequest = url.pathname.startsWith('/assets/');
  const isStaticFile = STATIC_FILES.includes(url.pathname) || 
                     url.pathname.endsWith('.css') || 
                     url.pathname.endsWith('.js');
  
  if (isAPIRequest) {
    // Network-first strategy for API requests
    event.respondWith(networkFirstStrategy(event.request));
  } else if (isAssetRequest || isStaticFile) {
    // Cache-first strategy for static assets
    event.respondWith(cacheFirstStrategy(event.request));
  } else {
    // Stale-while-revalidate for HTML pages
    event.respondWith(staleWhileRevalidateStrategy(event.request));
  }
});

// Background sync for queued downloads
self.addEventListener('sync', (event) => {
  console.log('Service Worker: Background sync triggered:', event.tag);
  
  if (event.tag === 'background-download') {
    event.waitUntil(handleBackgroundDownload());
  } else if (event.tag === 'queue-sync') {
    event.waitUntil(syncDownloadQueue());
  }
});

// Push notifications for download completion
self.addEventListener('push', (event) => {
  console.log('Service Worker: Push notification received');
  
  let data = {
    title: 'Apple Sider',
    body: 'Download completed!',
    icon: '/assets/icon-192.png',
    badge: '/assets/icon-72.png',
    tag: 'download-complete'
  };
  
  if (event.data) {
    try {
      data = { ...data, ...event.data.json() };
    } catch (e) {
      console.warn('Service Worker: Invalid push data');
    }
  }
  
  const options = {
    body: data.body,
    icon: data.icon,
    badge: data.badge,
    tag: data.tag,
    requireInteraction: true,
    actions: [
      {
        action: 'view',
        title: 'View Downloads',
        icon: '/assets/icon-72.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss'
      }
    ],
    data: {
      url: '/',
      timestamp: Date.now()
    }
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  console.log('Service Worker: Notification clicked:', event.action);
  
  event.notification.close();
  
  if (event.action === 'view') {
    // Open the app
    event.waitUntil(
      clients.openWindow(event.notification.data?.url || '/')
    );
  } else if (event.action === 'dismiss') {
    // Just close the notification
    return;
  } else {
    // Default action - open app
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Message handling for communication with main thread
self.addEventListener('message', (event) => {
  console.log('Service Worker: Message received:', event.data);
  
  if (event.data && event.data.type) {
    switch (event.data.type) {
      case 'SKIP_WAITING':
        self.skipWaiting();
        break;
        
      case 'CACHE_URLS':
        event.waitUntil(
          cacheUrls(event.data.urls)
        );
        break;
        
      case 'CLEAR_CACHE':
        event.waitUntil(
          clearCache(event.data.cacheName)
        );
        break;
        
      case 'GET_CACHE_STATUS':
        event.waitUntil(
          getCacheStatus().then(status => {
            event.ports[0].postMessage(status);
          })
        );
        break;
        
      default:
        console.warn('Service Worker: Unknown message type:', event.data.type);
    }
  }
});

/* ============================================================================
   Caching Strategies
   ============================================================================ */

// Cache-first strategy: Check cache first, fallback to network
async function cacheFirstStrategy(request) {
  try {
    // Try to get from cache first
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    
    // If not in cache, fetch from network and cache
    const response = await fetch(request);
    if (response.status === 200) {
      const cache = await caches.open(STATIC_CACHE_NAME);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.error('Service Worker: Cache-first strategy failed:', error);
    
    // Return offline fallback if available
    return getOfflineFallback(request);
  }
}

// Network-first strategy: Try network first, fallback to cache
async function networkFirstStrategy(request) {
  try {
    // Try network first
    const response = await fetch(request);
    
    // Cache successful responses
    if (response.status === 200) {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.log('Service Worker: Network failed, checking cache:', error.message);
    
    // Fallback to cache
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    
    // Return offline response for API calls
    if (request.url.includes('/api/')) {
      return new Response(JSON.stringify({
        error: 'Network unavailable',
        offline: true,
        timestamp: Date.now()
      }), {
        status: 503,
        statusText: 'Service Unavailable',
        headers: {
          'Content-Type': 'application/json'
        }
      });
    }
    
    throw error;
  }
}

// Stale-while-revalidate: Return cached version, update cache in background
async function staleWhileRevalidateStrategy(request) {
  const cache = await caches.open(DYNAMIC_CACHE_NAME);
  const cached = await cache.match(request);
  
  // Fetch fresh version in background
  const fetchPromise = fetch(request).then(response => {
    if (response.status === 200) {
      cache.put(request, response.clone());
    }
    return response;
  }).catch(error => {
    console.log('Service Worker: Background fetch failed:', error.message);
    return cached; // Return cached version if network fails
  });
  
  // Return cached version immediately if available
  return cached || fetchPromise;
}

/* ============================================================================
   Helper Functions
   ============================================================================ */

// Get offline fallback for different resource types
async function getOfflineFallback(request) {
  const url = new URL(request.url);
  
  if (url.pathname.endsWith('.html') || request.headers.get('accept')?.includes('text/html')) {
    // Return cached main page for HTML requests
    return caches.match('/') || new Response('Offline', { status: 503 });
  }
  
  if (url.pathname.endsWith('.css')) {
    return new Response('/* Offline */', {
      headers: { 'Content-Type': 'text/css' }
    });
  }
  
  if (url.pathname.endsWith('.js')) {
    return new Response('console.log("Offline");', {
      headers: { 'Content-Type': 'application/javascript' }
    });
  }
  
  return new Response('Offline', { status: 503 });
}

// Cache multiple URLs
async function cacheUrls(urls) {
  const cache = await caches.open(DYNAMIC_CACHE_NAME);
  
  const cachePromises = urls.map(async (url) => {
    try {
      const response = await fetch(url);
      if (response.status === 200) {
        return cache.put(url, response);
      }
    } catch (error) {
      console.warn('Service Worker: Failed to cache URL:', url, error.message);
    }
  });
  
  await Promise.allSettled(cachePromises);
}

// Clear specific cache
async function clearCache(cacheName) {
  if (cacheName) {
    await caches.delete(cacheName);
  } else {
    // Clear all dynamic caches
    const cacheNames = await caches.keys();
    const deletePromises = cacheNames
      .filter(name => name.includes('dynamic'))
      .map(name => caches.delete(name));
    
    await Promise.all(deletePromises);
  }
}

// Get cache status information
async function getCacheStatus() {
  const cacheNames = await caches.keys();
  const status = {};
  
  for (const cacheName of cacheNames) {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();
    status[cacheName] = keys.length;
  }
  
  return status;
}

// Handle background download synchronization
async function handleBackgroundDownload() {
  try {
    // Get queued downloads from IndexedDB or localStorage
    const queuedDownloads = await getQueuedDownloads();
    
    if (queuedDownloads.length === 0) {
      return;
    }
    
    console.log('Service Worker: Processing', queuedDownloads.length, 'background downloads');
    
    // Process downloads in background
    for (const download of queuedDownloads) {
      try {
        await processBackgroundDownload(download);
      } catch (error) {
        console.error('Service Worker: Background download failed:', error);
        // Mark download as failed
        await markDownloadFailed(download.id, error.message);
      }
    }
    
    // Notify user of completion
    if (Notification.permission === 'granted') {
      await self.registration.showNotification('Apple Sider', {
        body: `Background downloads completed: ${queuedDownloads.length} files`,
        icon: '/assets/icon-192.png',
        tag: 'background-complete'
      });
    }
    
  } catch (error) {
    console.error('Service Worker: Background download handler failed:', error);
  }
}

// Sync download queue with server
async function syncDownloadQueue() {
  try {
    // Attempt to sync local queue with server
    const response = await fetch('/api/sync-queue', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        timestamp: Date.now()
      })
    });
    
    if (response.ok) {
      console.log('Service Worker: Queue sync successful');
    } else {
      console.warn('Service Worker: Queue sync failed:', response.status);
    }
  } catch (error) {
    console.error('Service Worker: Queue sync error:', error);
  }
}

// Get queued downloads (placeholder - would integrate with your storage system)
async function getQueuedDownloads() {
  // This would typically read from IndexedDB or localStorage
  // For now, return empty array
  return [];
}

// Process individual background download
async function processBackgroundDownload(download) {
  // This would implement the actual download logic
  console.log('Service Worker: Processing background download:', download);
}

// Mark download as failed
async function markDownloadFailed(downloadId, error) {
  // This would update the download status in storage
  console.log('Service Worker: Marking download failed:', downloadId, error);
}

console.log('Service Worker: Script loaded successfully');
