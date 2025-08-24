#!/usr/bin/env python3
"""
Apple Music Library.xml Parser for Apple Sider
Extracts track metadata and generates download commands for CLI-Music-Downloader
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
import re
import logging

logger = logging.getLogger(__name__)

class Track:
    """Represents a single track from the iTunes/Apple Music library"""
    
    def __init__(self, track_data: Dict):
        self.track_id = track_data.get('Track ID')
        self.name = track_data.get('Name', '')
        self.artist = track_data.get('Artist', '')
        self.album_artist = track_data.get('Album Artist', '')
        self.album = track_data.get('Album', '')
        self.genre = track_data.get('Genre', '')
        self.year = track_data.get('Year')
        self.track_number = track_data.get('Track Number')
        self.total_time = track_data.get('Total Time', 0)  # milliseconds
        self.kind = track_data.get('Kind', '')
        self.track_type = track_data.get('Track Type', 'File')
        
        # Check if this is Apple Music content
        self.is_apple_music = track_data.get('Apple Music', False)
        self.is_purchased = 'Purchased' in self.kind
        self.is_matched = 'Matched' in self.kind
        
    def is_valid_music(self) -> bool:
        """Check if this track is valid music content for downloading"""
        if not self.name or not self.artist:
            return False
            
        # Skip podcasts, audiobooks, and other non-music content
        non_music_genres = ['podcast', 'audiobook', 'spoken', 'comedy', 'educational']
        if any(genre.lower() in self.genre.lower() for genre in non_music_genres):
            return False
            
        # Skip non-audio files
        non_audio_kinds = ['video', 'movie', 'tv show', 'music video']
        if any(kind.lower() in self.kind.lower() for kind in non_audio_kinds):
            return False
            
        return True
    
    def get_download_query(self) -> str:
        """Generate search query for CLI-Music-Downloader"""
        # Use the most specific artist information available
        primary_artist = self.artist or self.album_artist
        if not primary_artist:
            return ""
            
        # Clean up artist names (remove featuring artists for main search)
        clean_artist = re.sub(r'\s+(feat\.|featuring|ft\.|with)\s+.*$', '', primary_artist, flags=re.IGNORECASE)
        
        # Clean up track names (remove parenthetical content like "Remastered", "Live", etc.)
        clean_track = re.sub(r'\s*\([^)]*\)$', '', self.name)
        clean_track = re.sub(r'\s*\[[^\]]*\]$', '', clean_track)
        
        return f"{clean_artist} {clean_track}".strip()
    
    def get_duration_seconds(self) -> int:
        """Convert total time from milliseconds to seconds"""
        return int(self.total_time / 1000) if self.total_time else 0
    
    def __str__(self):
        duration = self.get_duration_seconds()
        return f"{self.artist} - {self.name} ({duration}s)"

class LibraryParser:
    """Parser for iTunes/Apple Music Library.xml files"""
    
    def __init__(self):
        self.tracks: List[Track] = []
        self.total_tracks = 0
        self.valid_tracks = 0
        self.estimated_duration_hours = 0.0
        
    def parse_library(self, xml_file_path: str) -> Dict:
        """
        Parse the Library.xml file and extract track information
        
        Args:
            xml_file_path: Path to the Library.xml file
            
        Returns:
            Dict with parsing results and statistics
        """
        try:
            logger.info(f"Parsing library file: {xml_file_path}")
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            
            # Find the Tracks dictionary
            tracks_dict = self._find_tracks_dict(root)
            if not tracks_dict:
                raise ValueError("Could not find Tracks section in Library.xml")
                
            # Parse each track
            self.tracks = []
            for track_key in tracks_dict:
                track_data = self._parse_track_dict(tracks_dict[track_key])
                if track_data:
                    track = Track(track_data)
                    self.tracks.append(track)
                    
            self.total_tracks = len(self.tracks)
            
            # Filter for valid music tracks
            valid_tracks = [track for track in self.tracks if track.is_valid_music()]
            self.valid_tracks = len(valid_tracks)
            
            # Calculate estimated duration
            total_duration_seconds = sum(track.get_duration_seconds() for track in valid_tracks)
            self.estimated_duration_hours = total_duration_seconds / 3600
            
            logger.info(f"Parsed {self.total_tracks} total tracks, {self.valid_tracks} valid music tracks")
            logger.info(f"Estimated total duration: {self.estimated_duration_hours:.1f} hours")
            
            return {
                'success': True,
                'total_tracks': self.total_tracks,
                'valid_tracks': self.valid_tracks,
                'estimated_hours': round(self.estimated_duration_hours, 1),
                'tracks': valid_tracks
            }
            
        except Exception as e:
            logger.error(f"Error parsing library: {e}")
            return {
                'success': False,
                'error': str(e),
                'total_tracks': 0,
                'valid_tracks': 0,
                'estimated_hours': 0,
                'tracks': []
            }
    
    def _find_tracks_dict(self, root) -> Optional[Dict]:
        """Find the Tracks dictionary in the plist structure"""
        # Navigate through the plist structure
        dict_elem = root.find('dict')
        if dict_elem is None:
            return None
            
        # Parse the root dictionary
        root_dict = self._parse_dict_to_python(dict_elem)
        
        # Return the Tracks subdictionary
        return root_dict.get('Tracks', None)
    
    def _parse_dict_to_python(self, dict_elem: ET.Element) -> Dict:
        """Convert XML dict element to Python dictionary"""
        result = {}
        children = list(dict_elem)
        
        for i in range(0, len(children), 2):
            if i + 1 < len(children):
                key_elem = children[i]
                value_elem = children[i + 1]
                
                if key_elem.tag == 'key':
                    key = key_elem.text
                    value = self._parse_value(value_elem)
                    result[key] = value
                    
        return result
    
    def _parse_value(self, elem: ET.Element):
        """Parse XML value element to appropriate Python type"""
        if elem.tag == 'string':
            return elem.text or ''
        elif elem.tag == 'integer':
            return int(elem.text) if elem.text else 0
        elif elem.tag == 'real':
            return float(elem.text) if elem.text else 0.0
        elif elem.tag == 'true':
            return True
        elif elem.tag == 'false':
            return False
        elif elem.tag == 'date':
            return elem.text or ''
        elif elem.tag == 'dict':
            return self._parse_dict_to_python(elem)
        elif elem.tag == 'array':
            return [self._parse_value(child) for child in elem]
        else:
            return elem.text or ''
    
    def _parse_track_dict(self, track_dict: Dict) -> Optional[Dict]:
        """Parse a single track dictionary and clean up the data"""
        if not track_dict or not isinstance(track_dict, dict):
            return None
            
        # Clean up common issues in track data
        cleaned = {}
        for key, value in track_dict.items():
            if isinstance(value, str):
                # Decode HTML entities
                value = value.replace('&#38;', '&').replace('&amp;', '&')
                value = value.replace('&#39;', "'").replace('&apos;', "'")
                value = value.replace('&#34;', '"').replace('&quot;', '"')
            cleaned[key] = value
            
        return cleaned

    def generate_download_manifest(self) -> List[Dict]:
        """Generate a manifest of tracks to download with metadata"""
        valid_tracks = [track for track in self.tracks if track.is_valid_music()]
        
        manifest = []
        for i, track in enumerate(valid_tracks, 1):
            download_query = track.get_download_query()
            if download_query:
                manifest.append({
                    'id': i,
                    'track_id': track.track_id,
                    'query': download_query,
                    'artist': track.artist,
                    'name': track.name,
                    'album': track.album,
                    'duration': track.get_duration_seconds(),
                    'metadata': {
                        'genre': track.genre,
                        'year': track.year,
                        'track_number': track.track_number
                    }
                })
        
        return manifest

# Example usage and testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        library_path = sys.argv[1]
        parser = LibraryParser()
        result = parser.parse_library(library_path)
        
        if result['success']:
            print(f"✅ Successfully parsed {result['valid_tracks']} tracks")
            print(f"📊 Estimated duration: {result['estimated_hours']} hours")
            
            # Show first 5 tracks as sample
            for track in result['tracks'][:5]:
                print(f"🎵 {track.get_download_query()}")
        else:
            print(f"❌ Error: {result['error']}")
    else:
        print("Usage: python parser.py <path_to_Library.xml>")
