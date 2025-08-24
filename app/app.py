#!/usr/bin/env python3
"""
Apple Sider - Flask Backend Application
A simple self-hosted web application for downloading Apple Music libraries
"""

import os
import tempfile
import logging
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import json
from pathlib import Path

# Import our modules
try:
    from .parser import LibraryParser
    from .config import config
    from .downloader import DownloadQueue
except ImportError:
    # For standalone running
    import sys
    sys.path.append(os.path.dirname(__file__))
    from parser import LibraryParser
    from config import config
    from downloader import DownloadQueue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__, 
            static_folder='static', 
            template_folder='templates')
app.config['SECRET_KEY'] = 'apple-sider-secret-key'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# SocketIO for WebSocket support
socketio = SocketIO(app, cors_allowed_origins="*")

# Global instances
download_queue = None
current_parser = None

def log_to_websocket(message: str, level: str = "info"):
    """Send log message to WebSocket clients"""
    try:
        socketio.emit('log_message', {
            'message': message,
            'level': level,
            'timestamp': time.time()
        }, namespace='/')
    except Exception as e:
        logger.error(f"Failed to send WebSocket message: {e}")

def initialize_download_queue():
    """Initialize the global download queue"""
    global download_queue
    if download_queue is None:
        download_queue = DownloadQueue(
            max_workers=config.get('concurrent_downloads', 3),
            log_callback=log_to_websocket
        )
        download_queue.start()
        logger.info("Download queue initialized")

# Routes

@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/upload', methods=['POST'])
def upload_library():
    """Handle Library.xml file upload"""
    global current_parser
    
    try:
        if 'library' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
            
        file = request.files['library']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
            
        if not file.filename.lower().endswith('.xml'):
            return jsonify({
                'success': False,
                'error': 'Please upload an XML file'
            }), 400
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xml', delete=False) as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Parse the library
            parser = LibraryParser()
            result = parser.parse_library(temp_path)
            
            if result['success']:
                current_parser = parser
                logger.info(f"Successfully parsed library: {result['valid_tracks']} valid tracks")
                
                # Add manifest to result
                result['manifest'] = parser.generate_download_manifest()
                
                return jsonify(result)
            else:
                logger.error(f"Failed to parse library: {result['error']}")
                return jsonify(result), 400
                
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except OSError:
                pass
                
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/start-download', methods=['POST'])
def start_download():
    """Start the download process"""
    global current_parser, download_queue
    
    try:
        if current_parser is None:
            return jsonify({
                'success': False,
                'error': 'No library loaded. Please upload a Library.xml file first.'
            }), 400
        
        # Initialize download queue if needed
        initialize_download_queue()
        
        # Clear any existing queue
        download_queue.clear_queue()
        
        # Generate manifest and add tasks
        manifest = current_parser.generate_download_manifest()
        added_tasks = download_queue.add_tasks_from_manifest(manifest)
        
        logger.info(f"Started download process with {len(added_tasks)} tracks")
        
        return jsonify({
            'success': True,
            'queued_count': len(added_tasks),
            'total_tracks': len(manifest)
        })
        
    except Exception as e:
        logger.error(f"Error starting download: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/status')
def get_status():
    """Get current download status"""
    global download_queue
    
    try:
        if download_queue is None:
            return jsonify({
                'total_tasks': 0,
                'queued': 0,
                'active': 0,
                'completed': 0,
                'failed': 0,
                'skipped': 0,
                'progress_percent': 0,
                'active_tasks': [],
                'max_workers': config.get('concurrent_downloads', 3)
            })
        
        status = download_queue.get_queue_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/pause-download', methods=['POST'])
def pause_download():
    """Pause/resume downloads"""
    global download_queue
    
    try:
        if download_queue is None:
            return jsonify({
                'success': False,
                'error': 'No download queue active'
            }), 400
        
        # For now, we'll implement this by stopping the queue
        # In a more sophisticated implementation, we might pause individual downloads
        download_queue.stop()
        
        return jsonify({
            'success': True,
            'message': 'Downloads paused'
        })
        
    except Exception as e:
        logger.error(f"Error pausing download: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/retry-failed', methods=['POST'])
def retry_failed():
    """Retry failed downloads"""
    global download_queue
    
    try:
        if download_queue is None:
            return jsonify({
                'success': False,
                'error': 'No download queue active'
            }), 400
        
        retried_count = download_queue.retry_failed_tasks()
        
        return jsonify({
            'success': True,
            'retried_count': retried_count
        })
        
    except Exception as e:
        logger.error(f"Error retrying failed downloads: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/clear-queue', methods=['POST'])
def clear_queue():
    """Clear the download queue"""
    global download_queue, current_parser
    
    try:
        if download_queue is not None:
            download_queue.clear_queue()
        
        current_parser = None
        
        return jsonify({
            'success': True,
            'message': 'Queue cleared'
        })
        
    except Exception as e:
        logger.error(f"Error clearing queue: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/settings', methods=['GET', 'POST'])
def handle_settings():
    """Get or update settings"""
    if request.method == 'GET':
        return jsonify(config.to_dict())
    
    elif request.method == 'POST':
        try:
            settings_data = request.get_json()
            
            if not settings_data:
                return jsonify({
                    'success': False,
                    'error': 'No settings data provided'
                }), 400
            
            # Update configuration
            config.update(settings_data)
            
            # Save to file
            if config.save_config():
                # Restart download queue with new settings if needed
                global download_queue
                if download_queue is not None and settings_data.get('concurrent_downloads'):
                    download_queue.max_workers = settings_data['concurrent_downloads']
                
                return jsonify({
                    'success': True,
                    'message': 'Settings saved'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to save settings'
                }), 500
                
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

# WebSocket events

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    logger.info(f"WebSocket client connected")
    emit('log_message', {
        'message': 'Connected to Apple Sider',
        'level': 'info',
        'timestamp': time.time()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    logger.info(f"WebSocket client disconnected")

# Error handlers

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def file_too_large(error):
    """Handle file too large errors"""
    return jsonify({'error': 'File too large (max 100MB)'}), 413

# Application factory

def create_app():
    """Create and configure the Flask app"""
    # Validate configuration
    errors = config.validate_settings()
    if errors:
        logger.warning("Configuration issues found:")
        for key, error in errors.items():
            logger.warning(f"  {key}: {error}")
    
    # Ensure download directory exists
    config.ensure_download_directory()
    
    logger.info(f"Apple Sider starting on {config.get('app_host')}:{config.get('app_port')}")
    
    return app

# Main entry point
if __name__ == '__main__':
    import time
    
    app = create_app()
    
    # Run the application
    try:
        socketio.run(
            app,
            host=config.get('app_host', '0.0.0.0'),
            port=config.get('app_port', 8080),
            debug=config.get('debug_mode', False),
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        logger.info("Shutting down Apple Sider...")
        if download_queue:
            download_queue.stop()
    except Exception as e:
        logger.error(f"Failed to start Apple Sider: {e}")
        exit(1)
