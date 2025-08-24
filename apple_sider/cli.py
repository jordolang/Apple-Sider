"""
Apple Sider Command Line Interface
==================================

CLI for managing Apple Sider music downloader interface.
"""

import sys
import argparse
from typing import List, Optional

from .core import AppleSider


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="apple-sider",
        description="Apple Sider - Web-based music downloader interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    apple-sider install          # Install Apple Sider
    apple-sider start            # Start services
    apple-sider status           # Check status
    apple-sider logs             # View logs
    apple-sider stop             # Stop services
    apple-sider update           # Update to latest version

For more information, visit: https://github.com/jordolang/Apple-Sider
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="Apple Sider 1.0.0"
    )
    
    parser.add_argument(
        "--config",
        help="Path to configuration file",
        metavar="PATH"
    )
    
    parser.add_argument(
        "--project-dir",
        help="Project directory path",
        metavar="PATH"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        metavar="COMMAND"
    )
    
    # Install command
    install_parser = subparsers.add_parser(
        "install",
        help="Install Apple Sider (download files and set up)"
    )
    install_parser.add_argument(
        "--force",
        action="store_true",
        help="Force reinstallation even if already installed"
    )
    
    # Start command
    start_parser = subparsers.add_parser(
        "start",
        help="Start Apple Sider services"
    )
    start_parser.add_argument(
        "--build",
        action="store_true",
        help="Build containers before starting"
    )
    
    # Stop command
    subparsers.add_parser(
        "stop",
        help="Stop Apple Sider services"
    )
    
    # Restart command
    subparsers.add_parser(
        "restart",
        help="Restart Apple Sider services"
    )
    
    # Status command
    subparsers.add_parser(
        "status",
        help="Show Apple Sider status"
    )
    
    # Logs command
    logs_parser = subparsers.add_parser(
        "logs",
        help="Show Apple Sider logs"
    )
    logs_parser.add_argument(
        "--follow",
        action="store_true",
        help="Follow logs in real-time"
    )
    
    # Update command
    subparsers.add_parser(
        "update",
        help="Update Apple Sider to latest version"
    )
    
    # Config command
    config_parser = subparsers.add_parser(
        "config",
        help="Manage configuration"
    )
    config_subparsers = config_parser.add_subparsers(
        dest="config_action",
        help="Configuration actions"
    )
    config_subparsers.add_parser("show", help="Show current configuration")
    config_subparsers.add_parser("edit", help="Edit configuration file")
    config_subparsers.add_parser("reset", help="Reset to default configuration")
    
    return parser


def handle_install(app: AppleSider, args: argparse.Namespace) -> int:
    """Handle install command."""
    try:
        if args.force or not app.project_dir.exists():
            app.install()
            print("\n🎉 Installation completed successfully!")
            print("\nNext steps:")
            print("  apple-sider start    # Start Apple Sider")
            print("  apple-sider status   # Check if running")
        else:
            print("✅ Apple Sider is already installed")
            print(f"📍 Project directory: {app.project_dir}")
            print("\nUse --force to reinstall")
        return 0
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return 1


def handle_config(app: AppleSider, args: argparse.Namespace) -> int:
    """Handle config command."""
    if args.config_action == "show":
        import json
        print("📝 Current configuration:")
        print(json.dumps(app.config, indent=2))
        print(f"\n📁 Config file: {app.config_path}")
        return 0
    
    elif args.config_action == "edit":
        import subprocess
        import shutil
        
        # Find an editor
        editors = ["nano", "vim", "vi", "code", "gedit"]
        editor = None
        for ed in editors:
            if shutil.which(ed):
                editor = ed
                break
        
        if not editor:
            print("❌ No text editor found")
            print("Please edit the config file manually:")
            print(f"  {app.config_path}")
            return 1
        
        try:
            subprocess.run([editor, app.config_path], check=True)
            print("✅ Configuration updated")
            return 0
        except subprocess.CalledProcessError:
            print("❌ Failed to edit configuration")
            return 1
    
    elif args.config_action == "reset":
        try:
            # Remove existing config to trigger default creation
            if app.config_path and app.config_path != "config/config.json":
                import os
                os.remove(app.config_path)
            
            # Recreate with defaults
            app.config = app._load_config()
            app.save_config()
            print("✅ Configuration reset to defaults")
            return 0
        except Exception as e:
            print(f"❌ Failed to reset configuration: {e}")
            return 1
    
    else:
        print("❌ Config action required: show, edit, or reset")
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    if argv is None:
        argv = sys.argv[1:]
    
    parser = create_parser()
    args = parser.parse_args(argv)
    
    # Handle no command case
    if not args.command:
        parser.print_help()
        return 0
    
    try:
        # Initialize Apple Sider instance
        app = AppleSider(config_path=args.config)
        
        # Override project directory if specified
        if args.project_dir:
            from pathlib import Path
            app.project_dir = Path(args.project_dir)
        
        # Execute command
        if args.command == "install":
            return handle_install(app, args)
        
        elif args.command == "start":
            if args.build:
                print("🏗️ Building containers...")
                app.run_command("build")
            app.start()
            return 0
        
        elif args.command == "stop":
            app.stop()
            return 0
        
        elif args.command == "restart":
            app.restart()
            return 0
        
        elif args.command == "status":
            app.status()
            return 0
        
        elif args.command == "logs":
            app.logs()
            return 0
        
        elif args.command == "update":
            app.update()
            return 0
        
        elif args.command == "config":
            return handle_config(app, args)
        
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1
    
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        return 130
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
