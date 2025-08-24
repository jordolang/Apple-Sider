#!/bin/bash
# Apple Sider - Enhanced Cross-Platform Start Script
# Compatible with Linux, macOS, WSL, and more

set -e

# Script metadata
SCRIPT_VERSION="2.0.0"
PROJECT_NAME="Apple Sider"
GITHUB_REPO="https://github.com/jordolang/Apple-Sider"

# Platform detection
detect_platform() {
    case "$(uname -s)" in
        Darwin*)    PLATFORM="macOS";;
        Linux*)     PLATFORM="Linux";;
        CYGWIN*|MINGW*|MSYS*) PLATFORM="Windows";;
        *)          PLATFORM="Unknown";;
    esac
    
    # WSL detection
    if [[ "$PLATFORM" == "Linux" ]] && grep -qi microsoft /proc/version 2>/dev/null; then
        PLATFORM="WSL"
    fi
}

# Initialize platform
detect_platform

echo "🍎 $PROJECT_NAME - Starting up..."
echo "📱 Platform: $PLATFORM"
echo "🔧 Script Version: $SCRIPT_VERSION"

# Colors for output (with fallback for systems without color support)
if [[ -t 1 ]] && command -v tput &> /dev/null && tput colors &> /dev/null && [[ $(tput colors) -ge 8 ]]; then
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4)
    CYAN=$(tput setaf 6)
    NC=$(tput sgr0)
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    CYAN=''
    NC=''
fi

# Enhanced output functions
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

print_debug() {
    if [[ "${DEBUG}" == "1" ]]; then
        echo -e "${CYAN}[DEBUG]${NC} $1"
    fi
}

# Logging function
log_action() {
    local log_file="./logs/apple-sider.log"
    mkdir -p "$(dirname "$log_file")"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$log_file"
}

# System requirements check
check_system_requirements() {
    print_status "Checking system requirements..."
    
    local missing_deps=()
    local missing_optional=()
    
    # Essential dependencies
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    if ! command -v curl &> /dev/null && ! command -v wget &> /dev/null; then
        missing_deps+=("curl or wget")
    fi
    
    # Optional but recommended
    if ! command -v git &> /dev/null; then
        missing_optional+=("git")
    fi
    
    if ! command -v jq &> /dev/null; then
        missing_optional+=("jq")
    fi
    
    # Report missing dependencies
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        echo ""
        case "$PLATFORM" in
            "macOS")
                echo "Install with Homebrew:"
                echo "  brew install docker"
                [[ " ${missing_deps[@]} " =~ " curl or wget " ]] && echo "  brew install curl wget"
                ;;
            "Linux"|"WSL")
                echo "Install with your package manager:"
                echo "  # Ubuntu/Debian:"
                echo "  sudo apt update && sudo apt install -y docker.io curl wget"
                echo "  # CentOS/RHEL/Fedora:"
                echo "  sudo yum install -y docker curl wget"
                echo "  # or: sudo dnf install -y docker curl wget"
                ;;
            *)
                echo "Please install the missing dependencies for your platform"
                ;;
        esac
        echo ""
        echo "Docker installation guide: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if [[ ${#missing_optional[@]} -gt 0 ]]; then
        print_warning "Missing optional dependencies (recommended): ${missing_optional[*]}"
    fi
    
    print_debug "System requirements check passed"
}

# Docker service check and start
ensure_docker_running() {
    print_status "Checking Docker service..."
    
    if ! docker info &> /dev/null; then
        print_warning "Docker service is not running"
        
        case "$PLATFORM" in
            "macOS")
                print_status "Attempting to start Docker Desktop..."
                if command -v open &> /dev/null; then
                    open -a Docker || true
                    print_status "Waiting for Docker Desktop to start (this may take a minute)..."
                    local count=0
                    while ! docker info &> /dev/null && [[ $count -lt 60 ]]; do
                        sleep 2
                        ((count++))
                        printf "."
                    done
                    echo ""
                fi
                ;;
            "Linux"|"WSL")
                print_status "Attempting to start Docker service..."
                if command -v systemctl &> /dev/null; then
                    sudo systemctl start docker || {
                        print_error "Failed to start Docker service"
                        print_error "Please start Docker manually: sudo systemctl start docker"
                        exit 1
                    }
                elif command -v service &> /dev/null; then
                    sudo service docker start || {
                        print_error "Failed to start Docker service"
                        print_error "Please start Docker manually: sudo service docker start"
                        exit 1
                    }
                fi
                ;;
        esac
        
        # Final check
        if ! docker info &> /dev/null; then
            print_error "Docker is not running and could not be started automatically"
            print_error "Please start Docker manually and try again"
            exit 1
        fi
    fi
    
    print_debug "Docker service is running"
}

