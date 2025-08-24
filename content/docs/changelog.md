# Changelog

All notable changes to Apple-Sider will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-12-19

### Added
- **Next-Generation UI**: Complete interface overhaul with modern design principles
- **Glassmorphism Design**: Frosted glass effects throughout the interface
- **Animated Gradients**: Dynamic background animations that respond to theme changes
- **Dark/Light Mode Toggle**: Persistent theme switching with system preference detection
- **Keyboard Shortcuts**: 
  - `Ctrl/Cmd + T` for theme toggle
  - `Ctrl/Cmd + K` for console toggle
- **Enhanced File Upload**: Drag-and-drop interface with real-time progress indicators
- **Fixed Settings Panel**: Replaced collapsible dropdown with always-visible settings box
- **Service Worker**: Offline functionality and improved caching
- **Progressive Web App**: Manifest file for mobile installation
- **Accessibility Improvements**: ARIA labels, keyboard navigation, and screen reader support
- **Responsive Design**: Mobile-first approach with optimized layouts for all screen sizes

### Changed
- **Template Structure**: Moved HTML from `static/` to `templates/` directory for proper Flask routing
- **Static Asset Handling**: Updated to use Flask's `url_for()` for proper static file serving
- **Color Palette**: Enhanced color schemes for both light and dark themes
- **Typography**: Improved font hierarchy and readability
- **Layout Optimization**: Reduced top margins to fit interface on single screen
- **Performance**: GPU-accelerated animations and optimized rendering

### Fixed
- **Static File Serving**: Resolved 404 errors on CSS, JS, and asset requests
- **Template Rendering**: Fixed Flask routing to properly serve templates vs static files
- **Console Functionality**: Settings panel now properly expands and functions
- **File Upload Processing**: Library.xml uploads now properly trigger processing
- **Theme Persistence**: Dark mode preferences correctly saved across sessions
- **Container Caching**: Docker builds now properly update with new static files

### Technical Improvements
- **Flask Architecture**: Proper separation of templates and static files
- **CSS Architecture**: Modular stylesheets with CSS custom properties
- **JavaScript Modules**: Enhanced script organization with better error handling
- **Docker Optimization**: Improved container build process and caching
- **Code Quality**: Added comprehensive documentation and code comments

### Breaking Changes
- HTML template moved from `app/static/index.html` to `app/templates/index.html`
- Flask routing updated to use `render_template()` instead of `send_from_directory()`
- Static asset URLs now use Flask's `url_for()` function
- Settings interface changed from dropdown to fixed panel

## [1.0.0] - 2024-12-18

### Added
- Initial release of Apple-Sider
- Basic Flask web application structure
- Docker containerization with Docker Compose
- iTunes/Apple Music Library.xml file upload functionality
- Basic HTML interface for file processing
- Simple CSS styling
- JavaScript for basic interactivity

### Features
- File upload endpoint (`/upload`)
- Static file serving
- Basic error handling
- Container deployment on port 8082

## Planned Features

### [2.1.0] - Upcoming
- **Library Analytics**: Detailed insights and statistics from music libraries
- **Data Visualization**: Charts and graphs for library analysis
- **Export Functionality**: Multiple output formats for processed data
- **Batch Processing**: Handle multiple Library.xml files
- **API Extensions**: Additional endpoints for data retrieval

### [3.0.0] - Future
- **User Accounts**: Authentication and personal libraries
- **Cloud Storage**: Integration with cloud file storage services
- **Real-time Processing**: WebSocket-based live processing updates
- **Plugin System**: Extensible processing modules
- **Mobile Apps**: Native iOS and Android applications

## Migration Guide

### From 1.x to 2.x

If you have a 1.x installation, follow these steps to upgrade:

1. **Backup your data**: 
   ```bash
   docker-compose down
   cp -r uploads uploads-backup
   ```

2. **Pull latest changes**:
   ```bash
   git pull origin main
   ```

3. **Rebuild containers**:
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

4. **Verify upgrade**:
   - Check that the new UI loads at `http://localhost:8082`
   - Test file upload functionality
   - Verify theme toggle works
   - Confirm settings panel is visible

### Breaking Changes in 2.x

- **Template Location**: If you customized `app/static/index.html`, you'll need to move your changes to `app/templates/index.html`
- **Static URLs**: Any custom static file references need to use Flask's `url_for('static', filename='...')` pattern
- **Settings Interface**: The collapsible settings panel has been replaced with a fixed box layout

## Development Notes

### Version 2.0.0 Development
- **Development Branch**: All 2.0 work done on `development` branch
- **Testing**: Extensive testing with Docker container rebuilds
- **Documentation**: Comprehensive docs added with Fumadocs framework
- **Code Quality**: ESLint and Prettier configurations added
- **Performance**: Benchmarked and optimized for sub-second load times

### Contributors
- Core development and UI/UX design
- Docker containerization and deployment
- Documentation and testing

## Support

For issues related to specific versions:
- **Version 2.x**: Check the [UI Features](./ui-features.md) documentation
- **Version 1.x**: Upgrade to 2.x for continued support
- **General Issues**: See [Getting Started](./getting-started.md) troubleshooting section
