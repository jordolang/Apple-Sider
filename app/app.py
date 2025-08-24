from flask import Flask, render_template, request, jsonify, send_file
import os
import logging
import xml.etree.ElementTree as ET
import json
from datetime import datetime

app = Flask(__name__, template_folder='templates', static_folder='static')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create uploads directory if it doesn't exist
UPLOADS_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and process Library.xml"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not file.filename.lower().endswith('.xml'):
            return jsonify({'error': 'Please upload a valid XML file'}), 400
            
        # Read file content
        file_content = file.read()
        
        # Save uploaded file
        filename = f"library_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        file_path = os.path.join(UPLOADS_DIR, filename)
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
            
        logger.info(f"File saved: {file_path}")
        
        # Parse the Library.xml file
        library_data = parse_library_xml(file_content)
        
        if library_data['status'] == 'error':
            return jsonify({
                'success': False,
                'error': library_data['message']
            }), 400
            
        return jsonify({
            'success': True,
            'message': 'Library.xml processed successfully!',
            'filename': file.filename,
            'data': {
                'tracks': library_data['tracks'],
                'artists': library_data['artists'],
                'albums': library_data['albums'],
                'playlists': library_data['playlists'],
                'total_size': library_data['total_size'],
                'total_time': library_data['total_time'],
                'genres': library_data['genres'],
                'processing_time': library_data['processing_time']
            }
        })
            
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Processing failed: {str(e)}'
        }), 500

def parse_library_xml(xml_content):
    """Parse iTunes/Apple Music Library.xml file"""
    start_time = datetime.now()
    
    try:
        # Parse XML content
        root = ET.fromstring(xml_content)
        
        # Find the main dict element
        main_dict = None
        for elem in root:
            if elem.tag == 'dict':
                main_dict = elem
                break
                
        if main_dict is None:
            return {'status': 'error', 'message': 'Invalid Library.xml format - no main dict found'}
            
        # Parse library data
        library_info = {'status': 'success'}
        tracks = {}
        playlists = []
        
        # Parse the main dictionary
        current_key = None
        tracks_dict = None
        playlists_array = None
        
        for elem in main_dict:
            if elem.tag == 'key':
                current_key = elem.text
            elif current_key == 'Tracks' and elem.tag == 'dict':
                tracks_dict = elem
            elif current_key == 'Playlists' and elem.tag == 'array':
                playlists_array = elem
                
        # Parse tracks
        if tracks_dict is not None:
            track_key = None
            for elem in tracks_dict:
                if elem.tag == 'key':
                    track_key = elem.text
                elif elem.tag == 'dict' and track_key:
                    track_info = parse_track_dict(elem)
                    tracks[track_key] = track_info
                    
        # Parse playlists
        if playlists_array is not None:
            for playlist_dict in playlists_array:
                if playlist_dict.tag == 'dict':
                    playlist_info = parse_playlist_dict(playlist_dict)
                    playlists.append(playlist_info)
                    
        # Calculate statistics
        stats = calculate_library_stats(tracks, playlists)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'status': 'success',
            'tracks': len(tracks),
            'artists': len(stats['artists']),
            'albums': len(stats['albums']),
            'playlists': len(playlists),
            'genres': len(stats['genres']),
            'total_size': stats['total_size'],
            'total_time': stats['total_time'],
            'processing_time': round(processing_time, 2)
        }
        
    except ET.ParseError as e:
        return {'status': 'error', 'message': f'XML parsing error: {str(e)}'}
    except Exception as e:
        return {'status': 'error', 'message': f'Processing error: {str(e)}'}

def parse_track_dict(track_dict):
    """Parse individual track dictionary"""
    track = {}
    current_key = None
    
    for elem in track_dict:
        if elem.tag == 'key':
            current_key = elem.text
        elif current_key and elem.tag in ['string', 'integer', 'date', 'true', 'false']:
            if elem.tag == 'true':
                track[current_key] = True
            elif elem.tag == 'false':
                track[current_key] = False
            elif elem.tag == 'integer':
                track[current_key] = int(elem.text) if elem.text else 0
            else:
                track[current_key] = elem.text if elem.text else ''
                
    return track

def parse_playlist_dict(playlist_dict):
    """Parse individual playlist dictionary"""
    playlist = {}
    current_key = None
    
    for elem in playlist_dict:
        if elem.tag == 'key':
            current_key = elem.text
        elif current_key and elem.tag in ['string', 'integer', 'true', 'false', 'array']:
            if elem.tag == 'true':
                playlist[current_key] = True
            elif elem.tag == 'false':
                playlist[current_key] = False
            elif elem.tag == 'integer':
                playlist[current_key] = int(elem.text) if elem.text else 0
            elif elem.tag == 'array':
                # Handle playlist items array
                playlist[current_key] = len(elem)
            else:
                playlist[current_key] = elem.text if elem.text else ''
                
    return playlist

def calculate_library_stats(tracks, playlists):
    """Calculate library statistics"""
    artists = set()
    albums = set()
    genres = set()
    total_size = 0
    total_time = 0
    
    for track in tracks.values():
        if 'Artist' in track:
            artists.add(track['Artist'])
        if 'Album' in track:
            albums.add(track['Album'])
        if 'Genre' in track:
            genres.add(track['Genre'])
        if 'Size' in track:
            total_size += track['Size']
        if 'Total Time' in track:
            total_time += track['Total Time']
            
    return {
        'artists': artists,
        'albums': albums,
        'genres': genres,
        'total_size': total_size,
        'total_time': total_time
    }

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=True)