# Docker Compose detection and setup
setup_docker_compose() {
    print_status "Setting up Docker Compose..."
    
    # Try different Docker Compose commands
    if docker compose version &> /dev/null; then
        DOCKER_COMPOSE="docker compose"
        print_debug "Using Docker Compose plugin"
    elif command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
        print_debug "Using standalone docker-compose"
    else
        print_error "Docker Compose is not available"
        echo ""
        echo "Install options:"
        case "$PLATFORM" in
            "macOS")
                echo "  Docker Desktop includes Compose: https://docs.docker.com/desktop/mac/"
                echo "  Or with Homebrew: brew install docker-compose"
                ;;
            "Linux"|"WSL")
                echo "  # Install Docker Compose plugin (recommended):"
                echo "  sudo apt update && sudo apt install -y docker-compose-plugin"
                echo "  # Or standalone version:"
                echo "  sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
                echo "  sudo chmod +x /usr/local/bin/docker-compose"
                ;;
        esac
        echo ""
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    export DOCKER_COMPOSE
    print_debug "Docker Compose command: $DOCKER_COMPOSE"
}

# Directory setup with proper permissions
setup_directories() {
    print_status "Creating directories..."
    
    # Platform-specific music directory
    case "$PLATFORM" in
        "macOS")
            MUSIC_DIR="$HOME/Music/Apple-Sider"
            ;;
        "WSL")
            # Try to use Windows Music folder if available
            if [[ -d "/mnt/c/Users/$USER/Music" ]]; then
                MUSIC_DIR="/mnt/c/Users/$USER/Music/Apple-Sider"
            else
                MUSIC_DIR="$HOME/Music/Apple-Sider"
            fi
            ;;
        *)
            MUSIC_DIR="$HOME/Music/Apple-Sider"
            ;;
    esac
    
    # Create directories with error handling
    local dirs_to_create=(
        "$MUSIC_DIR"
        "./config"
        "./logs"
        "./data"
        "./tmp"
    )
    
    for dir in "${dirs_to_create[@]}"; do
        if ! mkdir -p "$dir" 2>/dev/null; then
            print_warning "Could not create directory: $dir"
            if [[ "$dir" == "$MUSIC_DIR" ]]; then
                print_warning "Falling back to local downloads directory"
                MUSIC_DIR="./downloads"
                mkdir -p "$MUSIC_DIR"
            fi
        fi
    done
    
    export MUSIC_DIR
    print_debug "Music directory: $MUSIC_DIR"
    
    # Set up configuration
    if [[ ! -f "./config/config.json" ]]; then
        if [[ -f "./config.example.json" ]]; then
            cp "./config.example.json" "./config/config.json"
            print_success "Created default configuration"
        else
            print_warning "No example config found, creating basic config"
            cat > "./config/config.json" << 'JSON_EOF'
{
  "app": {
    "name": "Apple Sider",
    "version": "1.0.0",
    "port": 8080
  },
  "downloads": {
    "quality": "high",
    "format": "mp3",
    "organize_by_artist": true
  },
  "cli_music_downloader": {
    "enabled": true,
    "path": "/app/cli-music-downloader"
  }
}
JSON_EOF
            print_success "Created basic configuration"
        fi
    fi
}

# Network connectivity check
check_network() {
    print_status "Checking network connectivity..."
    
    local test_urls=(
        "google.com"
        "github.com"
        "docker.com"
    )
    
    local connectivity=false
    for url in "${test_urls[@]}"; do
        if ping -c 1 -W 3000 "$url" &> /dev/null 2>&1 || \
           ping -c 1 -w 3 "$url" &> /dev/null 2>&1; then
            connectivity=true
            break
        fi
    done
    
    if [[ "$connectivity" != "true" ]]; then
        print_warning "Network connectivity issues detected"
        print_warning "Some features may not work properly"
    else
        print_debug "Network connectivity confirmed"
    fi
}

