# Apple Sider

🍎 **One Click To Scrape Your Entire Library as MP3's**

A simple self-hosted Docker application that lets you upload your Apple Music Library.xml file and automatically downloads your entire music library as high-quality MP3s using the [CLI-Music-Downloader](https://github.com/yourusername/CLI-Music-Downloader).

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

## 🚀 Quick Start

### Using the Start Script (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/Apple-Sider.git
cd Apple-Sider

# Start Apple Sider (builds and runs automatically)
./start.sh
```

That's it! Apple Sider will be available at http://localhost:8080

### Manual Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or with plain Docker
docker build -t apple-sider .
docker run -p 8080:8080 -v ~/Music/Apple-Sider:/app/downloads apple-sider
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
├── app/
│   ├── app.py              # Flask backend application
│   ├── parser.py           # Library.xml parser
│   ├── config.py           # Configuration management
│   ├── downloader.py       # Download queue manager
│   └── static/
│       ├── index.html      # Single-page web interface
│       ├── style.css       # Apple-inspired styling
│       └── app.js          # Frontend JavaScript
├── config/
│   └── config.json         # Runtime configuration
├── docker-compose.yml      # Docker Compose setup
├── Dockerfile              # Container definition
├── requirements.txt        # Python dependencies
├── config.example.json     # Configuration template
└── start.sh               # Easy start script
```

## 🔧 Management Commands

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

# Open shell in container for debugging
./start.sh shell

# Stop and remove everything
./start.sh down
```

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
docker-compose ps

# Check logs for errors
./start.sh logs
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
```bash
# Stop and remove all containers and data
./start.sh down
rm -rf config/
rm -rf ~/Music/Apple-Sider/

# Start fresh
./start.sh up
```

## 📊 Performance

- **Parsing speed**: ~1000 tracks per second
- **Download speed**: Limited by CLI-Music-Downloader and network
- **Memory usage**: ~50-100MB base + ~10MB per concurrent download
- **Storage**: Original Library.xml size + downloaded MP3s

## 🛠️ Development

### Local Development Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run development server
cd app
python app.py
```

### Building Custom Images
```bash
# Build with custom CLI-Music-Downloader
docker build --build-arg CLI_REPO_URL=https://github.com/your/fork.git -t apple-sider .
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [CLI-Music-Downloader](https://github.com/yourusername/CLI-Music-Downloader) for the core downloading functionality
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for reliable audio extraction
- [Flask](https://flask.palletsprojects.com/) and [Flask-SocketIO](https://flask-socketio.readthedocs.io/) for the web framework
- Apple for the Library.xml export format
- The open-source community for inspiration and tools

## ⭐ Star History

If this project helped you, please consider giving it a star! ⭐

---

**Made with ❤️ for music lovers who appreciate good tooling and want to own their music collection**
