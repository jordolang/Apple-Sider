"""
Apple Sider Core Module
=======================

Core functionality for Apple Sider music downloader interface.
"""

import os
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Optional, Any


class AppleSider:
    """Main Apple Sider application class."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize Apple Sider instance.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path or self._find_config()
        self.config = self._load_config()
        self.project_dir = self._setup_project_directory()
        
    def _find_config(self) -> str:
        """Find configuration file in standard locations."""
        config_locations = [
            "config/config.json",
            "config.json",
            os.path.expanduser("~/.apple-sider/config.json"),
            os.path.expanduser("~/.config/apple-sider/config.json"),
        ]
        
        for config_path in config_locations:
            if os.path.exists(config_path):
                return config_path
        
        # Return default location
        return "config/config.json"
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        default_config = {
            "app": {
                "name": "Apple Sider",
                "version": "1.0.0",
                "port": 8080,
                "host": "0.0.0.0"
            },
            "downloads": {
                "quality": "high",
                "format": "mp3",
                "organize_by_artist": True,
                "download_path": os.path.expanduser("~/Music/Apple-Sider")
            },
            "cli_music_downloader": {
                "enabled": True,
                "path": "/usr/local/bin/download_music",
                "github_url": "https://github.com/jordolang/CLI-Music-Downloader"
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                return self._merge_configs(default_config, config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load config from {self.config_path}: {e}")
        
        return default_config
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Recursively merge user config with defaults."""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _setup_project_directory(self) -> Path:
        """Set up project directory structure."""
        # Try to find existing project directory
        potential_dirs = [
            Path.cwd(),
            Path.home() / ".apple-sider",
            Path("/opt/apple-sider") if os.name != 'nt' else Path.home() / "apple-sider"
        ]
        
        for dir_path in potential_dirs:
            if (dir_path / "docker-compose.yml").exists() or (dir_path / "Dockerfile").exists():
                return dir_path
        
        # Create new project directory
        project_dir = Path.home() / ".apple-sider"
        project_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        for subdir in ["config", "logs", "data", "downloads"]:
            (project_dir / subdir).mkdir(exist_ok=True)
        
        return project_dir
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        config_dir = Path(self.config_path).parent
        config_dir.mkdir(exist_ok=True, parents=True)
        
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def install_project_files(self) -> None:
        """Install/update project files (Docker, configs, etc.) to project directory."""
        try:
            # Download or copy essential files
            essential_files = [
                "Dockerfile",
                "docker-compose.yml",
                "start.sh",
                "requirements.txt"
            ]
            
            # If we're in the source directory, copy files
            current_dir = Path.cwd()
            if all((current_dir / f).exists() for f in essential_files):
                print("📦 Installing project files from source directory...")
                for file in essential_files:
                    shutil.copy2(current_dir / file, self.project_dir / file)
                
                # Copy app directory if it exists
                if (current_dir / "app").exists():
                    if (self.project_dir / "app").exists():
                        shutil.rmtree(self.project_dir / "app")
                    shutil.copytree(current_dir / "app", self.project_dir / "app")
            else:
                print("🌐 Downloading project files from GitHub...")
                self._download_project_files()
            
            # Make start.sh executable
            start_script = self.project_dir / "start.sh"
            if start_script.exists():
                start_script.chmod(0o755)
            
            print(f"✅ Project files installed to: {self.project_dir}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to install project files: {e}")
    
    def _download_project_files(self) -> None:
        """Download project files from GitHub repository."""
        import urllib.request
        import zipfile
        
        repo_url = "https://github.com/jordolang/Apple-Sider/archive/refs/heads/main.zip"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / "apple-sider.zip"
            
            # Download repository
            urllib.request.urlretrieve(repo_url, zip_path)
            
            # Extract files
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_path)
            
            # Find extracted directory
            extracted_dir = temp_path / "Apple-Sider-main"
            if not extracted_dir.exists():
                # Try alternative name
                extracted_dirs = [d for d in temp_path.iterdir() if d.is_dir() and "Apple-Sider" in d.name]
                if extracted_dirs:
                    extracted_dir = extracted_dirs[0]
                else:
                    raise RuntimeError("Could not find extracted repository directory")
            
            # Copy essential files
            essential_files = ["Dockerfile", "docker-compose.yml", "start.sh", "requirements.txt"]
            for file in essential_files:
                src = extracted_dir / file
                if src.exists():
                    shutil.copy2(src, self.project_dir / file)
            
            # Copy app directory
            app_dir = extracted_dir / "app"
            if app_dir.exists():
                if (self.project_dir / "app").exists():
                    shutil.rmtree(self.project_dir / "app")
                shutil.copytree(app_dir, self.project_dir / "app")
    
    def run_command(self, command: str, *args: str) -> subprocess.CompletedProcess:
        """Run a start.sh command."""
        start_script = self.project_dir / "start.sh"
        if not start_script.exists():
            raise RuntimeError("start.sh not found. Run install() first.")
        
        # Change to project directory for execution
        cmd = [str(start_script), command] + list(args)
        return subprocess.run(cmd, cwd=self.project_dir, check=True)
    
    def start(self, **kwargs) -> None:
        """Start Apple Sider services."""
        print("🍎 Starting Apple Sider...")
        try:
            os.chdir(self.project_dir)
            self.run_command("up")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to start Apple Sider: {e}")
    
    def stop(self) -> None:
        """Stop Apple Sider services."""
        print("🛑 Stopping Apple Sider...")
        try:
            self.run_command("stop")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to stop Apple Sider: {e}")
    
    def restart(self) -> None:
        """Restart Apple Sider services."""
        print("🔄 Restarting Apple Sider...")
        try:
            self.run_command("restart")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to restart Apple Sider: {e}")
    
    def status(self) -> None:
        """Show Apple Sider status."""
        try:
            self.run_command("status")
        except subprocess.CalledProcessError as e:
            print(f"Could not get status: {e}")
    
    def logs(self) -> None:
        """Show Apple Sider logs."""
        try:
            self.run_command("logs")
        except subprocess.CalledProcessError as e:
            print(f"Could not get logs: {e}")
    
    def update(self) -> None:
        """Update Apple Sider to latest version."""
        print("🔄 Updating Apple Sider...")
        try:
            self.run_command("update")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to update Apple Sider: {e}")
    
    def install(self) -> None:
        """Install Apple Sider (download files and set up)."""
        print("🚀 Installing Apple Sider...")
        self.install_project_files()
        
        # Set up configuration
        if not os.path.exists(self.config_path):
            self.save_config()
            print(f"✅ Configuration saved to: {self.config_path}")
        
        print("🎉 Apple Sider installation completed!")
        print(f"📍 Project directory: {self.project_dir}")
        print("🚀 Run 'apple-sider start' to begin!")
    
    def run(self, host: Optional[str] = None, port: Optional[int] = None, debug: bool = False) -> None:
        """Run Apple Sider in development mode (without Docker)."""
        # This would be used for development/testing
        # For production, users should use start() which uses Docker
        print("🧪 Development mode not implemented yet.")
        print("🐳 Please use 'apple-sider start' for Docker-based deployment.")
        print("🔧 Or run './start.sh up' in your project directory.")
