# Getting Started

This guide will help you set up and run Apple-Sider on your local machine.

## Prerequisites

- Docker and Docker Compose installed on your system
- Your iTunes/Apple Music Library.xml file

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Apple-Sider.git
cd Apple-Sider
```

### 2. Build and Start with Docker

```bash
# Build the Docker containers
docker-compose build --no-cache

# Start the application in detached mode
docker-compose up -d
```

### 3. Access the Application

Open your browser and navigate to:
```
http://localhost:8082
```

## Getting Your Library.xml File

### iTunes (Windows/older macOS)

1. Open iTunes
2. Go to **File** → **Library** → **Export Library**
3. Save the file as `Library.xml`

### Apple Music (macOS Catalina and later)

1. Open **Music** app
2. Go to **File** → **Library** → **Export Library**
3. Save the file as `Library.xml`

### Alternative Method (macOS)

The Library.xml file is typically located at:
```
~/Music/iTunes/Library.xml
```
or
```
~/Music/Music/Library.xml
```

## Using Apple-Sider

1. **Upload Library.xml**: Drag and drop your Library.xml file onto the upload area, or click to select it
2. **Configure Settings**: Adjust processing options in the settings panel
3. **Process Library**: Click "Process Library" to analyze your music data
4. **View Results**: Explore the insights and visualizations generated from your library

## Troubleshooting

### Port Already in Use
If port 8082 is already in use, modify the port mapping in `docker-compose.yml`:
```yaml
ports:
  - "8083:8080"  # Change 8082 to 8083 or any available port
```

### Container Won't Start
Check if Docker is running and try rebuilding:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Files Not Loading
Ensure static files are properly served by rebuilding the container after any code changes:
```bash
docker-compose build --no-cache
docker-compose up -d
```
