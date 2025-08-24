"""
Apple Sider - Music Downloader Web Interface
============================================

A web-based interface for downloading and managing music using CLI-Music-Downloader.
Features include:
- Web-based music search and download interface
- Integration with CLI-Music-Downloader
- Docker-based deployment
- Cross-platform support (macOS, Linux, WSL)

Usage:
    from apple_sider import AppleSider
    
    app = AppleSider()
    app.run()

Or use the command-line interface:
    apple-sider start
    apple-sider status
    apple-sider stop
"""

__version__ = "1.0.0"
__author__ = "Jordan Lang"
__email__ = "contact@jordolang.com"
__description__ = "Web-based music downloader interface with CLI-Music-Downloader integration"
__url__ = "https://github.com/jordolang/Apple-Sider"

from .core import AppleSider
from .cli import main as cli_main

__all__ = ['AppleSider', 'cli_main']
