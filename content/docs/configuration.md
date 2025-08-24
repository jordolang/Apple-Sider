# Configuration

Apple-Sider can be configured through environment variables, Docker settings, and application-level configuration.

## Environment Variables

### Flask Configuration

```bash
# Application environment
FLASK_ENV=development  # or 'production'
FLASK_DEBUG=1          # Enable debug mode (development only)

# Host and port configuration
FLASK_HOST=0.0.0.0     # Host to bind to
FLASK_PORT=8080        # Port to run Flask app on

# Security
SECRET_KEY=your_secret_key_here  # For session security
```

### File Upload Configuration

```bash
# Maximum file size for uploads (in bytes)
MAX_CONTENT_LENGTH=52428800  # 50MB default

# Upload directory path
UPLOAD_FOLDER=./uploads

# Allowed file extensions
ALLOWED_EXTENSIONS=xml,XML
```

### Processing Configuration

```bash
# Processing timeout (in seconds)
PROCESSING_TIMEOUT=300

# Maximum concurrent processing jobs
MAX_CONCURRENT_JOBS=3

# Enable verbose logging
VERBOSE_LOGGING=true
```

## Docker Configuration

### docker-compose.yml

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8082:8080"  # Host:Container port mapping
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=1
    volumes:
      - ./uploads:/app/uploads  # Persistent upload storage
    restart: unless-stopped
```

### Dockerfile Environment

The application uses the following default configuration in the Docker container:

```dockerfile
ENV FLASK_ENV=production
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=8080
ENV PYTHONUNBUFFERED=1
```

## Application Settings

### Frontend Configuration

Settings are managed through the web interface and stored in browser localStorage:

```javascript
// Default application settings
const defaultSettings = {
  theme: 'auto',           // 'light', 'dark', or 'auto'
  animations: true,        // Enable/disable animations
  sounds: false,          // Enable/disable sound effects
  autoSave: true,         // Auto-save processing results
  maxFileSize: 50,        // Maximum file size in MB
  processingMode: 'standard', // 'fast', 'standard', or 'detailed'
  showAdvanced: false     // Show advanced processing options
};
```

### Backend Configuration

Flask application configuration in `app/app.py`:

```python
import os

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    
    # File uploads
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 52428800))
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', './uploads')
    
    # Processing
    PROCESSING_TIMEOUT = int(os.environ.get('PROCESSING_TIMEOUT', 300))
    MAX_CONCURRENT_JOBS = int(os.environ.get('MAX_CONCURRENT_JOBS', 3))
    
    # Logging
    VERBOSE_LOGGING = os.environ.get('VERBOSE_LOGGING', 'false').lower() == 'true'
```

## Development vs Production

### Development Settings

Create a `.env` file for development:

```bash
# .env
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-secret-key
VERBOSE_LOGGING=true
MAX_CONTENT_LENGTH=104857600  # 100MB for testing
```

### Production Settings

For production deployment:

```bash
# Production environment variables
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=your-secure-random-secret-key
VERBOSE_LOGGING=false
MAX_CONTENT_LENGTH=52428800   # 50MB
PROCESSING_TIMEOUT=600        # 10 minutes
```

## Security Configuration

### HTTPS Configuration

For production deployments, configure HTTPS:

```python
# Force HTTPS in production
if os.environ.get('FLASK_ENV') == 'production':
    from flask_talisman import Talisman
    Talisman(app, force_https=True)
```

### CORS Configuration

Configure Cross-Origin Resource Sharing:

```python
from flask_cors import CORS

# Development - allow all origins
if app.config['DEBUG']:
    CORS(app, resources={r"/*": {"origins": "*"}})
else:
    # Production - specific origins only
    CORS(app, resources={r"/api/*": {"origins": ["https://yourdomain.com"]}})
```

### File Upload Security

```python
import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'xml'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def secure_upload(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Additional security checks
        return filename
    return None
```

## Logging Configuration

### Python Logging

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    # Production logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler('logs/apple-sider.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

### Docker Logging

Configure container logging:

```yaml
version: '3.8'
services:
  app:
    build: .
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Performance Configuration

### Gunicorn Configuration

For production deployment with Gunicorn:

```python
# gunicorn.conf.py
bind = "0.0.0.0:8080"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 300
keepalive = 2
```

### Nginx Configuration

Reverse proxy configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    client_max_body_size 50M;
    
    location / {
        proxy_pass http://127.0.0.1:8082;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /path/to/apple-sider/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Database Configuration

If extending with database functionality:

```bash
# Database configuration
DATABASE_URL=sqlite:///apple-sider.db
# or
DATABASE_URL=postgresql://user:password@localhost/apple_sider

# Connection pool settings
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
```

## Monitoring Configuration

### Health Check Endpoint

```python
@app.route('/health')
def health_check():
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': app.config.get('VERSION', '1.0.0')
    }
```

### Metrics Collection

```bash
# Enable metrics collection
ENABLE_METRICS=true
METRICS_PORT=9090

# Prometheus configuration
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc_dir
```
