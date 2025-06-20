# Pyper - A Modern Navidrome Music Player

A feature-rich, Linux-first music player application designed specifically for Navidrome servers. Built with PyQt6 and featuring a clean, modern interface with robust search capabilities, contextual information display, and intuitive workflow.

## ✨ Features

- **🐧 Linux-First Design**: Optimized for Linux desktop environments
- **🔍 Powerful Search**: Search across artists, albums, and songs with dedicated search tab
- **🎯 Enhanced Tabbed Interface**: Browse, Search, Queue, Most Played, and Recently Played tabs
- **🎨 Contextual Information Panel**: Dynamic bottom panel showing artist info, album details, and artwork based on your selection
- **🎵 Multi-Category Navigation**: Browse by Artists, Albums, Playlists, Genres, and Years (decades)
- **📊 Play Count Integration**: Display play counts from Navidrome database with remote SSH access support
- **🎨 Album Art Support**: Automatic album artwork display with proper scaling and contextual thumbnails
- **📋 Queue Management**: Full playback queue with individual track management and Clear Queue functionality
- **🎵 Scrobbling**: Last.fm compatible scrobbling through Navidrome
- **🌙 Modern Theming**: Dark theme with qt-material styling and purple accents
- **🖱️ Context Menus**: Right-click options throughout the interface
- **⚡ Smart Playback**: Double-click anywhere to add and play immediately
- **🚀 Auto-Expand**: Artists automatically expanded on startup for immediate browsing
- **📝 Comprehensive Logging**: File and console logging for debugging and monitoring
- **🔗 Remote Database Access**: SSH-based access to remote Navidrome databases for play count data

## 📋 Requirements

- Python 3.8+
- PyQt6
- Navidrome server (configured and running)
- Linux desktop environment (tested on Manjaro/Arch)
- SSH access to Navidrome server (optional, for play count features)

## 🚀 Installation

### For Manjaro/Arch Linux:

1. **Install system dependencies:**
   ```bash
   sudo pacman -S python-pyqt6 python-requests python-pipx
   ```

2. **Install Python packages:**
   ```bash
   pip install --break-system-packages py-sonic qt-material
   ```

3. **Clone/download Pyper and set up:**
   ```bash
   git clone <repository-url>
   cd pyper-app
   ```

4. **Configure your server settings:**
   ```bash
   cp config/config.example.json config/config.json
   # Edit config/config.json with your Navidrome server details
   ```

5. **Run Pyper:**
   ```bash
   ./run-pyper.sh
   # or
   python pyper.py
   ```

### Alternative Installation (any Linux):

1. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure and run as above**

## ⚙️ Configuration

Create your configuration file:

```bash
cp config/config.example.json config/config.json
```

Edit `config/config.json`:

```json
{
    "navidrome": {
        "server_url": "http://your-server:4533",
        "username": "your_username", 
        "password": "your_password",
        "database_path": "/home/user/.navidrome/navidrome.db",
        "ssh_host": "your-server-ip",
        "ssh_user": "username",
        "ssh_key_path": "~/.ssh/id_ed25519"
    },
    "ui": {
        "theme": "dark_teal.xml",
        "window_width": 1400,
        "window_height": 900
    }
}
```

**Important**: 
- Include `http://` or `https://` in your server URL
- The configuration file is ignored by git for security
- Never commit your actual credentials
- SSH configuration is optional but enables advanced play count features
- Set up SSH key authentication for seamless database access

**Common Database Locations:**
- `/var/lib/navidrome/navidrome.db` (systemd service)
- `/opt/navidrome/navidrome.db` (manual installation)  
- `/home/navidrome/navidrome.db` (user installation)

## 🎵 Usage

### Navigation Structure
- **Browse Tab**: Navigate Artists → Albums → Songs hierarchy (auto-expands artists on startup)
  - **Artists**: Browse by artist with album thumbnails in contextual panel
  - **Albums**: Browse all albums with play count integration
  - **Playlists**: Access your Navidrome playlists
  - **Genres**: Browse music by genre with album previews
  - **Years**: Browse by decades (1960s, 1970s, etc.) with album counts
- **Search Tab**: Find content across your entire library
- **Queue Tab**: Manage your playback queue
- **Most Played Tab**: Discover your most frequently played albums with play counts
- **Recently Played Tab**: Quick access to recently played albums

### Contextual Information Panel
The bottom panel dynamically displays relevant information based on your selection:
- **Artist Selection**: Shows artist name, album count, and scrollable album artwork thumbnails
- **Album Selection**: Displays large album artwork, title, artist, year, and track count
- **Genre Selection**: Shows genre information with representative album thumbnails
- **Decade Selection**: Displays decade info with albums from that era
- **Automatic Updates**: Panel content changes as you navigate through the interface

