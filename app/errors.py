#!/usr/bin/env python3
"""
Error Handling and Recovery for Apple Sider
Provides robust error handling, retry logic, and recovery mechanisms
"""

import logging
import time
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import traceback

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Types of errors that can occur"""
    PARSE_ERROR = "parse_error"
    NETWORK_ERROR = "network_error" 
    DISK_ERROR = "disk_error"
    CLI_ERROR = "cli_error"
    TIMEOUT_ERROR = "timeout_error"
    PERMISSION_ERROR = "permission_error"
    CONFIGURATION_ERROR = "config_error"
    UNKNOWN_ERROR = "unknown_error"

@dataclass
class ErrorRecord:
    """Represents a single error occurrence"""
    error_type: str
    message: str
    timestamp: float
    track_id: Optional[str] = None
    track_name: Optional[str] = None
    retry_count: int = 0
    recoverable: bool = True
    context: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

class ErrorHandler:
    """Comprehensive error handling and recovery system"""
    
    def __init__(self, config=None):
        """Initialize error handler"""
        self.config = config
        self.error_log: List[ErrorRecord] = []
        self.failed_tracks: Dict[str, ErrorRecord] = {}
        self.recovery_strategies = {
            ErrorType.NETWORK_ERROR: self._handle_network_error,
            ErrorType.DISK_ERROR: self._handle_disk_error,
            ErrorType.CLI_ERROR: self._handle_cli_error,
            ErrorType.TIMEOUT_ERROR: self._handle_timeout_error,
            ErrorType.PARSE_ERROR: self._handle_parse_error,
            ErrorType.PERMISSION_ERROR: self._handle_permission_error,
            ErrorType.CONFIGURATION_ERROR: self._handle_config_error,
        }
        
    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> ErrorRecord:
        """Handle an error and determine recovery strategy"""
        error_type = self._classify_error(error)
        
        error_record = ErrorRecord(
            error_type=error_type.value,
            message=str(error),
            timestamp=time.time(),
            track_id=context.get('track_id') if context else None,
            track_name=context.get('track_name') if context else None,
            context=context or {}
        )
        
        # Log the error
        logger.error(f"Error occurred: {error_type.value} - {error}")
        if context:
            logger.error(f"Context: {context}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Store error record
        self.error_log.append(error_record)
        
        # Track failed tracks
        if error_record.track_id:
            self.failed_tracks[error_record.track_id] = error_record
        
        # Attempt recovery
        if error_type in self.recovery_strategies:
            recovery_result = self.recovery_strategies[error_type](error_record)
            error_record.recoverable = recovery_result.get('recoverable', False)
            
        return error_record
    
    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error type based on exception"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # Network-related errors
        if any(keyword in error_str for keyword in ['network', 'connection', 'timeout', 'dns', 'resolve']):
            return ErrorType.NETWORK_ERROR
        if any(keyword in error_type for keyword in ['connectionerror', 'timeout', 'urlerror']):
            return ErrorType.NETWORK_ERROR
            
        # Disk/filesystem errors
        if any(keyword in error_str for keyword in ['disk', 'space', 'filesystem', 'no space left']):
            return ErrorType.DISK_ERROR
        if any(keyword in error_type for keyword in ['oserror', 'ioerror']):
            return ErrorType.DISK_ERROR
            
        # Permission errors
        if any(keyword in error_str for keyword in ['permission', 'access denied', 'forbidden']):
            return ErrorType.PERMISSION_ERROR
        if 'permissionerror' in error_type:
            return ErrorType.PERMISSION_ERROR
            
        # Parse errors
        if any(keyword in error_str for keyword in ['parse', 'xml', 'invalid']):
            return ErrorType.PARSE_ERROR
        if any(keyword in error_type for keyword in ['parseerror', 'xmlsyntaxerror']):
            return ErrorType.PARSE_ERROR
            
        # CLI errors
        if any(keyword in error_str for keyword in ['cli-music-downloader', 'subprocess', 'command']):
            return ErrorType.CLI_ERROR
        if any(keyword in error_type for keyword in ['calledprocesserror', 'subprocess']):
            return ErrorType.CLI_ERROR
            
        # Timeout errors
        if any(keyword in error_str for keyword in ['timeout', 'timed out']):
            return ErrorType.TIMEOUT_ERROR
        if 'timeouterror' in error_type:
            return ErrorType.TIMEOUT_ERROR
            
        return ErrorType.UNKNOWN_ERROR
    
    def _handle_network_error(self, error_record: ErrorRecord) -> Dict[str, Any]:
        """Handle network-related errors"""
        logger.info("Handling network error with exponential backoff")
        
        # Check connectivity
        if not self._check_network_connectivity():
            return {'recoverable': False, 'reason': 'No network connectivity'}
        
        # Implement exponential backoff
        retry_count = error_record.retry_count
        if retry_count < (self.config.get('max_retries', 3) if self.config else 3):
            backoff_time = min(300, 2 ** retry_count * 5)  # Max 5 minute backoff
            logger.info(f"Scheduling retry in {backoff_time} seconds")
            return {
                'recoverable': True,
                'retry_delay': backoff_time,
                'strategy': 'exponential_backoff'
            }
        
        return {'recoverable': False, 'reason': 'Max retries exceeded'}
    
    def _handle_disk_error(self, error_record: ErrorRecord) -> Dict[str, Any]:
        """Handle disk/filesystem errors"""
        logger.info("Handling disk error")
        
        # Check disk space
        download_path = Path(self.config.get('download_location', '~/Music/Apple-Sider')).expanduser()
        
        try:
            # Check available space (requires at least 100MB)
            free_space = shutil.disk_usage(download_path.parent)[2]
            if free_space < 100 * 1024 * 1024:  # 100MB
                logger.error(f"Insufficient disk space: {free_space / 1024 / 1024:.1f}MB available")
                return {'recoverable': False, 'reason': 'Insufficient disk space'}
            
            # Try to create download directory
            download_path.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions
            test_file = download_path / '.test_write'
            test_file.touch()
            test_file.unlink()
            
            return {'recoverable': True, 'strategy': 'disk_check_passed'}
            
        except Exception as e:
            logger.error(f"Disk error recovery failed: {e}")
            return {'recoverable': False, 'reason': str(e)}
    
    def _handle_cli_error(self, error_record: ErrorRecord) -> Dict[str, Any]:
        """Handle CLI-Music-Downloader errors"""
        logger.info("Handling CLI error")
        
        cli_path = Path(self.config.get('cli_music_downloader_path', ''))
        
        # Check if CLI exists and is executable
        if not cli_path.exists():
            return {'recoverable': False, 'reason': 'CLI-Music-Downloader not found'}
        
        if not cli_path.is_file() or not cli_path.stat().st_mode & 0o111:
            return {'recoverable': False, 'reason': 'CLI-Music-Downloader not executable'}
        
        # For CLI errors, often a retry can work
        if error_record.retry_count < 2:
            return {
                'recoverable': True,
                'retry_delay': 10,
                'strategy': 'cli_retry'
            }
        
        return {'recoverable': False, 'reason': 'CLI retry limit exceeded'}
    
    def _handle_timeout_error(self, error_record: ErrorRecord) -> Dict[str, Any]:
        """Handle timeout errors"""
        logger.info("Handling timeout error")
        
        # Timeouts are often recoverable with a retry
        if error_record.retry_count < (self.config.get('max_retries', 3) if self.config else 3):
            return {
                'recoverable': True,
                'retry_delay': 30,
                'strategy': 'timeout_retry'
            }
        
        return {'recoverable': False, 'reason': 'Timeout retry limit exceeded'}
    
    def _handle_parse_error(self, error_record: ErrorRecord) -> Dict[str, Any]:
        """Handle parsing errors"""
        logger.info("Handling parse error")
        
        # Parse errors are usually not recoverable without fixing the source
        return {'recoverable': False, 'reason': 'Parse errors require manual intervention'}
    
    def _handle_permission_error(self, error_record: ErrorRecord) -> Dict[str, Any]:
        """Handle permission errors"""
        logger.info("Handling permission error")
        
        # Try to fix common permission issues
        try:
            download_path = Path(self.config.get('download_location', '~/Music/Apple-Sider')).expanduser()
            download_path.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions
            test_file = download_path / '.test_write'
            test_file.touch()
            test_file.unlink()
            
            return {'recoverable': True, 'strategy': 'permission_fixed'}
            
        except Exception:
            return {'recoverable': False, 'reason': 'Permission cannot be fixed automatically'}
    
    def _handle_config_error(self, error_record: ErrorRecord) -> Dict[str, Any]:
        """Handle configuration errors"""
        logger.info("Handling configuration error")
        
        # Configuration errors usually require manual intervention
        return {'recoverable': False, 'reason': 'Configuration errors require manual fix'}
    
    def _check_network_connectivity(self) -> bool:
        """Check basic network connectivity"""
        import socket
        try:
            # Try to connect to Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except OSError:
            return False
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors"""
        error_counts = {}
        for error in self.error_log:
            error_type = error.error_type
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            'total_errors': len(self.error_log),
            'error_types': error_counts,
            'failed_tracks': len(self.failed_tracks),
            'recoverable_errors': len([e for e in self.error_log if e.recoverable])
        }
    
    def get_failed_tracks_report(self) -> List[Dict[str, Any]]:
        """Get detailed report of failed tracks"""
        return [error.to_dict() for error in self.failed_tracks.values()]
    
    def export_failed_tracks(self, output_path: str) -> bool:
        """Export failed tracks to a file for manual processing"""
        try:
            failed_data = {
                'timestamp': time.time(),
                'total_failed': len(self.failed_tracks),
                'failed_tracks': self.get_failed_tracks_report()
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(failed_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported {len(self.failed_tracks)} failed tracks to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export failed tracks: {e}")
            return False
    
    def clear_error_log(self):
        """Clear all error records"""
        self.error_log.clear()
        self.failed_tracks.clear()
        logger.info("Error log cleared")

# Utility functions for error handling

def safe_execute(func, *args, error_handler: ErrorHandler = None, context: Dict = None, **kwargs):
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs), None
    except Exception as e:
        if error_handler:
            error_record = error_handler.handle_error(e, context)
            return None, error_record
        else:
            logger.error(f"Error in {func.__name__}: {e}")
            return None, e

def with_retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for automatic retry with exponential backoff"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (backoff ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries} attempts failed")
            raise last_exception
        return wrapper
    return decorator

# Example usage and testing
if __name__ == "__main__":
    # Test error handler
    handler = ErrorHandler()
    
    # Simulate various errors
    try:
        raise ConnectionError("Network timeout")
    except Exception as e:
        error_record = handler.handle_error(e, {'track_id': '123', 'track_name': 'Test Song'})
        print(f"Handled error: {error_record.to_dict()}")
    
    # Test retry decorator
    @with_retry(max_retries=3, delay=0.1)
    def flaky_function():
        import random
        if random.random() < 0.7:
            raise ValueError("Random failure")
        return "Success!"
    
    try:
        result = flaky_function()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Final failure: {e}")
    
    # Show error summary
    print(f"Error summary: {handler.get_error_summary()}")
