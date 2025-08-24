# API Reference

Apple-Sider provides a RESTful API built with Flask for handling library uploads and processing.

## Base URL

When running locally with Docker:
```
http://localhost:8082
```

## Endpoints

### GET `/`

**Description**: Serves the main application interface

**Response**: HTML page with the Apple-Sider user interface

**Example**:
```bash
curl http://localhost:8082/
```

### POST `/upload`

**Description**: Handles Library.xml file uploads

**Content-Type**: `multipart/form-data`

**Parameters**:
- `file` (file, required): The Library.xml file to upload

**Response Format**:
```json
{
  "status": "success|error",
  "message": "Description of result",
  "data": {
    // Processing results (if successful)
  }
}
```

**Success Response** (200 OK):
```json
{
  "status": "success",
  "message": "Library processed successfully",
  "data": {
    "tracks_processed": 1234,
    "artists_found": 156,
    "albums_found": 89,
    "processing_time": 2.34
  }
}
```

**Error Responses**:

**400 Bad Request** - No file uploaded:
```json
{
  "status": "error",
  "message": "No file uploaded"
}
```

**400 Bad Request** - Invalid file type:
```json
{
  "status": "error",
  "message": "Invalid file type. Please upload a .xml file"
}
```

**500 Internal Server Error** - Processing failed:
```json
{
  "status": "error",
  "message": "Failed to process library file"
}
```

**Example Usage**:
```bash
curl -X POST \
  -F "file=@/path/to/Library.xml" \
  http://localhost:8082/upload
```

### GET `/static/<path:filename>`

**Description**: Serves static assets (CSS, JavaScript, images)

**Parameters**:
- `filename` (string, required): Path to the static file

**Response**: Static file content with appropriate MIME type

**Example**:
```bash
curl http://localhost:8082/static/style.css
curl http://localhost:8082/static/script.js
curl http://localhost:8082/static/assets/icon.svg
```

## Request Examples

### JavaScript Fetch API

```javascript
// Upload Library.xml file
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('/upload', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  if (data.status === 'success') {
    console.log('Upload successful:', data.message);
    console.log('Processing results:', data.data);
  } else {
    console.error('Upload failed:', data.message);
  }
})
.catch(error => {
  console.error('Network error:', error);
});
```

### Python Requests

```python
import requests

# Upload Library.xml file
with open('Library.xml', 'rb') as file:
    files = {'file': file}
    response = requests.post('http://localhost:8082/upload', files=files)
    
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'success':
            print(f"Success: {data['message']}")
            print(f"Results: {data['data']}")
        else:
            print(f"Error: {data['message']}")
    else:
        print(f"HTTP Error: {response.status_code}")
```

### cURL Examples

```bash
# Upload Library.xml file
curl -X POST \
  -F "file=@Library.xml" \
  -H "Accept: application/json" \
  http://localhost:8082/upload

# Download static assets
curl -o style.css http://localhost:8082/static/style.css
curl -o script.js http://localhost:8082/static/script.js
```

## Error Handling

The API uses standard HTTP status codes:

- **200 OK**: Request succeeded
- **400 Bad Request**: Invalid request data
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server processing error

All error responses include a JSON object with:
```json
{
  "status": "error",
  "message": "Human-readable error description"
}
```

## File Upload Specifications

### Supported File Types
- XML files (`.xml` extension)
- Specifically designed for iTunes/Apple Music Library.xml files

### File Size Limits
- Maximum file size: 50MB (configurable)
- Recommended: Library.xml files are typically 1-10MB

### File Validation
- Extension validation (must be `.xml`)
- MIME type checking
- Basic XML structure validation
- iTunes/Apple Music library format verification

## Rate Limiting

Currently no rate limiting is implemented, but it's recommended for production deployments.

## Authentication

No authentication is required for the local development version. For production deployments, consider implementing:
- API key authentication
- JWT tokens
- OAuth integration

## CORS Policy

The application currently allows all origins for development. For production:
- Configure specific allowed origins
- Set appropriate CORS headers
- Implement preflight request handling
