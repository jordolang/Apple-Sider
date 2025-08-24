<div align="center">
  <img src="logo.png" alt="Apple Sider Logo" width="200" height="200">
</div>


<div align="center">
  <img src="logo.png" alt="Apple Sider Logo" width="200" height="200">
</div>

<div align="center">
  <img src="logo.png" alt="Apple Sider Logo" width="200" height="200">
</div>

# Apple Sider

🍎 **One Click To Scrape Your Entire Library as MP3's**

A simple self-hosted Docker application that lets you upload your Apple Music Library.xml file and automatically downloads your entire music library as high-quality MP3s using the [CLI-Music-Downloader](https://github.com/jordolang/CLI-Music-Downloader).

## ✨ Features

- 📱 **Single-page web interface** - Clean, Apple-inspired design with drag-and-drop
- ⚡ **Real-time progress** - Live console output and download progress tracking
- 🔄 **Concurrent downloads** - Up to 3 simultaneous downloads with queue management
- 🎵 **High-quality MP3s** - Powered by CLI-Music-Downloader with metadata enhancement
- 🎨 **Album artwork** - Automatic album art from iTunes API and metadata tagging
- ⚙️ **Highly configurable** - Customize download location, folder structure, and CLI settings
- 🐳 **Docker ready** - Single container deployment with volume persistence
- 📊 **Smart parsing** - Handles Apple Music, purchased, and matched content
- 🔄 **Error handling** - Automatic retries, failed download tracking, and recovery
- 📡 **WebSocket streaming** - Real-time console output and status updates

## 🚀 Installation

### Method 1: pip install (Recommended for CLI)

```bash
# Install Apple Sider
pip install apple-sider

# Install and set up
apple-sider install

# Start the service
apple-sider start
```

### Method 2: Git Clone + Start Script

```bash
# Clone the repository
git clone https://github.com/jordolang/Apple-Sider.git
cd Apple-Sider

# Start Apple Sider (builds and runs automatically)
./start.sh
```

### Method 3: Manual Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or with plain Docker
docker build -t apple-sider .
docker run -p 8080:8080 -v ~/Music/Apple-Sider:/app/downloads apple-sider
```

That's it! Apple Sider will be available at http://localhost:8080

## 📋 CLI Usage

After installing with pip, you can use the `apple-sider` command:

```bash
# Install Apple Sider
apple-sider install

# Start services
apple-sider start

# Check status
apple-sider status

# View logs
apple-sider logs

# Stop services
apple-sider stop

# Restart services
apple-sider restart

# Update to latest version
apple-sider update

# Show configuration
apple-sider config show

# Edit configuration
apple-sider config edit

# Get help
apple-sider --help
```

## 📋 How to Use

1. **Export your Apple Music library:**
   - Open Apple Music (or iTunes)
   - Go to File → Library → Export Library...
   - Save as `Library.xml`

2. **Upload and download:**
   - Open http://localhost:8080 in your browser
   - Drag and drop your `Library.xml` file
   - Review the library analysis (total tracks, estimated time)
   - Click "Start Download" and watch the magic happen!

3. **Monitor progress:**
   - Real-time console output shows download progress
   - Progress bar and statistics update automatically
   - Failed downloads can be retried with one click

## ⚙️ Configuration

Apple Sider can be configured through the web interface or by editing `config/config.json`:

### Download Settings
- **Location**: `~/Music/Apple-Sider` (customizable)
- **Structure**: Flat (`Artist-Song.mp3`) or Nested (`Artist/Song.mp3`)
- **Concurrent downloads**: 1-10 simultaneous downloads
- **Overwrite existing**: Skip or overwrite duplicate files

### CLI-Music-Downloader Integration
- **Metadata sources**: All, MusicBrainz only, or skip metadata
- **Audio quality**: Best available quality
- **Retry settings**: Configurable retry count and delays

### Advanced Settings
- **File naming**: Custom filename formats
- **Character sanitization**: Safe filename handling
- **Timeout settings**: Per-download timeout limits
- **Logging**: Configurable log levels and buffer sizes

## 📁 Project Structure

```
Apple-Sider/
├── apple_sider/           # Python package
│   ├── __init__.py       # Package initialization
│   ├── core.py           # Core application logic
│   └── cli.py            # Command-line interface
├── app/
│   ├── app.py            # Flask backend application
│   ├── parser.py         # Library.xml parser
│   ├── config.py         # Configuration management
│   ├── downloader.py     # Download queue manager
│   └── static/
│       ├── index.html    # Single-page web interface
│       ├── style.css     # Apple-inspired styling
│       └── app.js        # Frontend JavaScript
├── config/
│   └── config.json       # Runtime configuration
├── docker-compose.yml    # Docker Compose setup
├── Dockerfile            # Container definition
├── requirements.txt      # Python dependencies
├── setup.py             # pip package setup
├── pyproject.toml       # Modern Python packaging
├── config.example.json  # Configuration template
└── start.sh             # Enhanced start script
```

## 🔧 Management Commands

### Using the CLI (after pip install)

```bash
# Start Apple Sider
apple-sider start

# Check status
apple-sider status

# View logs in real-time
apple-sider logs

# Stop the service
apple-sider stop

# Restart after config changes
apple-sider restart

# Update to latest version
apple-sider update

# Configuration management
apple-sider config show
apple-sider config edit
apple-sider config reset
```

### Using the Start Script

```bash
# Start Apple Sider
./start.sh up

# View logs in real-time
./start.sh logs

# Stop the service
./start.sh stop

# Restart after config changes
./start.sh restart

# Update to latest version
./start.sh update

# Show status and health
./start.sh status

# Open shell in container for debugging
./start.sh shell

# Stop and remove everything
./start.sh down

# Clean up all data
./start.sh clean
```

## 🌍 Cross-Platform Support

Apple Sider works on:

- ✅ **macOS** (Intel & Apple Silicon)
- ✅ **Linux** (Ubuntu, Debian, CentOS, RHEL, Fedora)
- ✅ **Windows Subsystem for Linux** (WSL)
- ✅ **Docker Desktop** environments

The enhanced start script automatically detects your platform and provides appropriate installation instructions.

## 📂 Output Structure

### Flat Structure (Default)
```
~/Music/Apple-Sider/
├── The Beatles-Hey Jude.mp3
├── Queen-Bohemian Rhapsody.mp3
├── Pink Floyd-Comfortably Numb.mp3
└── Taylor Swift-Shake It Off.mp3
```

### Nested Structure
```
~/Music/Apple-Sider/
├── The Beatles/
│   ├── Hey Jude.mp3
│   └── Yellow Submarine.mp3
├── Queen/
│   ├── Bohemian Rhapsody.mp3
│   └── We Will Rock You.mp3
└── Pink Floyd/
    ├── Comfortably Numb.mp3
    └── Wish You Were Here.mp3
```

## 🎯 What Gets Downloaded

- **Apple Music tracks**: Searches and downloads from YouTube
- **Purchased content**: Re-downloads with enhanced quality
- **Matched tracks**: Downloads the matched versions
- **Metadata enhancement**: Album art, lyrics, tags, and organization
- **Smart filtering**: Skips podcasts, audiobooks, and non-music content

## 🔍 Troubleshooting

### Common Issues

**Web interface not loading:**
```bash
# Check if container is running
apple-sider status

# Check logs for errors
apple-sider logs
```

**Downloads failing:**
- Ensure CLI-Music-Downloader dependencies are installed
- Check network connectivity
- Verify download location is writable
- Use the retry feature for failed downloads

**Large libraries timing out:**
- Increase timeout settings in configuration
- Process library in smaller batches
- Use fewer concurrent downloads for stability

### Reset Everything

#### Using pip installation:
```bash
# Stop services
apple-sider stop

# Reset configuration
apple-sider config reset

# Start fresh
apple-sider start
```

#### Using git clone:
```bash
# Stop and remove all containers and data
./start.sh clean
rm -rf config/
rm -rf ~/Music/Apple-Sider/

# Start fresh
./start.sh up
```

## 📊 Performance

- **Small libraries** (< 1000 tracks): ~30 minutes
- **Medium libraries** (1000-5000 tracks): ~2-4 hours
- **Large libraries** (> 5000 tracks): ~6+ hours

Performance varies based on:
- Network speed
- CPU/RAM resources
- Concurrent download settings
- YouTube availability

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -am 'Add feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [CLI-Music-Downloader](https://github.com/jordolang/CLI-Music-Downloader) - The powerful backend that makes this possible
- [InstantMusic](https://github.com/yask123/InstantMusic) - Original inspiration for music downloading
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Excellent YouTube downloading capabilities
- [MusicBrainz](https://musicbrainz.org/) - Comprehensive music metadata database

## ⭐ Support

If you find Apple Sider useful, please:
- ⭐ Star this repository
- 🐛 Report issues on GitHub
- 💡 Suggest new features
- 🔄 Share with others who might find it helpful

---

**Happy downloading! 🎵**
