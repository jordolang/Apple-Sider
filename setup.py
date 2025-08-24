"""
Apple Sider - Setup Configuration
=================================

Setup script for pip installation of Apple Sider music downloader interface.
"""

from setuptools import setup, find_packages
import os

# Read long description from README
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Apple Sider - Web-based music downloader interface"

# Read requirements
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('-'):
                    # Skip system utilities and Docker requirements for pip install
                    if not any(skip in line.lower() for skip in ['docker', 'system', 'apt-get', 'brew']):
                        requirements.append(line)
    
    # Add essential Python dependencies for CLI
    essential_deps = [
        'requests>=2.25.0',
        'urllib3>=1.26.0',
    ]
    
    # Combine and deduplicate
    all_deps = list(set(requirements + essential_deps))
    
    # Filter out dependencies that are only needed in Docker
    pip_deps = []
    docker_only = [
        'flask', 'flask-socketio', 'python-socketio', 'python-engineio', 
        'werkzeug', 'youtube-dl', 'yt-dlp', 'eyed3', 'mutagen', 
        'musicbrainzngs', 'lyricsgenius', 'pylast', 'discogs-client', 'shazamio'
    ]
    
    for dep in all_deps:
        dep_name = dep.split('>=')[0].split('==')[0].split('<')[0].lower()
        if dep_name not in docker_only:
            pip_deps.append(dep)
    
    return pip_deps

setup(
    name="apple-sider",
    version="1.0.0",
    author="Jordan Lang",
    author_email="contact@jordolang.com",
    description="Web-based music downloader interface with CLI-Music-Downloader integration",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/jordolang/Apple-Sider",
    project_urls={
        "Bug Tracker": "https://github.com/jordolang/Apple-Sider/issues",
        "Documentation": "https://github.com/jordolang/Apple-Sider#readme",
        "Source Code": "https://github.com/jordolang/Apple-Sider",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows 11",
        "Environment :: Console",
        "Environment :: Web Environment",
    ],
    keywords=[
        "music", "downloader", "youtube", "mp3", "web-interface", 
        "docker", "cli", "audio", "metadata", "album-art"
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.812",
        ],
        "all": [
            # All optional dependencies for full functionality
            "flask>=3.0.0",
            "flask-socketio>=5.3.0",
            "python-socketio>=5.10.0",
            "python-engineio>=4.8.0",
            "werkzeug>=3.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "apple-sider=apple_sider.cli:main",
            "applesider=apple_sider.cli:main",  # Alternative name
        ],
    },
    include_package_data=True,
    package_data={
        "apple_sider": [
            "templates/*",
            "static/*",
            "config/*",
        ]
    },
    zip_safe=False,
    platforms=["any"],
    license="MIT",
    
    # Additional metadata
    maintainer="Jordan Lang",
    maintainer_email="contact@jordolang.com",
    download_url="https://github.com/jordolang/Apple-Sider/archive/refs/heads/main.zip",
    
    # Project maturity
    test_suite="tests",
)