# Health check function
health_check() {
    local max_attempts=30
    local attempt=0
    
    print_status "Performing health check..."
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -s -f "http://localhost:8080/health" &> /dev/null || \
           curl -s -f "http://localhost:8080" &> /dev/null; then
            return 0
        fi
        
        sleep 2
        ((attempt++))
        
        if [[ $((attempt % 5)) -eq 0 ]]; then
            printf "\n"
            print_status "Still checking health... ($attempt/$max_attempts)"
        else
            printf "."
        fi
    done
    
    printf "\n"
    return 1
}

# Update function
update_application() {
    print_status "Updating Apple Sider..."
    
    # Stop current containers
    $DOCKER_COMPOSE down 2>/dev/null || true
    
    # Pull latest changes if git is available
    if command -v git &> /dev/null && [[ -d ".git" ]]; then
        print_status "Pulling latest changes..."
        git pull origin main || print_warning "Could not pull latest changes"
    fi
    
    # Pull latest Docker images
    print_status "Pulling latest Docker images..."
    $DOCKER_COMPOSE pull
    
    # Rebuild with no cache
    print_status "Rebuilding application..."
    $DOCKER_COMPOSE build --no-cache
    
    # Start updated application
    print_status "Starting updated application..."
    $DOCKER_COMPOSE up -d
    
    if health_check; then
        print_success "Apple Sider updated and restarted successfully!"
        show_success_info
    else
        print_error "Update completed but service health check failed"
        print_error "Check logs with: $DOCKER_COMPOSE logs"
        return 1
    fi
}

# Show success information
show_success_info() {
    echo ""
    echo "🎉 Apple Sider is running successfully!"
    echo ""
    echo "🌐 Web Interface: http://localhost:8080"
    echo "📁 Downloads: $MUSIC_DIR"
    echo "⚙️  Configuration: ./config/config.json"
    echo "📋 Logs: ./logs/"
    echo ""
    echo "📖 Useful commands:"
    echo "  ./start.sh logs      - View application logs"
    echo "  ./start.sh stop      - Stop the service"
    echo "  ./start.sh restart   - Restart the service"
    echo "  ./start.sh down      - Stop and remove containers"
    echo "  ./start.sh update    - Update to latest version"
    echo "  ./start.sh status    - Show service status"
    echo "  ./start.sh shell     - Open shell in container"
    echo ""
}

# Status check function
show_status() {
    print_status "Checking Apple Sider status..."
    
    if $DOCKER_COMPOSE ps | grep -q "Up"; then
        print_success "Apple Sider is running"
        
        # Show container details
        echo ""
        echo "Container Status:"
        $DOCKER_COMPOSE ps
        
        # Show resource usage if available
        if command -v docker &> /dev/null; then
            echo ""
            echo "Resource Usage:"
            docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
                $(docker ps --filter "name=apple-sider" --format "{{.Names}}") 2>/dev/null || \
                print_warning "Could not retrieve resource usage"
        fi
        
        # Test connectivity
        if health_check; then
            print_success "Service is healthy and responding"
        else
            print_warning "Service is running but not responding to health checks"
        fi
    else
        print_warning "Apple Sider is not running"
        echo ""
        echo "Start with: ./start.sh up"
    fi
}

