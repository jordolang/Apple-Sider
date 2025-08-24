#!/usr/bin/env python3
"""
Download Queue Manager for Apple Sider
Handles concurrent downloads, progress tracking, and CLI-Music-Downloader integration
"""

import queue
import subprocess
import threading
import time
import logging
import os
from typing import Dict, List, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import hashlib

try:
    from .config import config
except ImportError:
    # For standalone testing
    import sys
    sys.path.append(os.path.dirname(__file__))
    from config import config

logger = logging.getLogger(__name__)

class DownloadStatus(Enum):
    """Download status enumeration"""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"

@dataclass
class DownloadTask:
    """Represents a single download task"""
    id: str
    query: str
    artist: str
    title: str
    album: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: float = 0.0
    error_message: str = ""
    retry_count: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    output_path: Optional[Path] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get download duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
        
    @property
    def display_name(self) -> str:
        """Get display name for UI"""
        return f"{self.artist} - {self.title}"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'query': self.query,
            'artist': self.artist,
            'title': self.title,
            'album': self.album,
            'metadata': self.metadata,
            'status': self.status.value,
            'progress': self.progress,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'output_path': str(self.output_path) if self.output_path else None,
            'duration': self.duration,
            'display_name': self.display_name
        }

class DownloadQueue:
    """Manages download queue with concurrent processing"""
    
    def __init__(self, max_workers: int = None, log_callback: Callable[[str, str], None] = None):
        """Initialize download queue manager"""
        self.max_workers = max_workers or config.get('concurrent_downloads', 3)
        self.log_callback = log_callback
        
        # Queue and tracking
        self._queue = queue.Queue()
        self._tasks: Dict[str, DownloadTask] = {}
        self._active_downloads: Dict[str, Future] = {}
        self._completed_tasks: List[str] = []
        self._failed_tasks: List[str] = []
        
        # Thread pool
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self._shutdown_event = threading.Event()
        self._worker_thread = None
        
        # Progress tracking
        self.total_tasks = 0
        self.completed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
        # Deduplication
        self._track_hashes: Dict[str, str] = {}  # hash -> task_id
        
        logger.info(f"Initialized download queue with {self.max_workers} workers")
        
    def start(self):
        """Start the download queue worker"""
        if self._worker_thread and self._worker_thread.is_alive():
            logger.warning("Download queue already running")
            return
            
        self._shutdown_event.clear()
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        logger.info("Download queue started")
        
    def stop(self):
        """Stop the download queue worker"""
        self._shutdown_event.set()
        
        # Cancel active downloads
        for task_id, future in list(self._active_downloads.items()):
            future.cancel()
            
        # Wait for worker thread to finish
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5)
            
        logger.info("Download queue stopped")
        
    def add_task(self, query: str, artist: str, title: str, album: str = "", metadata: Dict = None) -> Optional[str]:
        """Add a download task to the queue"""
        # Create task ID
        task_id = self._generate_task_id(artist, title)
        
        # Check for duplicates
        track_hash = self._get_track_hash(artist, title)
        if track_hash in self._track_hashes:
            existing_task_id = self._track_hashes[track_hash]
            logger.info(f"Duplicate track skipped: {artist} - {title} (existing: {existing_task_id})")
            return None
            
        # Create task
        task = DownloadTask(
            id=task_id,
            query=query,
            artist=artist,
            title=title,
            album=album,
            metadata=metadata or {}
        )
        
        # Store task and hash
        self._tasks[task_id] = task
        self._track_hashes[track_hash] = task_id
        
        # Add to queue
        self._queue.put(task_id)
        self.total_tasks += 1
        
        logger.info(f"Added task {task_id}: {task.display_name}")
        self._log(f"📋 Queued: {task.display_name}", "info")
        
        return task_id
        
    def add_tasks_from_manifest(self, manifest: List[Dict]) -> List[str]:
        """Add multiple tasks from a download manifest"""
        added_task_ids = []
        
        for item in manifest:
            task_id = self.add_task(
                query=item.get('query', ''),
                artist=item.get('artist', ''),
                title=item.get('name', ''),
                album=item.get('album', ''),
                metadata=item.get('metadata', {})
            )
            if task_id:
                added_task_ids.append(task_id)
                
        logger.info(f"Added {len(added_task_ids)} tasks from manifest")
        return added_task_ids
        
    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """Get a specific task by ID"""
        return self._tasks.get(task_id)
        
    def get_all_tasks(self) -> List[DownloadTask]:
        """Get all tasks"""
        return list(self._tasks.values())
        
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        active_count = len(self._active_downloads)
        queued_count = self._queue.qsize()
        
        return {
            'total_tasks': self.total_tasks,
            'queued': queued_count,
            'active': active_count,
            'completed': self.completed_count,
            'failed': self.failed_count,
            'skipped': self.skipped_count,
            'progress_percent': round((self.completed_count / self.total_tasks * 100) if self.total_tasks > 0 else 0, 1),
            'active_tasks': [self._tasks[task_id].to_dict() for task_id in self._active_downloads.keys()],
            'max_workers': self.max_workers
        }
        
    def retry_failed_tasks(self) -> int:
        """Retry all failed tasks"""
        retried_count = 0
        
        for task_id in list(self._failed_tasks):
            task = self._tasks.get(task_id)
            if task and task.retry_count < config.get('max_retries', 3):
                task.status = DownloadStatus.QUEUED
                task.error_message = ""
                task.progress = 0.0
                self._queue.put(task_id)
                self._failed_tasks.remove(task_id)
                retried_count += 1
                
        if retried_count > 0:
            logger.info(f"Retrying {retried_count} failed tasks")
            self._log(f"🔄 Retrying {retried_count} failed downloads", "info")
            
        return retried_count
        
    def clear_queue(self):
        """Clear all tasks from queue"""
        # Clear the queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
                
        # Cancel active downloads
        for task_id, future in list(self._active_downloads.items()):
            future.cancel()
            
        # Reset tracking
        self._tasks.clear()
        self._active_downloads.clear()
        self._completed_tasks.clear()
        self._failed_tasks.clear()
        self._track_hashes.clear()
        
        self.total_tasks = 0
        self.completed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
        logger.info("Download queue cleared")
        self._log("🗑️ Queue cleared", "info")
        
    def _worker_loop(self):
        """Main worker loop that processes the download queue"""
        logger.info("Download queue worker started")
        
        while not self._shutdown_event.is_set():
            try:
                # Get next task (with timeout to allow shutdown check)
                task_id = self._queue.get(timeout=1.0)
                
                # Submit download task
                future = self._executor.submit(self._download_task, task_id)
                self._active_downloads[task_id] = future
                
                # Add completion callback
                future.add_done_callback(lambda f, tid=task_id: self._task_completed(tid, f))
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                
        logger.info("Download queue worker stopped")
        
    def _download_task(self, task_id: str) -> bool:
        """Download a single task"""
        task = self._tasks.get(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return False
            
        task.status = DownloadStatus.DOWNLOADING
        task.start_time = time.time()
        task.progress = 0.0
        
        logger.info(f"Starting download: {task.display_name}")
        self._log(f"🎵 Downloading: {task.display_name}", "info")
        
        try:
            # Build command
            cmd = config.get_cli_download_command(task.query)
            
            # Set output directory
            output_path = config.get_output_path(task.artist, task.title, task.album)
            task.output_path = output_path
            
            # Ensure output directory exists
            if config.get('folder_structure') == 'nested':
                output_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                config.ensure_download_directory()
            
            # Check if file already exists and skip if configured
            if output_path.exists() and not config.get('overwrite_existing', False):
                logger.info(f"File already exists, skipping: {output_path}")
                task.status = DownloadStatus.SKIPPED
                task.progress = 100.0
                self._log(f"⏭️ Skipped (exists): {task.display_name}", "warning")
                return True
            
            # Execute download command
            env = dict(os.environ) if 'os' in globals() else {}
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env,
                cwd=config.get_download_location()
            )
            
            # Stream output
            for line in iter(process.stdout.readline, ''):
                if self._shutdown_event.is_set():
                    process.terminate()
                    break
                    
                line = line.strip()
                if line:
                    self._log(f"  {line}", "output")
                    
                    # Update progress based on CLI output
                    if "%" in line or "downloading" in line.lower():
                        task.progress = min(task.progress + 10, 90)
            
            # Wait for completion
            return_code = process.wait(timeout=config.get('timeout', 300))
            
            if return_code == 0:
                task.status = DownloadStatus.COMPLETED
                task.progress = 100.0
                task.end_time = time.time()
                logger.info(f"Download completed: {task.display_name}")
                self._log(f"✅ Completed: {task.display_name}", "success")
                return True
            else:
                raise subprocess.CalledProcessError(return_code, cmd)
                
        except subprocess.TimeoutExpired:
            task.error_message = f"Download timeout ({config.get('timeout')}s)"
            logger.error(f"Download timeout: {task.display_name}")
            self._log(f"⏰ Timeout: {task.display_name}", "error")
            
        except subprocess.CalledProcessError as e:
            task.error_message = f"CLI-Music-Downloader failed (exit code: {e.returncode})"
            logger.error(f"Download failed: {task.display_name} - {task.error_message}")
            self._log(f"❌ Failed: {task.display_name} - {task.error_message}", "error")
            
        except Exception as e:
            task.error_message = str(e)
            logger.error(f"Download error: {task.display_name} - {e}")
            self._log(f"💥 Error: {task.display_name} - {e}", "error")
            
        # Handle failure
        task.status = DownloadStatus.FAILED
        task.end_time = time.time()
        task.retry_count += 1
        
        # Schedule retry if within limits
        if task.retry_count < config.get('max_retries', 3):
            retry_delay = config.get('retry_delay', 5) * task.retry_count
            threading.Timer(retry_delay, lambda: self._queue.put(task_id)).start()
            task.status = DownloadStatus.RETRYING
            self._log(f"🔄 Retrying in {retry_delay}s: {task.display_name}", "warning")
            
        return False
        
    def _task_completed(self, task_id: str, future: Future):
        """Handle task completion"""
        # Remove from active downloads
        self._active_downloads.pop(task_id, None)
        
        task = self._tasks.get(task_id)
        if not task:
            return
            
        # Update counters
        if task.status == DownloadStatus.COMPLETED:
            self.completed_count += 1
            self._completed_tasks.append(task_id)
        elif task.status == DownloadStatus.SKIPPED:
            self.skipped_count += 1
        elif task.status == DownloadStatus.FAILED and task.retry_count >= config.get('max_retries', 3):
            self.failed_count += 1
            self._failed_tasks.append(task_id)
            
    def _generate_task_id(self, artist: str, title: str) -> str:
        """Generate unique task ID"""
        content = f"{artist}_{title}_{time.time()}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
        
    def _get_track_hash(self, artist: str, title: str) -> str:
        """Generate hash for track deduplication"""
        # Normalize for comparison
        normalized = f"{artist.lower().strip()}_{title.lower().strip()}"
        return hashlib.md5(normalized.encode()).hexdigest()
        
    def _log(self, message: str, level: str = "info"):
        """Log message to callback if available"""
        if self.log_callback:
            self.log_callback(message, level)

# Example usage and testing
if __name__ == "__main__":
    import sys
    import os
    
    # Add parent directory to path for imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    def log_callback(message: str, level: str):
        print(f"[{level.upper()}] {message}")
    
    # Test queue
    queue_manager = DownloadQueue(max_workers=2, log_callback=log_callback)
    
    # Add some test tasks
    queue_manager.add_task("The Beatles Hey Jude", "The Beatles", "Hey Jude", "1 (Remastered)")
    queue_manager.add_task("Queen Bohemian Rhapsody", "Queen", "Bohemian Rhapsody", "A Night at the Opera")
    
    # Start processing
    queue_manager.start()
    
    try:
        # Monitor progress
        while True:
            status = queue_manager.get_queue_status()
            print(f"Progress: {status['progress_percent']}% ({status['completed']}/{status['total_tasks']})")
            
            if status['queued'] == 0 and status['active'] == 0:
                break
                
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        queue_manager.stop()
