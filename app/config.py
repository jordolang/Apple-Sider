#!/usr/bin/env python3
"""
Configuration Management for Apple Sider
Handles persistent settings, CLI-Music-Downloader integration, and user preferences
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Config:
    """Configuration manager for Apple Sider settings"""
    
    DEFAULT_CONFIG = {
        # Download settings
        "download_location": "~/Music/Apple-Sider",
        "folder_structure": "flat",  # 'flat' or 'nested'
        "concurrent_downloads": 3,
        "overwrite_existing": False,
        
        # CLI-Music-Downloader settings
        "cli_music_downloader_path": "/Users/jordanlang/Repos/CLI-Music-Downloader/bin/download_music",
        "metadata_source": "all",  # 'musicbrainz', 'all', 'skip-metadata'
        "force_metadata": False,
        "audio_quality": "best",
        
        # Web interface settings
        "log_buffer_size": 1000,
        "auto_start_download": True,
        "show_advanced_settings": False,
        
        # File naming settings
        "filename_format": "{artist}-{title}",  # flat format
        "sanitize_filenames": True,
        "max_filename_length": 255,
        
        # Application settings
        "app_host": "0.0.0.0",
        "app_port": 8080,
        "debug_mode": False,
        
        # Retry and error handling
        "max_retries": 3,
        "retry_delay": 5,  # seconds
        "timeout": 300,  # seconds per download
        
        # Progress tracking
        "save_progress": True,
        "resume_downloads": True
    }
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize configuration manager"""
        self.config_file = Path(config_file).expanduser().resolve()
        self._config = self.DEFAULT_CONFIG.copy()
        self.load_config()
        
    def load_config(self) -> None:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    self._config.update(user_config)
                    logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")
                logger.info("Using default configuration")
        else:
            logger.info("No config file found, using defaults")
            
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            # Create config directory if it doesn't exist
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
                logger.info(f"Configuration saved to {self.config_file}")
                return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
            
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)
        
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self._config[key] = value
        
    def update(self, config_dict: Dict[str, Any]) -> None:
        """Update multiple configuration values"""
        self._config.update(config_dict)
        
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary"""
        return self._config.copy()
        
    def get_download_location(self) -> Path:
        """Get resolved download location path"""
        path_str = self._config["download_location"]
        return Path(path_str).expanduser().resolve()
        
    def ensure_download_directory(self) -> bool:
        """Create download directory if it doesn't exist"""
        try:
            download_path = self.get_download_location()
            download_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Download directory ready: {download_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create download directory: {e}")
            return False
            
    def get_output_filename(self, artist: str, title: str, album: str = "") -> str:
        """Generate output filename based on configuration"""
        format_str = self._config["filename_format"]
        
        # Clean inputs for filename safety
        if self._config["sanitize_filenames"]:
            artist = self._sanitize_filename(artist)
            title = self._sanitize_filename(title)
            album = self._sanitize_filename(album)
            
        # Format filename
        filename = format_str.format(
            artist=artist,
            title=title,
            album=album
        ).strip()
        
        # Ensure .mp3 extension
        if not filename.lower().endswith('.mp3'):
            filename += '.mp3'
            
        # Truncate if too long
        max_len = self._config["max_filename_length"]
        if len(filename) > max_len:
            # Keep extension, truncate the rest
            base = filename[:-4]
            filename = base[:max_len-4] + '.mp3'
            
        return filename
        
    def get_output_path(self, artist: str, title: str, album: str = "") -> Path:
        """Get full output path for a track"""
        base_path = self.get_download_location()
        filename = self.get_output_filename(artist, title, album)
        
        if self._config["folder_structure"] == "nested":
            # Create artist subfolder
            artist_clean = self._sanitize_filename(artist) if self._config["sanitize_filenames"] else artist
            return base_path / artist_clean / filename
        else:
            # Flat structure
            return base_path / filename
            
    def get_cli_download_command(self, query: str) -> list:
        """Build CLI-Music-Downloader command with current settings"""
        cmd = [self._config["cli_music_downloader_path"]]
        
        # Add metadata flags
        if self._config["metadata_source"] == "skip-metadata":
            cmd.append("--skip-metadata")
        elif self._config["metadata_source"] != "all":
            cmd.extend(["--metadata-source", self._config["metadata_source"]])
            
        if self._config["force_metadata"]:
            cmd.append("--force-metadata")
            
        # Add the search query
        cmd.append(query)
        
        return cmd
        
    def _sanitize_filename(self, filename: str) -> str:
        """Remove or replace characters that are problematic in filenames"""
        # Replace problematic characters
        replacements = {
            '/': '-',
            '\\': '-',
            ':': '-',
            '*': '',
            '?': '',
            '"': "'",
            '<': '(',
            '>': ')',
            '|': '-',
            '\n': ' ',
            '\r': ' ',
            '\t': ' '
        }
        
        for old, new in replacements.items():
            filename = filename.replace(old, new)
            
        # Clean up multiple spaces
        filename = ' '.join(filename.split())
        
        # Remove leading/trailing periods and spaces
        filename = filename.strip('. ')
        
        return filename
        
    def validate_settings(self) -> Dict[str, str]:
        """Validate current configuration settings"""
        errors = {}
        
        # Check CLI-Music-Downloader path
        cli_path = Path(self._config["cli_music_downloader_path"]).expanduser()
        if not cli_path.exists():
            errors["cli_music_downloader_path"] = f"CLI-Music-Downloader not found at {cli_path}"
        elif not os.access(cli_path, os.X_OK):
            errors["cli_music_downloader_path"] = f"CLI-Music-Downloader is not executable: {cli_path}"
            
        # Check download location is writable
        try:
            download_path = self.get_download_location()
            download_path.mkdir(parents=True, exist_ok=True)
            test_file = download_path / ".test_write"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            errors["download_location"] = f"Download location is not writable: {e}"
            
        # Validate numeric settings
        if not isinstance(self._config["concurrent_downloads"], int) or self._config["concurrent_downloads"] < 1:
            errors["concurrent_downloads"] = "Concurrent downloads must be a positive integer"
            
        if not isinstance(self._config["app_port"], int) or not (1 <= self._config["app_port"] <= 65535):
            errors["app_port"] = "Port must be an integer between 1 and 65535"
            
        return errors

# Configuration presets for common use cases
PRESETS = {
    "minimal": {
        "folder_structure": "flat",
        "metadata_source": "skip-metadata",
        "force_metadata": False,
        "concurrent_downloads": 1,
        "show_advanced_settings": False
    },
    "balanced": {
        "folder_structure": "nested",
        "metadata_source": "musicbrainz", 
        "force_metadata": False,
        "concurrent_downloads": 3,
        "show_advanced_settings": True
    },
    "high_quality": {
        "folder_structure": "nested",
        "metadata_source": "all",
        "force_metadata": True,
        "concurrent_downloads": 2,  # Slower but more thorough
        "audio_quality": "best",
        "show_advanced_settings": True
    }
}

def load_preset(config: Config, preset_name: str) -> bool:
    """Load a configuration preset"""
    if preset_name not in PRESETS:
        return False
        
    preset = PRESETS[preset_name]
    config.update(preset)
    return True

# Global configuration instance
config = Config()

# Example usage and testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "validate":
            errors = config.validate_settings()
            if errors:
                print("❌ Configuration errors found:")
                for key, error in errors.items():
                    print(f"  {key}: {error}")
            else:
                print("✅ Configuration is valid")
                
        elif sys.argv[1] == "show":
            print("📋 Current configuration:")
            for key, value in config.to_dict().items():
                print(f"  {key}: {value}")
                
        elif sys.argv[1] in PRESETS:
            preset_name = sys.argv[1]
            load_preset(config, preset_name)
            config.save_config()
            print(f"✅ Loaded preset: {preset_name}")
            
    else:
        print("Usage: python config.py [validate|show|minimal|balanced|high_quality]")
