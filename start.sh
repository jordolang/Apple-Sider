#!/bin/bash
# Apple Sider - Start Script

set -e

echo "🍎 Apple Sider - Starting up..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available. Please install Docker Compose."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Determine Docker Compose command
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Create necessary directories
print_status "Creating directories..."
mkdir -p ~/Music/Apple-Sider
mkdir -p ./config

# Copy example config if config doesn't exist
if [ ! -f ./config/config.json ]; then
    if [ -f ./config.example.json ]; then
        cp ./config.example.json ./config/config.json
        print_success "Created default configuration"
    fi
fi

# Check CLI-Music-Downloader path
CLI_PATH="$HOME/Repos/CLI-Music-Downloader"
if [ ! -d "$CLI_PATH" ]; then
    print_warning "CLI-Music-Downloader not found at $CLI_PATH"
    print_warning "The Docker image will clone it automatically, but you may want to set it up locally first"
fi

# Parse command line arguments
ACTION=${1:-up}

case $ACTION in
    "build")
        print_status "Building Apple Sider Docker image..."
        $DOCKER_COMPOSE build --no-cache
        print_success "Build complete!"
        ;;
    "up")
        print_status "Starting Apple Sider..."
        $DOCKER_COMPOSE up -d
        
        # Wait a moment for the service to start
        sleep 3
        
        # Check if the container is running
        if $DOCKER_COMPOSE ps | grep -q "Up"; then
            print_success "Apple Sider is running!"
            echo ""
            echo "🌐 Web Interface: http://localhost:8080"
            echo "📁 Downloads: ~/Music/Apple-Sider/"
            echo "⚙️  Configuration: ./config/config.json"
            echo ""
            echo "📋 Useful commands:"
            echo "  ./start.sh logs    - View logs"
            echo "  ./start.sh stop    - Stop the service"
            echo "  ./start.sh restart - Restart the service"
            echo "  ./start.sh down    - Stop and remove containers"
        else
            print_error "Failed to start Apple Sider"
            echo "Check logs with: $DOCKER_COMPOSE logs"
            exit 1
        fi
        ;;
    "stop")
        print_status "Stopping Apple Sider..."
        $DOCKER_COMPOSE stop
        print_success "Apple Sider stopped"
        ;;
    "restart")
        print_status "Restarting Apple Sider..."
        $DOCKER_COMPOSE restart
        print_success "Apple Sider restarted"
        echo "🌐 Web Interface: http://localhost:8080"
        ;;
    "down")
        print_status "Stopping and removing Apple Sider containers..."
        $DOCKER_COMPOSE down
        print_success "Apple Sider containers removed"
        ;;
    "logs")
        print_status "Showing Apple Sider logs..."
        $DOCKER_COMPOSE logs -f
        ;;
    "update")
        print_status "Updating Apple Sider..."
        $DOCKER_COMPOSE down
        $DOCKER_COMPOSE pull
        $DOCKER_COMPOSE build --no-cache
        $DOCKER_COMPOSE up -d
        print_success "Apple Sider updated and restarted"
        ;;
    "shell")
        print_status "Opening shell in Apple Sider container..."
        $DOCKER_COMPOSE exec apple-sider /bin/bash
        ;;
    *)
        echo "🍎 Apple Sider - Docker Management Script"
        echo ""
        echo "Usage: ./start.sh [command]"
        echo ""
        echo "Commands:"
        echo "  up       - Start Apple Sider (default)"
        echo "  build    - Build the Docker image"
        echo "  stop     - Stop the service"
        echo "  restart  - Restart the service"
        echo "  down     - Stop and remove containers"
        echo "  logs     - Show logs"
        echo "  update   - Update and restart"
        echo "  shell    - Open shell in container"
        echo ""
        echo "Examples:"
        echo "  ./start.sh           # Start the service"
        echo "  ./start.sh logs      # View logs"
        echo "  ./start.sh stop      # Stop the service"
        ;;
esac