### Search Functionality
1. Type in the search bar at the top
2. Press Enter or click "Search"
3. Results appear in Artists | Albums | Songs columns
4. Double-click or right-click any result to play or queue

### Playback Controls
- **Double-click** any item to add to queue and start playing
- **Right-click** for context menu options:
  - "Add to Queue" - adds without playing
  - "Play Now" - adds to queue and starts playing immediately
- **Player Bar**: Compact controls with artwork, progress, and time

### Queue Management
- **Queue Tab**: Full queue view with clear button
- **Right-click** queue items for "Remove from Queue" or "Play Now"
- **Clear Queue** button in Queue tab to empty entire queue

### Album Artwork
- **Click artwork** in player to show detailed track info dialog
- Artwork automatically loads and scales properly
- Large artwork display in now playing dialog
- Contextual thumbnails in bottom panel

### Logging
- Application events logged to `pyper.log` in the application directory
- Console output for real-time monitoring
- Error tracking and debugging information
- Startup and connection status logging

## 🏗️ Project Structure

```
pyper-app/
├── src/
│   └── pyper/
│       ├── __init__.py        # Package initialization  
│       └── main.py            # Main application code
├── config/
│   ├── config.example.json    # Example configuration
│   └── config.json           # Your configuration (ignored by git)
├── docs/
│   ├── DATABASE_SETUP.md     # Database configuration guide
│   └── FEATURES.md           # Detailed feature documentation
├── assets/
│   ├── pyper.desktop         # Desktop entry file
│   ├── pyper-icon.png        # Application icon
│   └── create_icon.py        # Icon generation script
├── pyper.py                  # Entry point script
├── pyper.log                 # Application log file (generated)
├── requirements.txt          # Python dependencies
├── run-pyper.sh             # Launch script with config check
├── install-shortcut.sh      # Desktop shortcut installer
├── setup.py                 # Package setup
├── .gitignore              # Git ignore patterns
└── README.md               # This file
```

## 🛠️ Troubleshooting

### Configuration Issues
```bash
# Check if config exists
ls -la config/config.json

# Validate JSON syntax
python -m json.tool config/config.json

# Check log file for errors
tail -f pyper.log
```

### Connection Issues
- Verify Navidrome server is running and accessible
- Test by accessing Navidrome web interface first  
- Check URL format includes `http://` or `https://`
- Verify username and password are correct
- Check `pyper.log` for detailed connection error messages

### SSH/Database Issues
- Ensure SSH key authentication is set up correctly
- Test SSH connection manually: `ssh -i ~/.ssh/id_ed25519 user@server`
- Verify database path on remote server
- Check SSH configuration in config.json
- Application will fall back to API-based play data if SSH fails

### Audio Issues
- Ensure system has proper audio codecs installed
- Check that other audio applications work
- Verify Qt multimedia framework is installed
- Check log file for FFmpeg/audio-related errors

### Dependencies
```bash
# System packages (Manjaro/Arch)
sudo pacman -S python-pyqt6 python-requests

# Python packages
pip install py-sonic qt-material
```

## 🔧 Development

### Technology Stack
- **PyQt6**: Modern Qt bindings for Python
- **py-sonic**: Subsonic/Navidrome API client  
- **qt-material**: Material Design theme for Qt
- **SQLite3**: Database access for play count data
- **SSH/SCP**: Remote database access capabilities

### Key Components
- **ContextualInfoPanel**: Dynamic bottom panel showing selection-based information
- **NavidromeDBHelper**: Database access with SSH support for play count data
- **CustomSubsonicClient**: Enhanced API client with genre and year support
- **LibraryRefreshThread**: Threaded library loading for responsive UI
- **ImageDownloadThread**: Asynchronous artwork loading

### Logging System
- Comprehensive logging throughout the application
- File logging to `pyper.log` with rotation
- Console output for development
- Error tracking and debugging information

## 📚 Documentation

- **[Database Setup Guide](docs/DATABASE_SETUP.md)**: Detailed database configuration
- **[Features Documentation](docs/FEATURES.md)**: Complete feature overview
- **[Installation Guide](install-shortcut.sh)**: Desktop integration setup

## 🎯 Recent Updates

### v2.0 - Enhanced Navigation & Contextual Interface
- Added **Genres** and **Years** navigation categories
- Implemented **dynamic contextual information panel**
- Added **comprehensive logging system**
- Enhanced **remote database access** with SSH support
- Improved **album artwork handling** with thumbnails
- Added **decade-based year browsing**
- Enhanced **error handling and debugging**

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source. Please check the repository for license details.

## 🙏 Acknowledgments

- **Navidrome**: The excellent music server that powers this player
- **PyQt6**: For the robust GUI framework
- **qt-material**: For the beautiful material design theme