# Main execution logic
main() {
    local action="${1:-up}"
    local start_time=$(date +%s)
    
    # Enable debug mode if requested
    if [[ "$2" == "--debug" ]] || [[ "$DEBUG" == "1" ]]; then
        export DEBUG=1
        set -x
    fi
    
    # Log the action
    log_action "Starting action: $action (Platform: $PLATFORM)"
    
    case "$action" in
        "up"|"start")
            # Full startup sequence
            check_system_requirements
            ensure_docker_running
            setup_docker_compose
            setup_directories
            check_network
            
            print_status "Starting Apple Sider..."
            $DOCKER_COMPOSE up -d
            
            if health_check; then
                print_success "Apple Sider started successfully!"
                show_success_info
                log_action "Successfully started Apple Sider"
            else
                print_error "Apple Sider failed to start properly"
                print_error "Check logs with: $DOCKER_COMPOSE logs"
                log_action "Failed to start Apple Sider"
                exit 1
            fi
            ;;
            
        "build")
            setup_docker_compose
            print_status "Building Apple Sider Docker image..."
            $DOCKER_COMPOSE build --no-cache
            print_success "Build completed successfully!"
            ;;
            
        "stop")
            setup_docker_compose
            print_status "Stopping Apple Sider..."
            $DOCKER_COMPOSE stop
            print_success "Apple Sider stopped"
            log_action "Stopped Apple Sider"
            ;;
            
        "restart")
            setup_docker_compose
            print_status "Restarting Apple Sider..."
            $DOCKER_COMPOSE restart
            
            if health_check; then
                print_success "Apple Sider restarted successfully!"
                show_success_info
                log_action "Successfully restarted Apple Sider"
            else
                print_error "Restart completed but health check failed"
                log_action "Restart failed health check"
            fi
            ;;
            
        "down")
            setup_docker_compose
            print_status "Stopping and removing Apple Sider containers..."
            $DOCKER_COMPOSE down
            print_success "Apple Sider containers removed"
            log_action "Removed Apple Sider containers"
            ;;
            
        "logs")
            setup_docker_compose
            print_status "Showing Apple Sider logs..."
            $DOCKER_COMPOSE logs -f --tail=100
            ;;
            
        "update")
            setup_docker_compose
            update_application
            ;;
            
        "status")
            setup_docker_compose
            show_status
            ;;
            
        "shell"|"bash")
            setup_docker_compose
            print_status "Opening shell in Apple Sider container..."
            $DOCKER_COMPOSE exec apple-sider /bin/bash || \
            $DOCKER_COMPOSE run --rm apple-sider /bin/bash
            ;;
            
        "clean")
            setup_docker_compose
            print_warning "This will remove all containers, volumes, and images"
            read -p "Are you sure? (y/N): " -r
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                print_status "Cleaning up Apple Sider..."
                $DOCKER_COMPOSE down -v --rmi all
                docker system prune -f
                print_success "Cleanup completed"
                log_action "Performed full cleanup"
            else
                print_status "Cleanup cancelled"
            fi
            ;;
            
        "install")
            print_status "Installing Apple Sider system-wide..."
            
            # Copy script to system location
            local install_dir="/usr/local/bin"
            if [[ ! -w "$install_dir" ]]; then
                install_dir="$HOME/.local/bin"
                mkdir -p "$install_dir"
            fi
            
            cp "$0" "$install_dir/apple-sider"
            chmod +x "$install_dir/apple-sider"
            
            print_success "Apple Sider installed to $install_dir/apple-sider"
            print_status "You can now run 'apple-sider' from anywhere"
            ;;
            
        "version"|"--version")
            echo "$PROJECT_NAME v$SCRIPT_VERSION"
            echo "Platform: $PLATFORM"
            echo "Repository: $GITHUB_REPO"
            ;;
            
        "help"|"--help"|*)
            cat << 'HELP_EOF'
🍎 Apple Sider - Enhanced Cross-Platform Management Script

USAGE:
    ./start.sh [COMMAND] [OPTIONS]

COMMANDS:
    up, start    Start Apple Sider (default)
    build        Build the Docker image
    stop         Stop the service
    restart      Restart the service
    down         Stop and remove containers
    logs         Show and follow logs
    update       Update to latest version
    status       Show service status and health
    shell, bash  Open shell in container
    clean        Remove all containers, volumes, and images
    install      Install script system-wide
    version      Show version information
    help         Show this help message

OPTIONS:
    --debug      Enable debug output

EXAMPLES:
    ./start.sh                    # Start Apple Sider
    ./start.sh logs               # View logs
    ./start.sh status             # Check if running
    ./start.sh update             # Update to latest version
    ./start.sh up --debug         # Start with debug output

ENVIRONMENT VARIABLES:
    DEBUG=1                       # Enable debug mode
    MUSIC_DIR                     # Override music directory
    
PLATFORM SUPPORT:
    ✅ macOS (Intel & Apple Silicon)
    ✅ Linux (Ubuntu, Debian, CentOS, RHEL, Fedora)
    ✅ Windows Subsystem for Linux (WSL)
    ✅ Docker Desktop environments

For more information, visit: https://github.com/jordolang/Apple-Sider
HELP_EOF
            ;;
    esac
    
    # Log execution time
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_action "Action '$action' completed in ${duration}s"
}

# Trap for cleanup
trap 'print_error "Script interrupted"; exit 130' INT TERM

# Run main function with all arguments
main "$@"
